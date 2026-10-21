"""Strict data contracts, exact arithmetic, calendar alignment, snapshot comparison."""

import csv
import hashlib
import io
import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


class ResearchError(ValueError):
    """An input cannot support the requested research claim."""


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.utcoffset() is None:
            raise ValueError("timezone required")
        return result.astimezone(timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise ResearchError("Use an ISO timestamp with a timezone") from exc


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def method_path():
    return Path(__file__).parent / "methodologies" / "v1.json"


def load_method(path=None):
    method = json.loads(Path(path or method_path()).read_bytes())
    validate_method(method)
    return method


def validate_method(method):
    if not method.get("version") or method.get("output_unit") != "USD billions":
        raise ResearchError("Methodology requires a version and USD billions output")
    if set(method.get("series", {})) != {"WALCL", "WDTGAL", "WLRRAL", "WRBWFRBL"}:
        raise ResearchError("This engine supports exactly the four documented H.4.1 series")
    if set(method.get("recipes", {})) != {"liquidity", "reserves", "gap"}:
        raise ResearchError("Unsupported recipe set")
    for meta in method["series"].values():
        validate_contract(meta)
    for recipe in method["recipes"].values():
        if not recipe.get("coefficients") or not set(recipe["coefficients"]).issubset(method["series"]):
            raise ResearchError("Invalid recipe input")
        for weight in recipe["coefficients"].values():
            d = Decimal(weight)
            if not d.is_finite() or abs(d) > 10:
                raise ResearchError("Invalid recipe coefficient")
    for series in method["series"]:
        liquidity = Decimal(method["recipes"]["liquidity"]["coefficients"].get(series, "0"))
        reserve = Decimal(method["recipes"]["reserves"]["coefficients"].get(series, "0"))
        gap = Decimal(method["recipes"]["gap"]["coefficients"].get(series, "0"))
        if liquidity - reserve != gap:
            raise ResearchError("Gap must equal liquidity minus reserves")
    if not isinstance(method.get("stale_after_days"), int) or method["stale_after_days"] < 7:
        raise ResearchError("Invalid stale threshold")


def validate_contract(meta):
    expected = {"unit": "USD millions", "currency": "USD", "frequency": "weekly",
                "basis": "Wednesday level", "seasonal_adjustment": "NSA"}
    for key, value in expected.items():
        if meta.get(key) != value:
            raise ResearchError("Input contract mismatch: %s must be %s" % (key, value))


def parse_csv(raw, series, meta, captured_at):
    """No guessed zeros, silent duplicate resolution, future observations or mixed bases."""
    validate_contract(meta)
    cutoff = timestamp(captured_at).date()
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if reader.fieldnames not in (["observation_date", series], ["DATE", series]):
            raise ResearchError("Unexpected CSV columns for " + series)
        rows = {}
        date_column = reader.fieldnames[0]
        for row in reader:
            if None in row or row.get(series) is None:
                raise ResearchError("Malformed CSV row")
            observed = date.fromisoformat(row[date_column])
            if observed.weekday() != 2:
                raise ResearchError("Expected Wednesday level: " + observed.isoformat())
            if observed > cutoff:
                raise ResearchError("Future observation relative to capture")
            if observed in rows:
                raise ResearchError("Duplicate observation: " + observed.isoformat())
            token = row[series].strip()
            value = None if token in ("", ".") else Decimal(token)
            if value is not None and (not value.is_finite() or value < 0 or value > Decimal("1e12")):
                raise ResearchError("Nonfinite, negative, or implausibly large balance-sheet level")
            rows[observed] = value
    except (UnicodeError, InvalidOperation, ValueError) as exc:
        if isinstance(exc, ResearchError):
            raise
        raise ResearchError("Invalid CSV value for " + series) from exc
    if not rows or not any(v is not None for v in rows.values()):
        raise ResearchError("No usable observations for " + series)
    return rows


def evaluate(values, recipe, method):
    coefficients = method["recipes"][recipe]["coefficients"]
    if any(values.get(s) is None for s in coefficients):
        return None
    return sum((values[s] * Decimal(w) for s, w in coefficients.items()), Decimal(0)) / 1000


def aligned_rows(data, method):
    """Calendar spine retains absent weeks; missing inputs produce null outputs."""
    first = min(min(v) for v in data.values())
    last = max(max(v) for v in data.values())
    rows = []
    day = first
    while day <= last:
        values = {s: data[s].get(day) for s in method["series"]}
        rows.append({"date": day.isoformat(), "inputs": values,
                     **{r: evaluate(values, r, method) for r in method["recipes"]}})
        day += timedelta(days=7)
    return rows


def change_window(rows, weeks):
    """Exact calendar endpoint comparison, never positional 'N nonmissing rows ago'."""
    complete = [r for r in rows if all(r[k] is not None for k in ("liquidity", "reserves", "gap"))]
    if not complete:
        return None
    end = complete[-1]
    begin_date = (date.fromisoformat(end["date"]) - timedelta(weeks=weeks)).isoformat()
    begin = next((r for r in rows if r["date"] == begin_date), None)
    if begin is None or any(begin[k] is None for k in ("liquidity", "reserves", "gap")):
        return None
    return {"start": begin["date"], "end": end["date"], "weeks": weeks,
            "liquidity": end["liquidity"] - begin["liquidity"],
            "reserves": end["reserves"] - begin["reserves"], "gap": end["gap"] - begin["gap"],
            "input_deltas": {s: (end["inputs"][s] - begin["inputs"][s]) / 1000 for s in end["inputs"]},
            "missing_interior_weeks": sum(any(r[k] is None for k in ("liquidity", "reserves", "gap")) for r in rows if begin_date < r["date"] < end["date"])}


def percent_change(before, after):
    return None if before == 0 else (after - before) / abs(before) * 100


def classify_changes(old, new):
    events = []
    for series in sorted(set(old) | set(new)):
        a, b = old.get(series, {}), new.get(series, {})
        previous_last = max(a) if a else date.min
        for day in sorted(set(a) | set(b)):
            if day in a and day in b and a[day] == b[day]:
                continue
            before, after = a.get(day), b.get(day)
            if day not in b:
                kind = "removed_observation"
            elif day not in a:
                kind = "new_observation" if day > previous_last else "historical_backfill"
            elif before is None:
                kind = "filled_missing"
            elif after is None:
                kind = "became_missing"
            else:
                kind = "revised_prior_value"
            events.append({"series": series, "date": day.isoformat(), "kind": kind,
                           "before": before, "after": after})
    return events


def revision_bridge(old_data, new_data, old_method, new_method):
    """Exact ordered bridge: prior-date data, new endpoint, then methodology.

    Never assign an economic revision reason. Unavailable endpoints suppress the bridge.
    """
    old_rows, new_rows = aligned_rows(old_data, old_method), aligned_rows(new_data, old_method)
    full = lambda rows: [r for r in rows if all(r[k] is not None for k in ("liquidity", "reserves", "gap"))]
    a, b = full(old_rows), full(new_rows)
    if not a or not b:
        return None
    old_end, new_end = a[-1], b[-1]
    same_day = next((r for r in new_rows if r["date"] == old_end["date"]), None)
    if same_day is None or any(same_day[k] is None for k in ("liquidity", "reserves", "gap")) or new_end["date"] < old_end["date"]:
        return None
    result = {"old_date": old_end["date"], "new_date": new_end["date"], "recipes": {}}
    for key in ("liquidity", "reserves", "gap"):
        updated = evaluate(new_end["inputs"], key, new_method)
        result["recipes"][key] = {"before": old_end[key],
            "prior_data_effect": same_day[key] - old_end[key],
            "new_observation_effect": new_end[key] - same_day[key],
            "methodology_effect": updated - new_end[key], "after": updated,
            "total": updated - old_end[key]}
    return result


def serializable(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(v) for v in value]
    return value
