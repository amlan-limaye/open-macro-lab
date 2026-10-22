# Next official release and later visual review

Status checked **2026-10-21**. This is a dated plan, not a polling job or a claim of new data.

## Next real data release

The [Board's October 2026 calendar](https://www.federalreserve.gov/newsevents/2026-october.htm) lists H.4.1 for **Thursday, October 22, 2026, at 4:30 p.m. Eastern time**. That is **20:30 UTC** on this date. The [H.4.1 release schedule](https://www.federalreserve.gov/releases/h41/) states the usual Thursday 4:30 p.m. cadence with holiday exceptions. The [WALCL page](https://fred.stlouisfed.org/series/WALCL) also lists October 22 as the next release; the other three selected series showed the same date. The Board's [dated H.4.1 notices](https://www.federalreserve.gov/releases/h41/20251030/) explicitly identify the time convention as Eastern time.

The next Wednesday observation is expected to be October 21 based on the series basis. This is an expectation until the actual release is read, not a fabricated observation or publication timestamp. FRED can update after the Board's scheduled release; do not assume simultaneous availability. A future capture must record its actual retrieval/completion times.

After the release is actually available, an authorized manual check can capture the four series, verify the date sets and source metadata, compare with the retained first capture, and inspect new observations versus changed prior values. An unchanged or delayed result should be reported as such. The separate next-release comparison is scheduled outside this package. This version adds no polling, scheduler, or duplicate future fetch.

## Review the deployed artifacts

The existing publisher can review the public HTTPS demonstration after the approved candidate is deployed: the dated official report at the site root and the fabricated example at `/synthetic/`. This build task does not open a browser, start a server, or retry previously denied file/localhost routes. Content and Node mock DOM checks are recorded separately from screenshots.

The prior singular-day and narrow-screen scroll-cue fixes were published and visually checked before this package. They remain in the source. The newly added date notice, native-input calculation trace, and public evidence panel need a fresh desktop/narrow-screen review after deployment. Check text wrapping, units, dates, chart labels, tables and keyboard scroll cues; exercise the 13/52/all-history controls and download/evidence links. Confirm the saved-capture notice remains clear and that the synthetic route remains visibly labeled. Keep resulting screenshots with the publisher's verification evidence.

**Current candidate outcome:** the new real-data presentation has passed content and mock interaction checks; actual rendered verification is pending publication by the separate publisher. No screenshot or screen-reader claim is made here.
