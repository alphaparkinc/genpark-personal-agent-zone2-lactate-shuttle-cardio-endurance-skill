# -*- coding: utf-8 -*-
"""MCP Server for Zone 2 Lactate Shuttle & Mitochondrial MCT1/4 Capacity Skill."""
import sys
import json
import logging
from typing import Dict, Any

from .core import Zone2LactateShuttleMitochondrialModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TOOLS_SCHEMA = [
    {
        "name": "estimate_fat_max_pace",
        "description": "Estimate peak fat oxidation pace and blood lactate clearing capacity from threshold tests.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "threshold_pace_min_per_km": {
                    "type": "number"
                },
                "aerobic_base_weekly_km": {
                    "type": "number"
                }
            },
            "required": [
                "threshold_pace_min_per_km"
            ]
        }
    },
    {
        "name": "generate_mct_shuttle_session",
        "description": "Synthesize over-under lactate clearance micro-intervals (Zone 2 baseline with 30s Zone 4 surges).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_minutes": {
                    "type": "integer"
                }
            },
            "required": [
                "session_minutes"
            ]
        }
    }
]

def handle_rpc(line: str) -> str:
    try:
        req = json.loads(line)
        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            res = {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "genpark-personal-agent-zone2-lactate-shuttle-cardio-endurance-skill", "version": "1.0.0"}
            }
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": res})

        elif method == "tools/list":
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS_SCHEMA}})

        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})

            target_func = getattr(Zone2LactateShuttleMitochondrialModel, tool_name, None)
            if not target_func:
                return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {tool_name}"}})

            result = target_func(**args)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                }
            })

        else:
            return json.dumps({"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})

    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "id": req.get("id") if "req" in locals() else None, "error": {"code": -32000, "message": str(e)}})

def run_test():
    init_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    init_res = json.loads(handle_rpc(init_req))
    assert init_res.get("result", {}).get("serverInfo", {}).get("name") == "genpark-personal-agent-zone2-lactate-shuttle-cardio-endurance-skill"

    list_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    list_res = json.loads(handle_rpc(list_req))
    assert len(list_res.get("result", {}).get("tools", [])) == 2
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        if run_test():
            sys.exit(0)
        sys.exit(1)

    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
