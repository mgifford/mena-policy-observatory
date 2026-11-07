# Three-source verification and monitoring pilot

**Date:** 2026-11-07 (UTC)\
**Baseline:** `main` at `4257c1f`\
**Status:** evidence captured for three existing candidates; no legal verification, no change events and no reviewed findings.

This pilot exercises the publisher registry, source captures, source checks and the change-review workflow against three real official pages already represented in the candidate inventory. It is a bounded retrieval exercise, not a monitoring service.

## Selection rationale

| Candidate | Jurisdiction | Reported instrument | Publisher observed | Format | Why selected |
|---|---|---|---|---|---|
| `mena-t02-002` | Algeria | Law 25-11 of 2025 amending Law 18-07 | Journal Officiel (`joradp.dz`) | PDF | Official Gazette source, French, and a reported amendment relation to `mena-t02-001`. |
| `bh-personal-data-30-2018` | Bahrain | Law No. 30 of 2018 on personal data protection | Legislation and Legal Opinion Commission (`lloc.gov.bh`) | HTML | A different jurisdiction and a legislation portal; the page records the Official Gazette reference and links English and Arabic versions. |
| `om-national-digital-accessibility` | Oman | National Digital Accessibility Policy | Ministry of Transport, Communications and Information Technology (`mtcit.gov.om`) | HTML | A different jurisdiction and an official policy page rather than a statute; English/Arabic site. |

The set covers three jurisdictions, two formats, one reported amendment relationship, French and English source pages, and three different authority types (gazette, legislation portal, ministry). All three URLs already existed in `research-toolkit/sources/candidate-sources.json`; no new country or domain was added.

## Retrieval method

- One HTTPS `GET` per URL, with a descriptive user agent (`MENA-Policy-Observatory/0.1`), 60-second timeout and no retries or crawling.
- `robots.txt` checked first: `www.joradp.dz` and `www.lloc.gov.bh` returned 404 (no robots file); `www.mtcit.gov.om` returned a policy disallowing only `/web/login`. The retrieved pages are outside that path.
- Bytes were hashed with SHA-256 and the temporary files were deleted. Full text and PDF bytes are **not stored** in the repository; only metadata, checksum, URL and language are recorded.
- No authentication, anti-bot bypass, rate-limit circumvention or OCR was used.

## Evidence recorded

| Capture | Candidate | HTTP | Content type | Bytes | SHA-256 | Captured (UTC) | Language |
|---|---|---|---|---|---|---|---|
| `cap-mena-t02-002-855ff487d526` | `mena-t02-002` | 200 | `application/pdf` | 266,075 | `855ff487d5263d307d9295ce386e9bb96716084b7d09afb7892e16374bb91372` | 2026-11-07T03:54:52Z | fr |
| `cap-bh-personal-data-30-2018-c72eb36f1d31` | `bh-personal-data-30-2018` | 200 | `text/html; charset=utf-8` | 31,350 | `c72eb36f1d31de9ab3c09b87826955449c849b78b2d81a925ad2e568bc4a88b7` | 2026-11-07T03:54:54Z | en |
| `cap-om-national-digital-accessibility-2393b1412795` | `om-national-digital-accessibility` | 200 | `text/html; charset=utf-8` | 145,299 | `2393b14127951ed2b679323e0666d607b6a52b6b246bd7aec9bdb0ef4931eb8b` | 2026-11-07T03:54:58Z | en |

Registry notes:

- The Algeria PDF is the Official Gazette file `JO-FRANCAIS/2025/F2025048.pdf`. Its PDF metadata names “Journal Officiel”; the reported Law 25-11 identity comes from the candidate title and was **not** verified in extracted text. No PDF text extraction was performed.
- The Bahrain URL is a Legislation and Legal Opinion Commission landing page. The page itself records “LAW NO. (30) OF 2018 WITH RESPECT TO PERSONAL DATA PROTECTION LAW”, date 19 July 2018 and Official Gazette No. 3375, and links English and Arabic versions. It is an index page, not the full instrument text.
- The Oman URL is an MTCIT policy page. It records “Date Published: 01 August 2022” and states that the policy applies to all units of the State administrative apparatus. It is a policy page, not a verified instrument text.
- Publisher names and authority types were observed on the retrieved pages or document metadata and recorded as `unverified` in `publishers.json`. They are not independently confirmed.
- All three source checks now record `retrieval_status: success`, `last_successful_retrieval: 2026-11-07`, HTTP status, final URL and content type. Freshness is within the 180-day interval as of `as_of: 2026-11-07`. Legal verification remains `unreviewed`.

## What this establishes

- The three recorded URLs were reachable over HTTPS at the recorded times and returned the recorded status, content type, byte length and checksum.
- A source-check record and a captured-item metadata record now exist for each candidate.
- Publisher identity evidence is recorded with its limitation.
- The public source pages show retrieval outcome, freshness, captured version metadata and unreviewed legal status.

## What this does not establish

- It does not verify the legal effect, authenticity, completeness or current in-force status of any instrument.
- It does not verify that the Algeria PDF contains Law 25-11, that the Bahrain page’s linked texts are current, or that the Oman page reflects the operative policy text.
- It does not establish complete national coverage, source currency after the capture, or translation quality.
- It does not create a change event. With no previous capture, no comparison was possible. A later recapture can produce an observation through the WP5 workflow.
- It does not mark any source legally reviewed. All three checks remain `unreviewed`.

## Failures and limitations

- `robots.txt` returned 404 for two publishers; no explicit robots policy was available.
- No retry or change detection was attempted. Page templates, redirects and content may change after capture.
- The Bahrain and Oman sources are an index page and a policy page, not full legal text. A reviewer must decide whether they are sufficient evidence for the research question.
- The Algeria PDF metadata does not expose its title; identity depends on the candidate record and the Gazette file path.
- The captured bytes are not retained, so no textual comparison can be repeated from this repository. Re-retrieval would be required.
- No native Arabic/French review and no manual assistive-technology testing were part of this pilot.

## Review requirements

- Confirm publisher identity and authority.
- Confirm whether the Bahrain landing page and Oman policy page are adequate primary evidence or only discovery aids.
- Verify the Algeria Gazette issue and whether it contains Law 25-11.
- Record legal-effect and applicability only after qualified review.
- Decide whether a future recapture interval and permitted storage are appropriate.
- Native Arabic/French and accessibility reviews remain outstanding.

## Next

A later authorized step could recapture these three sources after an interval, record a real observation only if the bytes or extracted text differ, and create review tasks through the existing workflow. No such monitoring schedule has been created.
