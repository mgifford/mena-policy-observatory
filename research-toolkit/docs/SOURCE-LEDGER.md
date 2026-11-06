# Source ledger and source changes

Source lead -> official URL -> retrieved exact bytes (when authorized) -> SHA-256 -> structured metadata -> clause citation -> interpretation -> candidate RuleSpec -> publication.

Keep a source ledger with document ID, canonical URL, publisher, language, title, acquisition route, retrieved UTC timestamp, response metadata, original filename, bytes location, SHA-256, license/republication permission, review state, link to source, version of source, and relationship to previous versions. Never invent a checksum.

When source content changes, record the old/new hashes and produce human-readable diff at clause granularity if extraction permits. Source changes should create an issue and block stale rule publication until reviewed. Do not automatically overwrite legal text or infer a law has changed merely because a PDF's bytes differ (metadata may change).

Offline `scripts/manifest.py` can checksum local artifacts; it is not an authenticated source capture system and cannot establish source authenticity.
