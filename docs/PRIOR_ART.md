# Prior art and license review

Inspected 2026-10-21 using public repository pages and read-only GitHub content queries, before implementation. No repository was cloned, forked, created, or modified. No code or data from these projects is imported or copied.

| Project | Inspected scope | License finding | Decision |
| --- | --- | --- | --- |
| [lauren-shih/macro-liquidity-pipeline](https://github.com/lauren-shih/macro-liquidity-pipeline) | README architecture, source map, monitoring/point-in-time separation, LICENSE | [MIT](https://github.com/lauren-shih/macro-liquidity-pipeline/blob/main/LICENSE), copyright 2026 Lauren Shih | Relevant prior art for distinct monitoring and vintage-aware research. Acknowledge that data ingestion and PIT safeguards are not new inventions. Its broad indicator pipeline and credentialed API workflow exceed this small release. |
| [R1cK-ChaN/macro-data-service](https://github.com/R1cK-ChaN/macro-data-service) | README architecture, root contents, pyproject, recursive tree license-file check | No LICENSE/COPYING/NOTICE file found in inspected default-branch recursive tree; pyproject has no license declaration | Public visibility is not a reuse license. No source reuse. Relevant prior art for release availability, source contracts, and operational data quality. |
| [jalonso1979/puremacro](https://github.com/jalonso1979/puremacro) | README modeling scope and LICENSE | [MIT](https://github.com/jalonso1979/puremacro/blob/main/LICENSE), copyright 2026 Jorge Alonso Ortiz | A broad macroeconometrics/structural modeling library. No model estimation is needed for these accounting recipes; avoid adding a large numerical dependency. |

The differentiator is a small maintainable research publication: explicit recipe semantics, conservative knowledge dates, immutable captured evidence, and an exact explanation of changed readings. It is not a claim of novel ingestion technology or an audited endorsement of the referenced projects.

License status is scoped to inspected files at the review date, not a guarantee about all dependencies, contributors, later repository changes, or third-party data. Because none of their code was reused, their license texts are not incorporated into this project's MIT license. If future work copies MIT-licensed code, preserve the upstream copyright and permission notice in the distributed material. Do not reuse macro-data-service code unless a suitable license is independently established.
