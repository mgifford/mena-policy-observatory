# Phase 3: policy comparison UI

Read AGENTS.md. Implement an accessible comparison by obligation (not by count of laws or a country score). Initial topics: public-sector web coverage, WCAG version/level, mobile apps, procurement, accessibility statements, monitoring, complaints, remediation and enforcement. Use real source-linked records only; missing data must show `not researched` or `not established by reviewed evidence`, never `no requirement` without a documented negative search and review.

Provide UAE, Saudi Arabia and Qatar comparison. Each cell must show requirement/claim, legal-effect status, date/version, provenance link, and ambiguity warning where applicable. Support semantic HTML tables with captions and correct row/column headers; accessible filtering/selection via labeled native controls; no color-only status; keyboard and screen reader usability; Arabic RTL; narrow screen reflow; a non-JS baseline. If there is a visual diagram, provide an equivalent structured relationship list.

Add stable deep links to countries, obligations and provision records. Test localized navigation, table semantics, focus, keyboard, zoom, print, and axe; document manual AT tests not yet performed. Keep facts and UI states separate. PR only.
