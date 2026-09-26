// Rampur Processing Unit — Personnel (6 people, spread across years_to_retirement
// to exercise the knowledge-retirement-risk view — Vikram Singh is the deliberate
// high-risk case: 1 year out, tied to multiple WorkOrders/FailureEvents below)

UNWIND [
  {person_id: 'PER-001', name: 'Vikram Singh',  role: 'Maintenance Supervisor',          department: 'Mechanical',              years_to_retirement: 1},
  {person_id: 'PER-002', name: 'Ramesh Kumar',  role: 'Senior Rotating Equipment Engineer', department: 'Mechanical',           years_to_retirement: 2},
  {person_id: 'PER-003', name: 'Deepak Rao',    role: 'Safety Officer',                  department: 'HSE',                     years_to_retirement: 5},
  {person_id: 'PER-004', name: 'Suresh Patil',  role: 'Instrumentation Technician',      department: 'Instrumentation & Control', years_to_retirement: 8},
  {person_id: 'PER-005', name: 'Anita Verma',   role: 'Process Engineer',                department: 'Process',                 years_to_retirement: 15},
  {person_id: 'PER-006', name: 'Priya Nair',    role: 'Junior Maintenance Engineer',     department: 'Mechanical',              years_to_retirement: 30}
] AS row
MERGE (p:Person {person_id: row.person_id})
SET p.name = row.name,
    p.role = row.role,
    p.department = row.department,
    p.years_to_retirement = row.years_to_retirement;
