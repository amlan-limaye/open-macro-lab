# Next official release and later visual review

Status checked **2026-10-21**. This is a dated plan, not a polling job or a claim of new data.

## Next real data release

The [Board's October 2026 calendar](https://www.federalreserve.gov/newsevents/2026-october.htm) lists H.4.1 for **Thursday, October 22, 2026, at 4:30 p.m. Eastern time**. That is **20:30 UTC** on this date. The [H.4.1 release schedule](https://www.federalreserve.gov/releases/h41/) states the usual Thursday 4:30 p.m. cadence with holiday exceptions. The [WALCL page](https://fred.stlouisfed.org/series/WALCL) also lists October 22 as the next release; the other three selected series showed the same date. The Board's [dated H.4.1 notices](https://www.federalreserve.gov/releases/h41/20251030/) explicitly identify the time convention as Eastern time.

The next Wednesday observation is expected to be October 21 based on the series basis. This is an expectation until the actual release is read, not a fabricated observation or publication timestamp. FRED can update after the Board's scheduled release; do not assume simultaneous availability. A future capture must record its actual retrieval/completion times.

After the release is actually available, an authorized manual check can capture the four series, verify the date sets and source metadata, compare with the retained first capture, and inspect new observations versus changed prior values. An unchanged or delayed result should be reported as such. No polling, automation, or future fetch has been created.

## Supported visual-review route

The local HTML report is self-contained. A normal browser can render it without build dependencies. For automated visual review, the supported Playwright CLI workflow can use an **isolated browser session**, navigate to an explicitly approved local preview, take a DOM snapshot, exercise the range controls, and capture screenshots. Do not reuse an existing personal browser profile or attach to someone else's running browser. Do not install browser tooling or download executables without separate authorization.

The preparation environment has `npx`, the installed Playwright CLI wrapper, and cached Chromium binaries. The wrapper normally uses `npx --yes --package @playwright/cli`; that can fetch software if the CLI package is absent, so its presence alone does not establish an installation-free ready runtime. Before a later automated run, verify the CLI is already available and that the specific browser and preview route are authorized. No wrapper, browser, server, mouse, or keyboard action was run during this preparation.

The current no-UI restriction and any prior denial of a preview route must be explicitly cleared before retrying that route. If automated preview remains unavailable, a user can supply desktop/mobile screenshots from their own manual view for image inspection. A screenshot review does not substitute for testing clicks or downloads.

Review the synthetic report and the separate retained official report at desktop and narrow widths. Check that synthetic labels and snapshot ages remain visible; amounts match the CSV/JSON; chart scales, legends, gaps, dates, and units are readable; tables scroll without clipping the page; 13/52/all-history controls select the right data; evidence links and downloads resolve; and keyboard focus is visible. Record screenshots under a local review output directory and keep the review result distinct from the already-passed content checks.

**Current outcome:** visual verification is pending. No screenshot or real-browser behavior claim is made.
