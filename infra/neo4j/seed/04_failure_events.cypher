// Rampur Processing Unit — FailureEvents with realistic symptom/root_cause.
// All DOCUMENTED_IN the incident log (DOC-LOG-001); see 03_documents_and_procedures.cypher

UNWIND [
  {id: 'FE-001', date: '2025-03-14', equipment: 'P-101',   symptom: 'Excessive vibration (>7 mm/s RMS) and drive-end bearing housing temperature rising above 85C during routine rounds', root_cause: 'Drive-end bearing wear caused by a lubrication interval lapse — scheduled quarterly greasing (WO-1002) was never completed'},
  {id: 'FE-002', date: '2025-05-02', equipment: 'C-201',   symptom: 'Unexpected trip on high discharge temperature interlock during startup', root_cause: 'Fouled intercooler tubes reduced heat transfer, causing second-stage discharge temperature to exceed the trip setpoint'},
  {id: 'FE-003', date: '2025-06-20', equipment: 'HX-401',  symptom: 'Gradual rise in feed outlet temperature deviation from design curve over 6 weeks, reduced heat recovery', root_cause: 'Tube-side fouling from scale buildup after exceeding the recommended cleaning interval'},
  {id: 'FE-004', date: '2025-08-11', equipment: 'PSV-701', symptom: 'PSV-701 lifted at approximately 90% of nameplate set pressure, causing a premature relief event during normal operation', root_cause: 'Relief valve spring fatigue combined with a missed annual calibration (WO-1007 was never completed) allowed set-pressure drift to go undetected'},
  {id: 'FE-005', date: '2025-10-05', equipment: 'T-501',   symptom: 'Tower flooding observed; differential pressure across trays rose sharply above the normal operating band', root_cause: 'Tray damage from an upstream slug-flow event during a prior process upset, not caught during the post-upset inspection (WO-1009)'},
  {id: 'FE-006', date: '2026-01-18', equipment: 'P-102',   symptom: 'Visible mechanical seal leak detected during routine operator rounds', root_cause: 'Mechanical seal degradation after exceeding rated service life without replacement'},
  {id: 'FE-007', date: '2026-02-11', equipment: 'P-101',   symptom: 'Broadband vibration rose while bearing temperature remained near normal during low tank level operation', root_cause: 'Suction starvation caused incipient cavitation; the low-level operating limit was not maintained'}
] AS row
MERGE (f:FailureEvent {id: row.id})
SET f.date = row.date,
    f.symptom = row.symptom,
    f.root_cause = row.root_cause
WITH f, row
MATCH (e:Equipment {tag_id: row.equipment})
MERGE (f)-[:OCCURRED_ON]->(e)
WITH f
MATCH (d:Document {id: 'DOC-LOG-001'})
MERGE (f)-[:DOCUMENTED_IN]->(d);
