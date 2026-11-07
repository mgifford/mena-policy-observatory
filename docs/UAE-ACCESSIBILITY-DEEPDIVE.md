# UAE accessibility deep dive

**Status:** prototype research note for a conversation with UAE counterparts. **Not authoritative, not legal advice and not an audit.** Manual legal, language and accessibility review has not been performed. Sources were consulted on 2026-11-07; links and pages can change.

This note is deliberately separate from the policy records and visualizations. It does not change any legal-effect status.

## Executive read

1. The UAE has an unusually explicit **national digital accessibility policy** (issued March 2024, TDRA as competent authority), a **national design system with accessibility guidance**, and a **public digital accessibility statement** on the federal portal. This is more than a single agency pledge.
2. The policy's scope is broad on paper: federal entities, semi-government entities, private companies involved in government digital transactions, partners, contractors and service providers. Local government and private-sector entities are addressed more softly ("should take this document into account ... best efforts").
3. The captured technical baseline is **WCAG 2.1 Level AA** in the policy annex and design system, while the federal portal's accessibility statement claims **WCAG 2.1 and 2.2 AA**. Agency statements vary. Ask which baseline is contractually enforced and from when.
4. The policy establishes governance and reporting (Digital Accessibility Officer; entity policies/statements; compliance reporting; annual/semi-annual compliance percentages; Digital Government Enablers indicators). The captured English text does **not** show a public penalty schedule or independent enforcement decisions; that needs confirmation.
5. Arabic is the official language, and the UAE Legislation platform states that the Arabic text prevails for legislation. The English policy PDF and English portal pages are useful but are **not proof that English is equally authoritative**. Our current UAE records are English-source only and need Arabic-source verification.

## What the observatory currently records

| Record | What it is | What it shows | Current limits |
|---|---|---|---|
| `ae-national-digital-accessibility` | National Digital Accessibility Policy (March 2024) | 5 provisions, 5 questions, 4 links, 2 excerpts | English PDF and full Arabic PDF; clause comparison, legal status, authority and enforcement unresolved |
| `ae-federal-law-29-2006` | Federal Law No. 29 of 2006 | 5 provisions, 4 questions, 3 links, 1 Arabic excerpt | Arabic official page plus official English translation; digital scope, implementing instrument and authority unresolved |
| `ae-moe-accessibility` | Ministry of Education digital accessibility policy | 2 provisions, 3 questions | Agency policy, not national law; no excerpt/capture; WCAG 2.1/2.2 AA claim self-described |
| `ae-mof-accessibility` | Ministry of Finance digital accessibility policy | 1 provision, 2 questions | Agency policy; no WCAG version; no excerpt/capture |

The public visualizations show these as **source structure and candidate questions**, not as a UAE compliance conclusion. The 2024 policy is still a policy record, not a legally reviewed instrument.

## Institutional and legal map

| Instrument / source | Type | What it adds | Evidential status |
|---|---|---|---|
| [Federal Law No. 29 of 2006 Concerning the Rights of People with Special Needs](https://u.ae/en/about-the-uae/human-rights-in-the-uae/protecting-the-rights-of-people-of-determination) | Federal law | Broad rights, dignity, equality and protection for people of determination; the official page links the [UN-hosted English text](https://www.un.org/development/desa/disabilities/wp-content/uploads/sites/15/2019/11/United-Arab-Emirates_The-Rights-of-People-with-Special-Needs.pdf) | Binding-law candidate; **digital-specific obligations not established** from the captured material; Arabic text and official English translation now recorded, native legal review outstanding |
| [Cabinet Resolution No. 43 of 2018 Regarding Supporting Special Needs (People of Determination) Work](https://uaelegislation.gov.ae/en/legislations/1174) | Cabinet resolution | Employment/support measures; issued 29 July 2018, effective 1 August 2018, Gazette 633 | Binding instrument; not a digital-accessibility standard |
| [National Policy for Empowering People of Determination](https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/policies/social-affairs/the-national-policy-for-empowering-people-with-special-needs) | National policy | Six pillars: health/rehabilitation, education/vocational rehabilitation/employment, outreach, social protection/family empowerment, and public life/culture/sports | Policy, not a statute; implementation detail not established |
| [National Digital Accessibility Policy](https://uaelegislation.gov.ae/en/policy/details/the-national-digital-accessibility-policy) — [English PDF](https://assets.u.ae/api/public/content/84ec9317f73249c8a2594d76705d3c46?v=8a2f9df6) — [Arabic PDF](https://assets.u.ae/api/public/content/4108f4f6ade849fb92d5ffcb67c2a416?v=35bf36ee) | National policy, issued March 2024 | Digital scope, obligations, governance, Digital Accessibility Officer, technical annex and compliance reporting | Policy instrument; legal enforceability and penalty mechanism unresolved; clause-level Arabic/English comparison outstanding |
| [UAE Digital Government Strategy 2025](https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/strategies-plans-and-visions/government-services-and-digital-transformation/uae-national-digital-government-strategy) | Strategy | "Inclusive by default" and digital government direction | Strategy, not a legal obligation |
| [UAE Design System 3.0 — Accessibility](https://designsystem.gov.ae/guidelines/accessibility) | Technical guidance | WCAG 2.1 AA baseline, WAI references, ARIA, testing at 175% zoom; federal entities instructed to comply | Guidance/standard, not a statute; useful for procurement and design review |
| [UAE Digital Accessibility Statement](https://u.ae/en/Footer/Accessibility) | Public self-statement | Claims WCAG 2.1 and 2.2 AA as minimum; describes audits, feedback and AI-powered accessibility tools | Self-description, not independent certification; third-party content is a stated limitation |
| [MoE](https://www.moe.gov.ae/en/digital-participation/policies/pages/digital-accessibility-policy.aspx) / [MoF](https://mof.gov.ae/en/digital-participation/digital-accessibility-policy/) policies | Agency policies | Departmental commitments, audits/feedback, WCAG references | Agency-level; not national law; version claims differ |

## What the 2024 policy says — and what it does not settle

The policy PDF sets out 14 articles and two annexes. Read together with the official policy page, the important points are:

### Scope

- Digital services provided in the UAE.
- All **federal ministries, authorities and institutions**.
- Sector regulators are to liaise with their licensed **private-sector entities** to ensure compliance.
- **Semi-government entities, consultants, institutions, private companies and others** involved in digital transactions with government, through the competent authority.
- **Partners, contractors and outsourced staff** involved in internal/external digital transactions.
- **Service providers** developing websites, services, channels, apps and systems for federal entities.
- **Local government, semi-government and private-sector entities** "should take this document into account" and exert "best efforts" — softer language than the federal obligations.

This is a broader scope than a website-only policy, but the legal effect of each category — especially "should" and "best efforts" — needs UAE confirmation.

### Standards

- Annex 1: "All public service sites must comply with Level AA of the WCAG 2.1."
- Design system: WCAG 2.1 AA, WAI references, ARIA and 175% zoom testing.
- Federal portal statement: WCAG 2.1 **and 2.2** AA minimum.
- MoE statement: WCAG 2.1 and 2.2 AA.
- MoF statement: cites the national policy and WCAG but does not state a version on the captured page.

The lack of one consistent version is a practical question, not a reason to ignore the policy. Ask which version is in contracts, audits and acceptance criteria, and what transition date applies.

### Governance and reporting

- Each government entity must adopt its own digital accessibility policy/statement and incorporate it into relevant policies and service agreements.
- A **Digital Accessibility Officer** role is defined in Annex 2, with responsibilities for governance, priorities, support, reports and compliance quality.
- Entities must provide reports and information to the competent authority; compliance percentages are updated annually or semi-annually; Digital Government Enablers indicators are measured.
- The policy is subject to periodic review, amendment, cancellation or replacement by the competent authority.

### Enforcement

The policy objective includes defining enforcement and control mechanisms and specifying technical standards. The captured English text shows governance, reporting, compliance percentages and indicators. It does **not** show a public penalty schedule, independent adjudication or a published enforcement decision. Do not assume either that enforcement is absent or that it is automatic.

## Binding law vs policy vs guidance

| Layer | Examples | How to treat it |
|---|---|---|
| **Binding legislation** | Federal Law 29/2006; Cabinet Resolution 43/2018 | Legal obligations; verify Arabic text, scope and any digital-specific provisions |
| **National policy** | 2017 empowerment policy; 2024 National Digital Accessibility Policy | Government policy direction and entity obligations; legal enforceability/penalties to confirm |
| **Technical guidance** | Design System 3.0; Annex 1; WCAG | Design, procurement and audit baseline; not law by itself |
| **Self-description** | u.ae accessibility statement; agency statements | Evidence of claimed practice; not independent verification |
| **Our records** | Source-structure visualizations | Research in progress; not legal findings or compliance ratings |

The strongest current public chain is therefore **policy + governance + technical guidance**, not a demonstrated court-enforced digital-accessibility statute. That distinction matters when talking to UAE counterparts.

## Language and authority

- The UAE's official language is Arabic. The UAE Legislation platform states on its legislation pages that the English version is provided for accuracy but **the Arabic text prevails** in case of conflict ([example](https://uaelegislation.gov.ae/en/legislations/1174)).
- The 2024 policy PDF is an English edition; the policy page is also available through the official legislation platform. Do not assume the English PDF is the authoritative expression without confirmation.
- Our UAE records currently use **English source pages** and mark authoritative language as unknown. This is a real limitation for any legal comparison.
- For a bilingual comparison, capture the Arabic policy/legal text, record the source language and translation status, and have Arabic review before drawing wording-sensitive conclusions.
- English is widely used in UAE government digital services, but interface English does not make English the authoritative legal text.

## Accessibility practice: questions the public evidence raises

1. **Version baseline:** Is the operative standard WCAG 2.1 AA, 2.2 AA, or both? Which applies to new services, existing services, mobile apps, documents and third-party content?
2. **Scope:** Which private-sector entities are legally or contractually bound — only government contractors, or all licensed service providers in a sector? How are local governments and free zones covered?
3. **Enforcement:** What happens after a low compliance percentage or a complaint? Are there financial or procurement consequences, published decisions, or only management indicators?
4. **Digital Accessibility Officer:** Is the role independent, trained, resourced and empowered to block releases? What is its reporting line?
5. **Procurement:** Are accessibility requirements, acceptance tests, VPAT/ACR evidence and remediation clauses in tenders and contracts? Are contractors tested on the same baseline?
6. **Testing:** Is automated testing supplemented by manual keyboard, screen-reader and disabled-user testing? Which assistive technologies and browsers?
7. **Arabic and sign language:** Is Arabic content tested with Arabic screen readers? Is Emirati Sign Language video provided where needed? Is Easy Read available?
8. **Overlays and AI tools:** The federal portal describes "AI-powered accessibility tools". Are these supplements to accessible code, or are they being treated as a substitute? The design system's ARIA guidance suggests the former is intended.
9. **Complaints and remedies:** What is the route, timeframe and published data for accessibility complaints? Is there a remedy for a failed service journey?
10. **Legacy and third parties:** How are archived documents, embedded maps, payment providers, identity services and social media content covered?
11. **Metrics:** What exactly is measured by the compliance percentage and Digital Government Enablers indicators? Are the underlying results public?
12. **Policy status:** Is the 2024 policy a Cabinet-approved instrument? What is its legal basis and relationship to Federal Law 29/2006?

## Suggested framing for the conversation

A useful opening is not "is the UAE compliant?" but:

> "We are mapping how federal policy, technical standards and agency practice fit together. We can see a national policy, a design system and public accessibility statements. We are trying to distinguish binding obligations from guidance and from self-reported practice, especially for private-sector providers and Arabic-language content. Which of these does the UAE consider the authoritative baseline, and what evidence would you point a reviewer to?"

This avoids ranking the UAE and invites the counterpart to clarify legal status, scope and evidence.

## Gaps in the current observatory

- **Federal Law 29/2006** now has a structured record with an Arabic authoritative expression, an official English translation expression and five provisions (captured 2026-11-07). The digital scope is still a legal question, not a finding.
- The **2024 National Digital Accessibility Policy** record now has five provisions, the March 2024 English PDF and the full Arabic PDF. The two language expressions have not been compared clause by clause.
- **Cabinet Resolution 43/2018** is recorded as a related instrument, not a standalone accessibility record; it addresses employment/support and its full text was not captured.
- **Federal Law 29/2006 amendment list** shows one 2009 amendment; the consolidated text and substantive effect are not captured.
- No official instrument for the Article 23 building-standard Cabinet decision was located in the sources consulted; this remains an explicit gap.
- No local-emirate records (Dubai/Abu Dhabi) or free-zone authorities.
- No procurement, audit, complaint or enforcement evidence.
- No manual accessibility or native Arabic review.

## Evidence captured on 2026-11-07

- **Federal Law 29/2006:** Arabic official page and official English translation page retrieved; 5 provisions recorded; Arabic expression marked authoritative, English translation expression unreviewed. Official metadata: issued 13 August 2006; published/effective 26 August 2006; Official Gazette No. 453; one amendment listed.
- **2024 National Digital Accessibility Policy:** official English PDF and full Arabic PDF retrieved; both language expressions recorded. Policy page records issue date 18 March 2024 and TDRA as lead authority. Five policy provisions now recorded. Clause-level comparison remains outstanding.
- No capture bytes or checksums were stored; the records point to the official pages and explicitly say so.

## Recommended next evidence, if the UAE conversation continues

1. Compare the full Arabic 2024 policy PDF with the English PDF clause by clause, especially scope, technical standards, governance and enforcement.
2. Capture the 2024 policy's technical annex with locators and permitted checksums.
3. Obtain and record the Cabinet decision contemplated by Article 23, and the consolidated Federal Law 29/2006 after its one listed 2009 amendment.
4. Record Federal Law 29/2006, the 2024 policy and Cabinet Resolution 43/2018 as separate source records; the first two now exist, the resolution is only a related link.
4. Ask for the entity-level Digital Accessibility Officer contact/role description, a sample accessibility statement, and a redacted audit/acceptance test template.
5. Ask for the procurement/contract clause used for digital services and the remediation process.
6. Ask which services are considered priority for people of determination and senior citizens, and how user testing is conducted.
7. Record findings as candidate interpretations only; do not convert them into legal-effect findings.

## Source register

- UAE Government, [Protecting the rights of people of determination](https://u.ae/en/about-the-uae/human-rights-in-the-uae/protecting-the-rights-of-people-of-determination), with link to Federal Law No. 29 of 2006.
- UAE Government, [National Policy for Empowering People of Determination](https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/policies/social-affairs/the-national-policy-for-empowering-people-with-special-needs).
- UAE Legislation, [Cabinet Resolution No. 43 of 2018](https://uaelegislation.gov.ae/en/legislations/1174).
- UAE Legislation, [Federal Law No. 29 of 2006 amendment list](https://uaelegislation.gov.ae/ar/legislations/1172/modifications).
- UAE Legislation, [The National Digital Accessibility Policy](https://uaelegislation.gov.ae/en/policy/details/the-national-digital-accessibility-policy); [English PDF](https://assets.u.ae/api/public/content/84ec9317f73249c8a2594d76705d3c46?v=8a2f9df6); [Arabic PDF](https://assets.u.ae/api/public/content/4108f4f6ade849fb92d5ffcb67c2a416?v=35bf36ee).
- UAE Government, [National Digital Accessibility Policy page](https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/policies/government-services-and-digital-transformation/national-digital-accessibility-policy).
- UAE Government, [Digital Accessibility Statement](https://u.ae/en/Footer/Accessibility).
- UAE Design System 3.0, [Accessibility guideline](https://designsystem.gov.ae/guidelines/accessibility).
- UAE Government, [UAE Digital Government Strategy 2025](https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/strategies-plans-and-visions/government-services-and-digital-transformation/uae-national-digital-government-strategy).
- UAE Ministry of Education, [Digital Accessibility Policy](https://www.moe.gov.ae/en/digital-participation/policies/pages/digital-accessibility-policy.aspx).
- UAE Ministry of Finance, [Digital Accessibility Policy](https://mof.gov.ae/en/digital-participation/digital-accessibility-policy/).
- Existing observatory records: `ae-federal-law-29-2006`, `ae-national-digital-accessibility`, `ae-moe-accessibility`, `ae-mof-accessibility`.

## Bottom line

The UAE has a credible national policy architecture and a public accessibility commitment. The open questions are **legal status, enforceable scope, consistent WCAG baseline, Arabic authority and evidence of practice** — not whether any policy exists. Those are the questions to take into the conversation.

**Prototype note. Not authoritative. No legal or compliance conclusion.**
