"""Rebuild explicitly synthetic CSV fixtures, with intentionally simple arithmetic."""
from datetime import date, timedelta
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "open_macro_lab" / "fixtures"
for version, count in (("baseline", 16), ("later", 17)):
    folder = root / version
    folder.mkdir(parents=True, exist_ok=True)
    for series in ("WALCL", "WDTGAL", "WLRRAL", "WRBWFRBL"):
        lines = ["observation_date," + series]
        for i in range(count):
            value = {"WALCL": 7000000 + 10000*i, "WDTGAL": 800000 + 5000*i,
                     "WLRRAL": 500000 - 10000*i, "WRBWFRBL": 3000000 + 8000*i}[series]
            if version == "later" and series == "WALCL" and i == 15:
                value += 2000  # Deliberate synthetic revision: +2 USD bn at old endpoint.
            if version == "later" and series == "WDTGAL" and i == 10:
                value += 1000  # A revision away from the current comparison endpoints.
            lines.append((date(2025, 1, 1) + timedelta(weeks=i)).isoformat() + "," + str(value))
        (folder / (series + ".csv")).write_text("\n".join(lines) + "\n")
