#!/usr/bin/env python3
"""Run one direct skillpay flow and validate the installed artifacts in Python."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from typing import Any
from urllib.parse import urlparse

from skillpay_common import (
    normalized_skills_root,
    CONTROL_HEADERS,
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    Keepalive,
    SKILLPAY_TIMEOUT_SECONDS,
    normalize_headers,
    run_alipay_bot,
    verified_install_result,
)


ORDER_PATTERN = re.compile(r"^[0-9]{32}$")


def terminal_failure(error_code: str, failed_stage: str = "INPUT") -> dict[str, Any]:
    return {
        "terminal": True,
        "stage": "FAILED",
        "status": "failed",
        "errorCode": error_code,
        "failedStage": failed_stage,
        "attempts": 0,
    }


def build_command(args: argparse.Namespace) -> tuple[list[str] | None, str | None, str | None]:
    skills_root = normalized_skills_root(args.skills_root)
    if not skills_root:
        return None, None, "SKILLS_ROOT_INVALID"
    command = ["alipay-bot", "skillpay"]
    phase: str
    if args.fulfillment_proof:
        parsed = urlparse(args.fulfillment_proof)
        if parsed.scheme != "https" or not parsed.netloc:
            return None, None, "INVALID_FULFILLMENT_PROOF"
        if args.out_shake_no or args.resource_url or args.method or args.data or args.header:
            return None, None, "INSTALL_MODE_CONFLICT"
        command.extend(["--fulfillment-proof", args.fulfillment_proof])
        if args.external_order_id:
            command.extend(["--external-order-id", args.external_order_id])
        phase = "PAY_EXEMPT_INSTALLING"
    else:
        if args.external_order_id:
            return None, None, "INSTALL_MODE_CONFLICT"
        if (
            not args.out_shake_no
            or not ORDER_PATTERN.fullmatch(args.out_shake_no)
            or args.out_shake_no[10:14] != "8282"
        ):
            return None, None, "OUT_SHAKE_NO_INVALID"
        parsed = urlparse(str(args.resource_url or ""))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None, None, "RESOURCE_URL_INVALID"
        method = (args.method or "POST").upper()
        if method == "GET" and args.data is not None:
            return None, None, "BODY_NOT_ALLOWED"
        headers = normalize_headers(args.header or [])
        if headers is None:
            return None, None, "HEADERS_INVALID"
        command.extend(
            [
                "--out-shake-no",
                args.out_shake_no,
                "--resource-url",
                args.resource_url,
                "--method",
                method,
            ]
        )
        if args.data is not None:
            command.extend(["--data", args.data])
        for key, value in headers.items():
            if str(key).lower() not in CONTROL_HEADERS:
                command.extend(["--header", f"{key}:{value}"])
        phase = "PAYMENT_RESUME_INSTALLING"
    command.extend(["--skills-root", skills_root])
    if args.target_agent:
        command.extend(["--target-agent", args.target_agent])
    return command, phase, None


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fulfill, install, and verify one exempt or resumed Skill"
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--fulfillment-proof")
    mode.add_argument("--out-shake-no")
    parser.add_argument("--external-order-id")
    parser.add_argument("--resource-url")
    parser.add_argument("--method", choices=("GET", "POST"))
    parser.add_argument("--data")
    parser.add_argument("--header", action="append")
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--target-agent")
    parser.add_argument("--heartbeat-interval", type=float, default=DEFAULT_HEARTBEAT_INTERVAL_SECONDS)
    parser.add_argument("--timeout", type=float, default=SKILLPAY_TIMEOUT_SECONDS)
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    if not math.isfinite(args.heartbeat_interval) or args.heartbeat_interval <= 0:
        result = terminal_failure("HEARTBEAT_INTERVAL_INVALID")
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")), flush=True)
        return 20
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        result = terminal_failure("SKILLPAY_TIMEOUT_INVALID")
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")), flush=True)
        return 20
    command, phase, error = build_command(args)
    if error or command is None or phase is None:
        result = terminal_failure(error or "INPUT_INVALID")
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")), flush=True)
        return 20

    keepalive = Keepalive(args.heartbeat_interval)
    keepalive.update(phase)
    returncode, output = run_alipay_bot(command, args.timeout, keepalive)
    result_code, result = verified_install_result(
        returncode, output, normalized_skills_root(args.skills_root) or args.skills_root, 0
    )
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")), flush=True)
    return result_code


if __name__ == "__main__":
    sys.exit(main())
