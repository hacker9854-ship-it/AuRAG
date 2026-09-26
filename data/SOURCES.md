# Data Provenance

Tracks which files in `data/` are real (public) vs. synthetic/self-authored,
per PRD Section 7's "real where possible" principle.

## Real, public sources

- `pnid/sample_pnid.pdf` — "Piping and Instrumentation Diagrams" (Course 462),
  Mark Ludwigson, P.E., PMP, PDH Academy. Publicly hosted continuing-education
  course PDF containing real P&ID example figures (equipment tags, symbols,
  control loops) — used to exercise the Gemini vision P&ID-parsing path.
  Source: https://pdhacademy.com/wp-content/uploads/2023/08/462-Piping-and-Instrumentation-Diagrams.pdf

- Regulatory clauses in `infra/neo4j/seed/06_regulatory_clauses.cypher`:
  - Factories Act 1948, Sections 31 & 37 — primary Government of India
    legislative text, scraped verbatim from
    https://www.indiacode.nic.in/bitstream/123456789/15097/1/factory_acta1948-63.pdf
  - OISD-STD-132 clause references — quoted as cited in a real, public OISD
    case study (OISD/CS/2021-22/E&P/04):
    https://www.oisd.gov.in/public/assets/upload/CaseStudies/1721737695_9597dd0db08b186a3095.pdf
    (The full OISD-STD-132 standard document itself is not freely hosted;
    this case-study citation is the real, public, verifiable source used.)

## Synthetic / self-authored

- `documents/pump_pm_sop.md` — fictional Rampur Processing Unit SOP.
- `documents/incident_log.md` — fictional Rampur Processing Unit incident log.
- All Equipment/WorkOrder/FailureEvent/Person seed data in `infra/neo4j/seed/`
  (Rampur Processing Unit is a fictional plant — no privacy/IP concern).

## Real, public sources (user-supplied)

- `scanned/scnd1.jpeg` — real scanned/handwritten maintenance-log-style
  document, supplied by the user for OCR-path testing in Phase 2.
