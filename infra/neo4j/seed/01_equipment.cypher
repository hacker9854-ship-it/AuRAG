// Rampur Processing Unit — Equipment (15 items across 6 process units)

UNWIND [
  {tag_id: 'P-101',   type: 'Centrifugal Pump',         name: 'Feed Pump - Train A',                    location: 'Unit 100 - Feed Section',     criticality: 'High'},
  {tag_id: 'P-102',   type: 'Centrifugal Pump',         name: 'Feed Pump - Train A (Standby)',          location: 'Unit 100 - Feed Section',     criticality: 'High'},
  {tag_id: 'MOT-901', type: 'Electric Motor',           name: 'Drive Motor for P-101',                  location: 'Unit 100 - Feed Section',     criticality: 'Medium'},
  {tag_id: 'FCV-801', type: 'Control Valve',            name: 'Feed Flow Control Valve',                location: 'Unit 100 - Feed Section',     criticality: 'Medium'},
  {tag_id: 'C-201',   type: 'Reciprocating Compressor', name: 'Process Gas Compressor - Train 1',       location: 'Unit 200 - Compression',      criticality: 'High'},
  {tag_id: 'C-202',   type: 'Reciprocating Compressor', name: 'Process Gas Compressor - Train 1 (Standby)', location: 'Unit 200 - Compression',  criticality: 'High'},
  {tag_id: 'V-301',   type: 'Pressure Vessel',          name: 'Feed Surge Vessel',                      location: 'Unit 300 - Separation',       criticality: 'High'},
  {tag_id: 'V-302',   type: 'Separator Vessel',         name: 'Two-Phase Separator',                    location: 'Unit 300 - Separation',       criticality: 'Medium'},
  {tag_id: 'PSV-701', type: 'Pressure Safety Valve',    name: 'Relief Valve on V-301',                  location: 'Unit 300 - Separation',       criticality: 'High'},
  {tag_id: 'HX-401',  type: 'Shell & Tube Heat Exchanger', name: 'Feed/Effluent Exchanger',             location: 'Unit 400 - Heat Recovery',    criticality: 'Medium'},
  {tag_id: 'HX-402',  type: 'Shell & Tube Heat Exchanger', name: 'Trim Cooler',                         location: 'Unit 400 - Heat Recovery',    criticality: 'Medium'},
  {tag_id: 'T-501',   type: 'Distillation Tower',       name: 'Product Fractionation Tower',            location: 'Unit 500 - Fractionation',    criticality: 'High'},
  {tag_id: 'CV-110',  type: 'Control Valve',            name: 'Reflux Control Valve',                   location: 'Unit 500 - Fractionation',    criticality: 'Low'},
  {tag_id: 'R-601',   type: 'Fixed-Bed Reactor',        name: 'Primary Reaction Vessel',                location: 'Unit 600 - Reaction',         criticality: 'High'},
  {tag_id: 'TK-101',  type: 'Atmospheric Storage Tank', name: 'Raw Feed Storage Tank',                  location: 'Tank Farm',                   criticality: 'Medium'}
] AS row
MERGE (e:Equipment {tag_id: row.tag_id})
SET e.type = row.type,
    e.name = row.name,
    e.location = row.location,
    e.criticality = row.criticality;

// HAS_PART — sub-equipment / mounted components
MATCH (parent:Equipment {tag_id: 'P-101'}), (child:Equipment {tag_id: 'MOT-901'})
MERGE (parent)-[:HAS_PART]->(child);

MATCH (parent:Equipment {tag_id: 'V-301'}), (child:Equipment {tag_id: 'PSV-701'})
MERGE (parent)-[:HAS_PART]->(child);

MATCH (parent:Equipment {tag_id: 'T-501'}), (child:Equipment {tag_id: 'CV-110'})
MERGE (parent)-[:HAS_PART]->(child);
