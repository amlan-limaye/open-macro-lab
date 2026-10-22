# Research workflow improvements in 0.2.0

This pass addresses three concrete researcher problems. It adds no indicator and changes no economic definition.

| Before | After | Evidence |
| --- | --- | --- |
| Researchers copied snapshot paths by hand and tracked which capture to compare. | `update` inherits the prior method/window, selects the latest already-known official capture, validates inputs, and commits a verified issue under its capture ID. | Full CLI acquisition simulation plus first-run, later-run, future-capture, retry, and failure tests. |
| `verify` checked snapshots but not a report's conclusions or exported files. | `verify-report` recomputes the full payload and checks CSV/HTML against attached evidence and the recorded implementation. | Tests alter raw data, a calculated result, CSV, HTML, and the engine hash; each fails. |
| The documented path ran from the checkout, without an installation regression check. | A wheel installs and runs outside the checkout with its method and fixtures, and records its version in reports. | Clean Python 3.9.6 and 3.13.7 environments; zero runtime dependencies and offline installation/demo. |

The unchanged-observation explanation was also corrected: two captures with equal parsed values now say so explicitly. They do not claim observed differences or prove that no intermediate revision occurred.

## Practical use

From a source checkout:

```sh
python3 -m open_macro_lab demo
python3 -m open_macro_lab verify-report build/demo
python3 -m open_macro_lab update --store data/live --output build/issues
```

The first two commands are offline and synthetic. The last contacts the four documented official FRED sources and requires trusted HTTPS. Its JSON response contains `report`, `snapshot`, `previous`, `observation_date`, `data_status`, `warnings`, `comparison`, `change_counts`, and interpretation. `previous` is null on the first capture; that report remains a baseline.

Run the same update command after a later release. Inspect the explanation and ledger. An unchanged observation is a useful result, not a reason to manufacture a daily trading signal. No scheduler is created by the CLI.

To reproduce an issue, transfer its whole directory and retain the package version recorded in `report.json`. Run `verify-report` with that implementation. When changing the implementation, explicitly rebuild from the attached snapshots and effective method into a new directory; do not relabel an older report as newly observed data.

## Preserved scope

- Package version changes to 0.2.0; method remains 1.0.0. Original 0.1.0 release and raw captures are retained.
- Formulas, Wednesday alignment, units, absence of historical publication timestamps, and economic limitations are unchanged.
- The synthetic revision example is still fabricated. Its raw evidence and history CSV are byte-identical.
- The existing 146-week real baseline reproduces with unchanged calculations. No new real release was fetched, and the scheduled future comparison was not duplicated.
- No credentials, accounts, market execution, private messages, telemetry, or publication command were added.
- LICENSE contains standard MIT grant/disclaimer text. The previous explanatory scope paragraph is preserved unchanged in DATA_LICENSE.md, which is also included in the wheel.

See [verification scope](../VERIFICATION.md) for observed results and limits. This is functionality and reproducibility evidence; it makes no claim about external users, adoption, stars, or investment performance.
