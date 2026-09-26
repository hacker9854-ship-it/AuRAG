// Real regulatory clauses (Section 7 sourcing principle: reference data = real).
//
// Sources:
// - Factories Act 1948, Sections 31 & 37 — primary legislative text, scraped
//   verbatim from indiacode.nic.in (Government of India official text).
// - OISD-STD-132 (Inspection of Pressure Relieving Devices) — clause
//   references and requirement text as quoted in a real, public OISD case
//   study (OISD/CS/2021-22/E&P/04, oisd.gov.in), which cites the specific
//   clause numbers verbatim. The full OISD-STD-132 document itself is not
//   freely hosted; this case-study citation is the real, public, verifiable
//   source used here.

UNWIND [
  {clause_id: 'FACT1948-S31', source: 'Factories Act 1948', requirement_text: 'If in any factory, any plant or machinery or any part thereof is operated at a pressure above atmospheric pressure, effective measures shall be taken to ensure that the safe working pressure of such plant or machinery or part is not exceeded.'},
  {clause_id: 'FACT1948-S37', source: 'Factories Act 1948', requirement_text: 'Where in any factory any manufacturing process produces dust, gas, fume or vapour of such character and to such extent as to be likely to explode on ignition, all practicable measures shall be taken to prevent any such explosion by effective enclosure of the plant or machinery, removal or prevention of accumulation of such dust, gas, fume or vapour, and exclusion or effective enclosure of all possible sources of ignition.'},
  {clause_id: 'OISD-STD-132-10.2ii', source: 'OISD-STD-132', requirement_text: 'The Testing and Maintenance History of the Safety Relief Valve must be provided to the in-house testing team prior to testing or calibration (Clause 10.2(ii)).'},
  {clause_id: 'OISD-STD-132-TESTMED', source: 'OISD-STD-132', requirement_text: 'Water, air or an inert gas such as bottled nitrogen is the recommended testing medium for pressure testing of Safety Relief Valves; hydrocarbon or natural gas shall not be used as the test medium.'}
] AS row
MERGE (r:RegulatoryClause {clause_id: row.clause_id})
SET r.source = row.source,
    r.requirement_text = row.requirement_text;

// APPLIES_TO — pressure-plant clauses apply to the pressure vessel and its PSV
MATCH (r:RegulatoryClause {clause_id: 'FACT1948-S31'}), (e:Equipment {tag_id: 'V-301'})
MERGE (r)-[:APPLIES_TO]->(e);
MATCH (r:RegulatoryClause {clause_id: 'FACT1948-S31'}), (e:Equipment {tag_id: 'PSV-701'})
MERGE (r)-[:APPLIES_TO]->(e);

// Explosive/flammable-atmosphere clause applies to compressors and reactor
MATCH (r:RegulatoryClause {clause_id: 'FACT1948-S37'}), (e:Equipment {tag_id: 'C-201'})
MERGE (r)-[:APPLIES_TO]->(e);
MATCH (r:RegulatoryClause {clause_id: 'FACT1948-S37'}), (e:Equipment {tag_id: 'C-202'})
MERGE (r)-[:APPLIES_TO]->(e);
MATCH (r:RegulatoryClause {clause_id: 'FACT1948-S37'}), (e:Equipment {tag_id: 'R-601'})
MERGE (r)-[:APPLIES_TO]->(e);

// OISD-STD-132 clauses apply directly to the PSV — this is the compliance
// gap the Compliance Agent should be able to surface: FE-004's root cause
// (missed WO-1007 calibration) is exactly what OISD-STD-132-10.2ii exists
// to prevent.
MATCH (r:RegulatoryClause {clause_id: 'OISD-STD-132-10.2ii'}), (e:Equipment {tag_id: 'PSV-701'})
MERGE (r)-[:APPLIES_TO]->(e);
MATCH (r:RegulatoryClause {clause_id: 'OISD-STD-132-TESTMED'}), (e:Equipment {tag_id: 'PSV-701'})
MERGE (r)-[:APPLIES_TO]->(e);
