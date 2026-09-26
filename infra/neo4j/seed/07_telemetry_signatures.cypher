// Rampur Processing Unit — telemetry signatures for the Phase 7 proactive
// layer. Each FailureEvent gets a `signature_json` string property (Neo4j has
// no native nested-map property type) holding the numeric feature-vector
// "fingerprint" of that failure, sparse — only the 1-2 dimensions its own
// failure mode actually involves. Values derived from each event's existing
// `symptom` text where a number is stated (FE-001, FE-004); otherwise a
// plausible value stands in for the qualitative description (FE-002, FE-003,
// FE-005, FE-006) — see NOTES.md Phase 7 for the full derivation table.
// Nominal (healthy-baseline) values are NOT stored here — they're a
// generator-only synthesis assumption, kept in telemetry/generator.py.

UNWIND [
  {id: 'FE-001', signature_json: '{"vibration_mm_s": 7.5, "bearing_temp_c": 87}'},
  {id: 'FE-002', signature_json: '{"discharge_temp_c": 165}'},
  {id: 'FE-003', signature_json: '{"outlet_temp_deviation_c": 12}'},
  {id: 'FE-004', signature_json: '{"set_pressure_pct": 90}'},
  {id: 'FE-005', signature_json: '{"differential_pressure_kpa": 45}'},
  {id: 'FE-006', signature_json: '{"seal_leak_rate_ml_min": 15}'},
  {id: 'FE-007', signature_json: '{"vibration_mm_s": 6.8, "bearing_temp_c": 60}'}
] AS row
MATCH (f:FailureEvent {id: row.id})
SET f.signature_json = row.signature_json;
