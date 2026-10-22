# Source-data rights and public release boundary

## Project license scope

This license applies to original project code, documentation, and synthetic
fixtures. It does not relicense source data, source metadata pages, or any
third-party material. See DATA_LICENSE.md and docs/PRIOR_ART.md.

Reviewed 2026-10-21. The MIT license covers original project material and synthetic examples, not third-party source data or captured webpage markup.

## Selected official series

All four originate with the **Board of Governors of the Federal Reserve System (US), H.4.1 Factors Affecting Reserve Balances**, retrieved via **FRED, Federal Reserve Bank of St. Louis**. Each series page identifies the data as **Public Domain: Citation Requested**:

| ID | Series and source |
| --- | --- |
| WALCL | [Consolidated total assets, Wednesday level](https://fred.stlouisfed.org/series/WALCL) |
| WDTGAL | [Treasury general account, Wednesday level](https://fred.stlouisfed.org/series/WDTGAL) |
| WLRRAL | [Total reverse-repo liabilities, Wednesday level](https://fred.stlouisfed.org/series/WLRRAL) |
| WRBWFRBL | [Reserve balances, Wednesday level](https://fred.stlouisfed.org/series/WRBWFRBL) |

Units are USD millions, not seasonally adjusted, weekly as of Wednesday. The [Board's copyright notice](https://www.federalreserve.gov/disclaimer.htm) permits copying and distribution of its public-domain information unless otherwise indicated, with attribution. [FRED's legal notice](https://fred.stlouisfed.org/legal/) describes the permission and citation conditions for the public-domain tag, separately from proprietary series and FRED site content. Its prohibited-use conditions continue to apply. The four selected numerical series can be displayed or published with those source conditions and attribution; they must not be represented as original official data authored by this project.

Use the citation: **Board of Governors of the Federal Reserve System (US), [official series title] [ID], retrieved from FRED, Federal Reserve Bank of St. Louis; [series URL], [actual retrieval timestamp].** Mark derived calculations as Open Macro Lab calculations. Do not imply institutional endorsement or use official logos/seals.

## What this public release includes

The ready-made report, raw example CSVs, saved synthetic snapshots, and fixtures use fabricated data under MIT. Synthetic capture times and revisions are scenario metadata, not official publication history. They are labeled explicitly in the report and source files' surrounding documentation.

The audit documentation quotes selected numerical reference values from the official series with source links and capture context. It preserves the first-baseline limitation. The full original real snapshot and its raw FRED HTML pages remain outside this source release. This avoids treating captured website markup, logos, scripts, or other source-page content as project-licensed material. No official graph image or website design is redistributed.

## Future acquisitions

`fetch` saves public CSV and HTML responses locally for evidence and contract verification. Keep those generated directories out of version control by default. The selected data rights do not automatically license all downloaded HTML or any later substituted series. Review the current source notice before a separately authorized redistribution.

`RRPONTSYD` and `WRESBAL` are not inputs. The former is a different daily overnight measure; the latter is a weekly-average reserve measure. Neither may be silently substituted for the documented Wednesday-level series. Preserve all source attributions and do not broaden a future release's data scope based on this review.
