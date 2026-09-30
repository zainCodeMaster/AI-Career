"""Real job source adapters for CareerOS Phase 4.x.

Each adapter implements the ``BaseJobSource`` interface and produces
``RawJob`` objects that flow through the existing normalization/dedup
pipeline into the ``Job`` table.

Adapters are grouped by category:
- Government sources (public HTML page parsing)
- Private job boards (public page / RSS parsing)
- Company career pages (JSON-LD / schema.org JobPosting)
- Unsupported sources (LinkedIn, Indeed, Google Jobs — no authorized integration)
"""
