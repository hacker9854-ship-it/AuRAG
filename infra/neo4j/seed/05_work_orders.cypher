// Rampur Processing Unit — WorkOrders (12 records)
// WO-1002 and WO-1007 are deliberately status "Overdue" — the missed preventive
// maintenance that root-causes FE-001 and FE-004 respectively, for RCA Agent
// traversal demos. `description` is an additive property beyond the PRD's
// minimal WorkOrder field list, added to give the retrieval layer real text
// to match on — see NOTES.md.

UNWIND [
  {id: 'WO-1001', date: '2025-03-15', type: 'Corrective', status: 'Closed',  equipment: 'P-101',   person: 'PER-002', description: 'Replaced drive-end bearing and re-greased per OEM spec'},
  {id: 'WO-1002', date: '2025-02-01', type: 'Preventive', status: 'Overdue', equipment: 'P-101',   person: 'PER-006', description: 'Scheduled quarterly lubrication service'},
  {id: 'WO-1003', date: '2025-05-03', type: 'Corrective', status: 'Closed',  equipment: 'C-201',   person: 'PER-001', description: 'Cleaned fouled intercooler tubes, reset high-discharge-temperature trip'},
  {id: 'WO-1004', date: '2025-04-01', type: 'Preventive', status: 'Closed',  equipment: 'C-202',   person: 'PER-004', description: 'Standby compressor functional test and inspection'},
  {id: 'WO-1005', date: '2025-06-21', type: 'Corrective', status: 'Closed',  equipment: 'HX-401',  person: 'PER-002', description: 'Chemical cleaning of tube bundle to remove scale'},
  {id: 'WO-1006', date: '2025-08-12', type: 'Corrective', status: 'Closed',  equipment: 'PSV-701', person: 'PER-003', description: 'Replaced relief valve spring and recalibrated set pressure'},
  {id: 'WO-1007', date: '2025-07-01', type: 'Preventive', status: 'Overdue', equipment: 'PSV-701', person: 'PER-004', description: 'Scheduled annual PSV calibration'},
  {id: 'WO-1008', date: '2025-10-06', type: 'Corrective', status: 'Closed',  equipment: 'T-501',   person: 'PER-002', description: 'Replaced damaged trays, sections 12-15'},
  {id: 'WO-1009', date: '2025-09-15', type: 'Inspection', status: 'Closed',  equipment: 'T-501',   person: 'PER-001', description: 'Post-upset internal inspection following a process trip'},
  {id: 'WO-1010', date: '2026-01-19', type: 'Corrective', status: 'Closed',  equipment: 'P-102',   person: 'PER-004', description: 'Replaced mechanical seal'},
  {id: 'WO-1011', date: '2026-02-10', type: 'Preventive', status: 'Closed',  equipment: 'R-601',   person: 'PER-005', description: 'Catalyst bed pressure-drop inspection'},
  {id: 'WO-1012', date: '2026-04-05', type: 'Preventive', status: 'Open',    equipment: 'TK-101',  person: 'PER-006', description: 'Scheduled tank integrity inspection (API-653 style)'}
] AS row
MERGE (w:WorkOrder {id: row.id})
SET w.date = row.date,
    w.type = row.type,
    w.status = row.status,
    w.description = row.description
WITH w, row
MATCH (e:Equipment {tag_id: row.equipment})
MERGE (w)-[:PERFORMED_ON]->(e)
WITH w, row
MATCH (p:Person {person_id: row.person})
MERGE (w)-[:PERFORMED_BY]->(p);
