#!/usr/bin/env python3
"""
A2A Bridge Health Check — validates that all components are running.

Checks three components for each target:
1. A2A Server — is the HTTP service online?
2. Agent Card — is the discovery endpoint returning valid JSON?
3. OpenResponses API — is the backend API accessible?

Usage:
    python -m src.health_check                     # Check local agent
    python -m src.health_check --url http://host:9100  # Check specific URL
    python -m src.health_check --json              # JSON output (for automation)

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

# Bypass system proxy for Tailscale internal IPs
os.environ.pop("http_proxy", None)
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("https_proxy", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ["no_proxy"] = "100.0.0.0/8,localhost,127.0.0.1"

_no_proxy_handler = urllib.request.ProxyHandler({})
_opener = urllib.request.build_opener(_no_proxy_handler)
urllib.request.install_opener(_opener)


def check_url(url: str, timeout: float = 5.0) -> dict:
    """
    Check if a URL is reachable.

    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.

    Returns:
        Dict with 'ok' (bool), 'status', 'elapsed_ms', and optional 'error'.
    """
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.monotonic() - t0
            return {
                "ok": True,
                "status": resp.status,
                "elapsed_ms": round(elapsed * 1000),
            }
    except urllib.error.HTTPError as e:
        elapsed = time.monotonic() - t0
        # 405 Method Not Allowed is OK for POST-only endpoints
        if e.code == 405:
            return {
                "ok": True,
                "status": e.code,
                "elapsed_ms": round(elapsed * 1000),
                "note": "POST-only endpoint (405 is expected for GET)",
            }
        return {
            "ok": False,
            "status": e.code,
            "elapsed_ms": round(elapsed * 1000),
            "error": str(e),
        }
    except Exception as e:
        elapsed = time.monotonic() - t0
        return {
            "ok": False,
            "status": None,
            "elapsed_ms": round(elapsed * 1000),
            "error": str(e),
        }


def check_agent_card(base_url: str, timeout: float = 5.0) -> dict:
    """
    Fetch and validate the Agent Card from a server.

    Args:
        base_url: The base URL of the A2A server.
        timeout: Request timeout in seconds.

    Returns:
        Dict with 'ok', agent metadata, and timing info.
    """
    url = f"{base_url}/.well-known/agent.json"
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.monotonic() - t0
            data = json.loads(resp.read().decode())
            return {
                "ok": True,
                "agent_name": data.get("name", "?"),
                "version": data.get("version", "?"),
                "skills": len(data.get("skills", [])),
                "elapsed_ms": round(elapsed * 1000),
            }
    except Exception as e:
        elapsed = time.monotonic() - t0
        return {
            "ok": False,
            "elapsed_ms": round(elapsed * 1000),
            "error": str(e),
        }


def check_openresponses(api_url: str, timeout: float = 10.0) -> dict:
    """
    Check OpenResponses API with a lightweight echo call.

    Args:
        api_url: The OpenResponses API endpoint URL.
        timeout: Request timeout in seconds.

    Returns:
        Dict with 'ok', status, and timing info.
    """
    t0 = time.monotonic()
    try:
        payload = json.dumps({
            "model": "echo",
            "input": "health_check_ping",
        }).encode()
        req = urllib.request.Request(
            api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.monotonic() - t0
            return {
                "ok": True,
                "status": resp.status,
                "elapsed_ms": round(elapsed * 1000),
            }
    except urllib.error.HTTPError as e:
        elapsed = time.monotonic() - t0
        # 401 means the API is up but auth is needed — still "reachable"
        if e.code == 401:
            return {
                "ok": True,
                "status": 401,
                "elapsed_ms": round(elapsed * 1000),
                "note": "API reachable (auth required)",
            }
        return {
            "ok": False,
            "status": e.code,
            "elapsed_ms": round(elapsed * 1000),
            "error": str(e),
        }
    except Exception as e:
        elapsed = time.monotonic() - t0
        return {
            "ok": False,
            "status": None,
            "elapsed_ms": round(elapsed * 1000),
            "error": str(e),
        }


def run_checks(a2a_url: str, api_url: str) -> dict:
    """
    Run all health checks for a target.

    Args:
        a2a_url: The A2A server base URL.
        api_url: The OpenResponses API URL.

    Returns:
        Structured dict with all check results and overall health status.
    """
    results = {
        "target": a2a_url,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "checks": {},
    }

    results["checks"]["a2a_server"] = check_url(a2a_url)
    results["checks"]["agent_card"] = check_agent_card(a2a_url)
    results["checks"]["openresponses_api"] = check_openresponses(api_url)

    results["healthy"] = all(c["ok"] for c in results["checks"].values())
    return results


def print_results(results: dict, use_json: bool = False):
    """Pretty-print or JSON-dump the health check results."""
    if use_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    icon = "✅" if results["healthy"] else "❌"
    status_text = "HEALTHY" if results["healthy"] else "UNHEALTHY"
    print(f"\n{icon} {results['target']} — {status_text}")
    print(f"   Checked at: {results['timestamp']}")
    print()

    for name, check in results["checks"].items():
        status = "✅" if check["ok"] else "❌"
        label = name.replace("_", " ").title()
        detail = f"{check.get('elapsed_ms', '?')}ms"
        if check.get("note"):
            detail += f" ({check['note']})"
        if check.get("agent_name"):
            detail += (
                f" — {check['agent_name']} v{check.get('version', '?')} "
                f"({check.get('skills', 0)} skills)"
            )
        if check.get("error"):
            detail += f" — {check['error']}"
        print(f"   {status} {label}: {detail}")

    print()


def main():
    """Entry point for the health check CLI."""
    parser = argparse.ArgumentParser(description="A2A Bridge Health Check")
    parser.add_argument(
        "--url", "-u",
        default="http://localhost:9100",
        help="A2A server URL to check (default: http://localhost:9100)",
    )
    parser.add_argument(
        "--api-url", "-a",
        default=None,
        help="OpenResponses API URL (default: derived from --url)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON (for programmatic use)",
    )
    args = parser.parse_args()

    # Derive API URL from A2A URL if not specified
    api_url = args.api_url
    if not api_url:
        from urllib.parse import urlparse
        parsed = urlparse(args.url)
        api_url = f"http://{parsed.hostname}:18789/v1/responses"

    results = run_checks(args.url, api_url)
    print_results(results, use_json=args.json)
    sys.exit(0 if results["healthy"] else 1)


if __name__ == "__main__":
    main()
