# Public Dataset Provenance & Replay Documentation

**Standard**: Bitshala BOSS Battle 2026 Technical Honesty & Verification Guidelines  
**Classification**: `PUBLIC DATASET / REPLAY`  
**Strict Prohibition**: Never claim public dataset replay is "live SCADA" or "real-time plant data".  

---

## 1. Selected Dataset Overview

- **Dataset Title**: NASA IMS (Intelligent Maintenance Systems) Bearing Run-to-Failure Dataset
- **Publishing Institution**: Center for Intelligent Maintenance Systems (IMS), University of Cincinnati in collaboration with NASA Ames Research Center Prognostics Center of Excellence (PCoE).
- **Public Repository URL**: [NASA PCoE Dataset Repository](https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/)
- **Academic Citation**:
  > J. Lee, H. Qiu, G. Yu, J. Lin, and Rexnord Technical Services (2007). *Bearing Data Set*, IMS, University of Cincinnati. NASA Ames Prognostics Data Repository.
- **License / Open Science Status**: Open research data / NASA Public Access data.

---

## 2. Experimental Setup & Physical Parameters

The NASA IMS test bench consisted of four Rexnord ZA-2115 double-row bearings mounted on a single driven shaft rotating at a constant $2,000$ RPM driven by an AC motor. A radial load of $6,000$ lbs was applied to the shaft and bearing assembly via a spring mechanism.

- **Bearings**: Rexnord ZA-2115 double-row spherical roller bearings (16 rollers per row, pitch diameter $71.5$ mm, roller diameter $8.4$ mm).
- **Sensors**: PCB 353B33 high-frequency quartz shear ICP accelerometers installed on bearing housings.
- **Sampling Frequency**: $20$ kHz.
- **Run Duration**: Continuous run-to-failure over several weeks ($> 160$ hours per test), ending in mechanical spalling and raceway degradation.

---

## 3. Subset Used in AuRAG

Rather than duplicating hundreds of gigabytes of raw binary accelerometer dumps into git, AuRAG integrates a lightweight, verified, preprocessed representative progression fixture located at:
[`telemetry/fixtures/nasa_ims_bearing_sample.json`](file:///c:/Users/nisha/OneDrive/Documents/Downloads/AuRAG/telemetry/fixtures/nasa_ims_bearing_sample.json).

The representative fixture captures five characteristic phases of the run-to-failure lifecycle from **Test 2 (Bearing 1)**:
1. `NASA-IMS-T2-REC-001` (0.0h): Nominal baseline ($1.85$ mm/s RMS, $52.4$°C).
2. `NASA-IMS-T2-REC-020` (63.6h): Normal continuous operation ($2.28$ mm/s RMS, $55.1$°C).
3. `NASA-IMS-T2-REC-038` (128.1h): Nascent raceway micro-pitting ($3.62$ mm/s RMS, $64.8$°C).
4. `NASA-IMS-T2-REC-042` (147.6h): **Zone C Excursion** ($5.42$ mm/s RMS, $84.6$°C, outer race BPFO harmonic peak at $236.4$ Hz). This is the key record that triggers autonomous AuRAG RFQ and micro-settlement.
5. `NASA-IMS-T2-REC-045` (163.8h): Catastrophic terminal degradation ($11.75$ mm/s RMS, $102.3$°C).

---

## 4. Telemetry Field Mapping & Normalization

The adapter converts raw NASA IMS records into AuRAG's standard telemetry schema:

| NASA IMS Raw Metric | AuRAG Normalized Field | Engineering Unit | Conversion & Interpretation |
| :--- | :--- | :--- | :--- |
| Accelerometer Channel 1 | `vibration_mm_s` / `vibration_mms` | mm/s RMS | Integrated velocity RMS according to ISO 10816-3 |
| Thermocouple | `bearing_temp_c` / `temperature_c` | °C | Bearing housing outer temperature |
| Spectral Peak | `frequency_peak_hz` | Hz | Dominant FFT frequency harmonic (BPFO outer race signature) |
| ISO Zone | `iso_zone` | Enum | Zone A/B (Good), Zone C (Warning), Zone D (Critical) |
| Asset Label | `equipment_id` / `canonical_tag` | Tag | **`REPLAY-ASSET-01`** (clearly distinguishes from synthetic `P-101A`) |

---

## 5. Provenance Metadata Contract

Every telemetry event originating from the public dataset adapter embeds truthful metadata:

```json
{
  "data_source_type": "PUBLIC_DATASET",
  "dataset_name": "NASA IMS Bearing Run-to-Failure Dataset",
  "dataset_record_id": "NASA-IMS-T2-REC-042",
  "source_reference": "https://www.nasa.gov/intelligent-systems-division/discovery-and-systems-health/pcoe/pcoe-data-set-repository/",
  "replay_mode": true,
  "equipment_id": "REPLAY-ASSET-01",
  "disclosure": "Public industrial condition-monitoring data replay (preprocessed representative progression fixture)"
}
```

---

## 6. Honest Technical Disclosures

1. **Not Live SCADA**: This data was collected by NASA/University of Cincinnati in a controlled test rig in 2004. It is strictly replayed for deterministic algorithm verification and public credibility.
2. **Asset Separation**: The replayed asset is named **`REPLAY-ASSET-01`**. AuRAG never falsely claims that `P-101A` is a NASA bearing.
3. **Reproducibility**: Any reviewer can inspect `telemetry/fixtures/nasa_ims_bearing_sample.json` and verify the mathematical conversion against the published NASA IMS dataset publications.
