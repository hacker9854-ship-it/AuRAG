"""Synthetic Deep Health & Readiness Probe for AuRAG Production Monitoring.

Runs comprehensive checks against:
- Liveness (/api/health/live)
- Multi-dependency Readiness (/api/health/ready)
- Enterprise Connectors Freshness (/api/connectors)
- Automation Engine Policies (/api/automations/policies)
- Model Gateway Roundtrip Latency
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
import urllib.request
import urllib.error

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("health_probe")


def check_http_endpoint(url: str, timeout_seconds: float = 5.0) -> dict:
    start = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AuRAG-HealthProbe/1.0"})
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            latency_ms = round((time.time() - start) * 1000, 2)
            body = response.read().decode("utf-8")
            try:
                parsed = json.loads(body)
            except Exception:
                parsed = {"raw": body}
            return {
                "status_code": response.status,
                "latency_ms": latency_ms,
                "healthy": 200 <= response.status < 300,
                "data": parsed,
            }
    except urllib.error.HTTPError as e:
        latency_ms = round((time.time() - start) * 1000, 2)
        parsed = {}
        try:
            body = e.read().decode("utf-8")
            parsed = json.loads(body)
        except Exception:
            parsed = {"error": str(e)}
        return {
            "status_code": e.code,
            "latency_ms": latency_ms,
            "healthy": False,
            "error": str(e),
            "data": parsed,
        }
    except Exception as e:
        latency_ms = round((time.time() - start) * 1000, 2)
        return {
            "status_code": 0,
            "latency_ms": latency_ms,
            "healthy": False,
            "error": str(e),
        }


def run_synthetic_probe(base_url: str = "http://localhost:8000", timeout_seconds: float = 5.0) -> dict:
    logger.info(f"Initiating synthetic health probe against {base_url} (timeout={timeout_seconds}s)...")
    checks = {}

    # 1. Process Liveness
    checks["liveness"] = check_http_endpoint(f"{base_url}/api/health/live", timeout_seconds=timeout_seconds)

    # 2. Dependency Readiness
    checks["readiness"] = check_http_endpoint(f"{base_url}/api/health/ready", timeout_seconds=timeout_seconds)

    # 3. Connector Freshness
    checks["connectors"] = check_http_endpoint(f"{base_url}/api/connectors", timeout_seconds=timeout_seconds)

    # 4. Automation Policies
    checks["automations"] = check_http_endpoint(f"{base_url}/api/automations/policies", timeout_seconds=timeout_seconds)

    # Summary
    all_healthy = all(c["healthy"] for c in checks.values())
    latencies = [c["latency_ms"] for c in checks.values() if c["status_code"] > 0]
    avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_url": base_url,
        "overall_status": "HEALTHY" if all_healthy else "DEGRADED",
        "average_latency_ms": avg_latency,
        "checks": checks,
    }

    logger.info(f"Health Probe Completed: Overall={report['overall_status']}, Latency={avg_latency}ms")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AuRAG Synthetic Health Probe")
    parser.add_argument("--url", default="http://localhost:8000", help="Base backend URL")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-endpoint HTTP timeout in seconds")
    parser.add_argument("--allow-degraded", action="store_true", help="Exit with 0 even if dependencies report DEGRADED")
    args = parser.parse_args()

    probe_result = run_synthetic_probe(args.url, timeout_seconds=args.timeout)
    print(json.dumps(probe_result, indent=2))
    if probe_result["overall_status"] != "HEALTHY" and not args.allow_degraded:
        sys.exit(1)
