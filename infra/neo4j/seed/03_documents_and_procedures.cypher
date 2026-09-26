// Rampur Processing Unit — Documents + Procedure
// source_file paths match files placed under data/ (see repo README).
// DOC-PID-001 / DOC-SCAN-001 point at files sourced separately (real public
// P&ID sample, real user-supplied scanned document) — see NOTES.md.

UNWIND [
  {id: 'DOC-SOP-001',  type: 'Procedure Manual', title: 'Centrifugal Pump Preventive Maintenance SOP', date: '2025-01-05', source_file: 'data/documents/pump_pm_sop.md'},
  {id: 'DOC-LOG-001',  type: 'Incident Log',      title: 'Maintenance & Incident Log — Rampur Processing Unit', date: '2026-01-19', source_file: 'data/documents/incident_log.md'},
  {id: 'DOC-PID-001',  type: 'P&ID Diagram',      title: 'Sample Process & Instrumentation Diagram', date: '2026-07-08', source_file: 'data/pnid/sample_pnid.pdf'},
  {id: 'DOC-SCAN-001', type: 'Scanned Log',       title: 'Handwritten Shift/Maintenance Log (scanned)', date: '2026-07-08', source_file: 'data/scanned/scnd1.jpeg'}
] AS row
MERGE (d:Document {id: row.id})
SET d.type = row.type,
    d.title = row.title,
    d.date = row.date,
    d.source_file = row.source_file;

MERGE (proc:Procedure {id: 'PROC-001'})
SET proc.title = 'Centrifugal Pump Preventive Maintenance SOP',
    proc.version = '2.1';

MATCH (proc:Procedure {id: 'PROC-001'}), (p101:Equipment {tag_id: 'P-101'})
MERGE (proc)-[:GOVERNS]->(p101);
MATCH (proc:Procedure {id: 'PROC-001'}), (p102:Equipment {tag_id: 'P-102'})
MERGE (proc)-[:GOVERNS]->(p102);
