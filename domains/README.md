# Domains Data

Local domain-specific inputs and generated artifacts live here.

- `site_context/`: hand-authored supplemental JSON for a website.
- `crawls/`: generated crawled page extraction data. Gitignored except `.gitkeep`.
- `intelligence/`: generated LLM domain intelligence preflight JSON. Gitignored except `.gitkeep`.

Domain audits run the intelligence preflight before crawling unless skipped with
`skip_domain_intelligence`.
