#!/usr/bin/env python3
"""Poll one payment and install its Skill without exposing fulfillment proof."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from skillpay_common import (
    CONTROL_HEADERS, DEFAULT_HEARTBEAT_INTERVAL_SECONDS, SKILLPAY_TIMEOUT_SECONDS,
    LOGGER, Keepalive, configure_logging, install_with_fulfillment_proof,
    keepalive_sleep, log_method_entry, normalize_headers, parse_json_payload,
    run_alipay_bot, verified_install_result,
)


INTERVAL_SECONDS = 2.0
QUERY_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_ATTEMPTS = 90
RETRYABLE_EXIT_CODES = {1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15}
PAYMENT_SUCCESS_STATUSES = {"paid", "success", "completed", "fulfilled"}
PAYMENT_FAILURE_STATUSES = {
    "failed",
    "failure",
    "expired",
    "closed",
    "cancelled",
    "canceled",
}
PAYMENT_PENDING_STATUSES = {"init", "open_link_created", "trade_created", "paying", "pending", "waiting"}


def fail(
    code: str,
    detail: str | None = None,
    attempts: int = 0,
    failed_stage: str | None = None,
) -> int:
    log_method_entry("fail", code=code, attempts=attempts, has_detail=bool(detail))
    result: dict[str, Any] = {
        "terminal": True,
        "stage": "FAILED",
        "status": "failed",
        "errorCode": code,
        "attempts": attempts,
    }
    if detail:
        result["detail"] = detail
    if failed_stage:
        result["failedStage"] = failed_stage
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")), flush=True)
    return 20


def is_non_empty(value: Any) -> bool:
    log_method_entry("is_non_empty", value_type=type(value).__name__)
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def find_resource(value: Any) -> bool:
    """Look for a non-empty resource/body field in a JSON response."""
    log_method_entry("find_resource", value_type=type(value).__name__)
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in {
                "resource",
                "resourcebody",
                "resource_body",
                "body",
                "content",
                "data",
                "artifact",
                "fulfillment_proof",
                "resource_response",
                "resourceresponse",
                "fulfillment_response",
                "fulfillmentresponse",
                "download_url",
                "package_url",
            } and is_non_empty(item):
                return True
            if isinstance(item, (dict, list)) and find_resource(item):
                return True
    elif isinstance(value, list):
        return any(find_resource(item) for item in value)
    return False


def extract_fulfillment_proof(value: Any) -> str | None:
    """Extract the current order's HTTPS fulfillment proof from a response."""
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in {"fulfillment_proof", "fulfillmentproof"}:
                if isinstance(item, str):
                    candidate = item.strip()
                    parsed = urlparse(candidate)
                    if parsed.scheme == "https" and parsed.netloc:
                        return candidate
            nested = extract_fulfillment_proof(item)
            if nested:
                return nested
    elif isinstance(value, list):
        for item in value:
            nested = extract_fulfillment_proof(item)
            if nested:
                return nested
    return None


def normalize_java_value(value: str | None) -> str | None:
    log_method_entry("normalize_java_value", has_value=value is not None)
    if value is None:
        return None
    normalized = value.strip().strip('"')
    if not normalized or normalized.lower() in {"null", "<null>", "none"}:
        return None
    return normalized


def parse_java_payment_payload(text: str) -> dict[str, Any] | None:
    """Parse AgentPaymentQueryResponse/AgentOrderDTO Java toString output."""
    log_method_entry("parse_java_payment_payload", text_length=len(text))
    if "AgentPaymentQueryResponse" not in text and "AgentOrderDTO" not in text:
        return None

    def field(pattern: str) -> str | None:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        return normalize_java_value(matches[-1]) if matches else None

    success_value = field(r"\bsuccess\s*=\s*(true|false)\b")
    status = field(r"\bstatus\s*=\s*([A-Za-z_]+)")
    payment_proof = field(r"\bpaymentProof\s*=\s*([^,\]\s]+)")
    fulfillment_proof = field(r"\bfulfillmentProof\s*=\s*([^,\]\s]+)")
    out_shake_no = field(r"\boutShakeNo\s*=\s*([0-9]+)")
    if (
        success_value is None
        and status is None
        and payment_proof is None
        and fulfillment_proof is None
        and out_shake_no is None
    ):
        return None
    return {
        "success": success_value.lower() == "true" if success_value else None,
        "status": status.lower() if status else "",
        "paymentProof": payment_proof,
        "fulfillmentProof": fulfillment_proof,
        "outShakeNo": out_shake_no,
    }


def extract_payment_payload(parsed: Any) -> dict[str, Any] | None:
    log_method_entry("extract_payment_payload", value_type=type(parsed).__name__)
    if not isinstance(parsed, dict):
        return None
    order = parsed.get("agentOrderDTO")
    order = order if isinstance(order, dict) else {}
    status = order.get("status", parsed.get("status", parsed.get("stage", "")))
    proof = order.get("paymentProof", order.get("payment_proof", parsed.get("paymentProof")))
    out_shake_no = order.get("outShakeNo", order.get("out_shake_no", parsed.get("outShakeNo")))
    has_fields = any(key in parsed for key in ("success", "status", "stage", "paymentProof", "agentOrderDTO"))
    if not has_fields:
        return None
    return {
        "success": parsed.get("success") if isinstance(parsed.get("success"), bool) else None,
        "status": str(status).lower() if status is not None else "",
        "paymentProof": proof,
        "outShakeNo": str(out_shake_no) if out_shake_no is not None else None,
    }


def has_resource_result(output: str, parsed: Any) -> bool:
    log_method_entry("has_resource_result", output_length=len(output), parsed_type=type(parsed).__name__)
    if parsed is not None and find_resource(parsed):
        return True
    if re.search(r"hasResourceResponse\s*[:=]\s*true|PAID_WITH_RESOURCE", output, flags=re.IGNORECASE):
        return True
    if re.search(r"(?:resourceResponse|fulfillmentResponse)\s*[:=]\s*(?!<null>|null\b|\{\s*\})\S+", output, flags=re.IGNORECASE):
        return True
    marker = re.search(r"资源响应体\**\s*[：:]\s*(.*)", output)
    if marker and marker.group(1).strip():
        return True
    if marker:
        return any(line.strip() for line in output[marker.end():].splitlines())
    return False


def classify(returncode: int, output: str, expected_order: str | None = None) -> str:
    log_method_entry(
        "classify",
        returncode=returncode,
        output_length=len(output),
        has_expected_order=expected_order is not None,
    )
    text = output.strip()
    lowered = text.lower()
    parsed = parse_json_payload(text)
    java_payment = parse_java_payment_payload(text)
    json_payment = extract_payment_payload(parsed)
    payment = json_payment or java_payment

    failure_terms = (
        "支付失败",
        "付款失败",
        "已取消",
        "已过期",
        "账户不匹配",
        "买家不匹配",
        "业务失败",
        "payment_failed",
        "payment_expired",
        "explicit_failure",
    )
    pending_terms = (
        "支付待确认",
        "仍待支付",
        "待支付",
        "未支付",
        "payment_pending",
        "pending",
        "waiting",
        "状态未知",
        "indeterminate",
        "unknown",
    )
    paid_terms = (
        "已支付",
        "支付成功",
        "payment_success",
        '"paid"',
        '"status":"paid"',
        '"status": "paid"',
        '"stage":"paid"',
        '"stage": "paid"',
    )
    empty_terms = (
        "资源为空",
        "body为空",
        "empty_resource",
        "resource_empty",
    )

    if payment:
        status = payment["status"]
        if payment["success"] is False or status in PAYMENT_FAILURE_STATUSES:
            return "EXPLICIT_FAILURE"
        if status in PAYMENT_PENDING_STATUSES:
            return "PENDING"
        if status in PAYMENT_SUCCESS_STATUSES:
            observed_order = payment.get("outShakeNo")
            if not observed_order or (expected_order and observed_order != expected_order):
                return "ORDER_MISMATCH"
            resource_present = has_resource_result(text, parsed)
            if returncode == 124 and not resource_present:
                return "TRANSIENT_ERROR"
            if not is_non_empty(payment.get("paymentProof")):
                # The default user-mode CLI deliberately redacts paymentProof.
                # A matching order plus a non-empty resourceResponse proves that
                # the CLI already used the credential and completed fulfillment.
                redacted_proof = bool(
                    json_payment
                    and resource_present
                    and isinstance(parsed, dict)
                    and ("resourceResponse" in parsed or parsed.get("agentPayQuery") is True)
                )
                if not redacted_proof:
                    return "UNSAFE_RESULT"
            if not resource_present:
                return "EMPTY_RESOURCE"
            return "PAID_WITH_RESOURCE"

    # User-mode 402-query output omits the internal status/proof fields but
    # includes an explicit success heading, query number, and resource body.
    if (
        expected_order
        and re.search(r"查询支付状态成功", text)
        and re.search(rf"查询单号\**\s*[：:]\s*\**{re.escape(expected_order)}", text)
    ):
        return "PAID_WITH_RESOURCE" if has_resource_result(text, parsed) else "EMPTY_RESOURCE"

    if any(term in lowered for term in failure_terms):
        return "EXPLICIT_FAILURE"
    if returncode == 124:
        return "TRANSIENT_ERROR"
    if any(term in lowered for term in empty_terms):
        return "EMPTY_RESOURCE"
    if any(term in lowered for term in pending_terms):
        return "PENDING"

    paid = any(term in lowered for term in paid_terms)
    if isinstance(parsed, dict):
        status = str(parsed.get("status", parsed.get("stage", ""))).lower()
        paid = paid or status in PAYMENT_SUCCESS_STATUSES
        if parsed.get("paid") is True or parsed.get("paymentStatus") in {"PAID", "paid", "SUCCESS", "success"}:
            paid = True
        if paid and not has_resource_result(text, parsed):
            return "EMPTY_RESOURCE"
    if paid:
        return "PAID_WITH_RESOURCE" if text else "EMPTY_RESOURCE"

    if returncode in RETRYABLE_EXIT_CODES or returncode != 0:
        return "TRANSIENT_ERROR"
    return "UNSAFE_RESULT"


def validate_state(state: Any) -> tuple[dict[str, Any] | None, str | None]:
    log_method_entry("validate_state", value_type=type(state).__name__)
    if not isinstance(state, dict):
        return None, "STATE_INVALID"
    if state.get("payment_owner") != "skillshop":
        return None, "PAYMENT_OWNER_INVALID"
    if state.get("payment_notice_sent") is not True:
        return None, "PAYMENT_NOTICE_REQUIRED"
    order = str(state.get("out_shake_no", ""))
    if not re.fullmatch(r"\d{32}", order) or order[10:14] != "8282":
        return None, "OUT_SHAKE_NO_INVALID"
    resource_url = state.get("resource_url")
    parsed_url = urlparse(str(resource_url))
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return None, "RESOURCE_URL_INVALID"
    method = str(state.get("method", "POST")).upper()
    if method not in {"GET", "POST"}:
        return None, "METHOD_INVALID"
    data = state.get("data")
    if data is not None and not isinstance(data, str):
        return None, "BODY_INVALID"
    if method == "GET" and data is not None:
        return None, "BODY_NOT_ALLOWED"
    headers = state.get("headers", {})
    normalized_headers = normalize_headers(headers)
    if normalized_headers is None:
        return None, "HEADERS_INVALID"
    filtered = {
        str(key): str(value)
        for key, value in normalized_headers.items()
        if str(key).lower() not in CONTROL_HEADERS
    }
    skills_root = state.get("skills_root")
    if not isinstance(skills_root, str) or not skills_root.strip():
        return None, "SKILLS_ROOT_REQUIRED"
    root_path = Path(skills_root).expanduser()
    if not root_path.is_absolute():
        return None, "SKILLS_ROOT_NOT_ABSOLUTE"
    root_path = root_path.resolve()
    if root_path == Path(root_path.anchor):
        return None, "SKILLS_ROOT_INVALID"
    target_agent = state.get("target_agent")
    if target_agent is not None and (
        not isinstance(target_agent, str) or not target_agent.strip()
    ):
        return None, "TARGET_AGENT_INVALID"
    return {
        "out_shake_no": order,
        "resource_url": str(resource_url),
        "method": method,
        "data": data,
        "headers": filtered,
        "skills_root": str(root_path),
        "target_agent": target_agent.strip() if isinstance(target_agent, str) else None,
    }, None


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Poll one payment with a per-run query limit and a 20-second timeout per query.")
    parser.add_argument("--out-shake-no")
    parser.add_argument("--resource-url")
    parser.add_argument("--method", choices=("GET", "POST"))
    parser.add_argument("--data")
    parser.add_argument("--header", action="append")
    parser.add_argument("--payment-notice-sent", action="store_true", default=None)
    parser.add_argument("--skills-root", required=True, help="Fixed absolute Skills installation root")
    parser.add_argument("--target-agent", help="Optional target-agent label forwarded to skillpay")
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS, help="Maximum CLI queries per run, including retries (default: 90)")
    parser.add_argument("--heartbeat-interval", type=float, default=DEFAULT_HEARTBEAT_INTERVAL_SECONDS, help="Seconds between safe stderr keepalive records (default: 3)")
    parser.add_argument("--debug-log", action="store_true", help="Enable local development diagnostics (may contain sensitive output)")
    parser.add_argument("--log-file", help="Diagnostic path; used only with --debug-log")
    return parser.parse_args()


def input_state(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "payment_owner": "skillshop",
        "payment_notice_sent": args.payment_notice_sent is True,
        "out_shake_no": args.out_shake_no,
        "resource_url": args.resource_url,
        "method": args.method or "POST",
        "data": args.data,
        "headers": args.header or [],
        "skills_root": args.skills_root,
        "target_agent": args.target_agent,
    }


def query(
    context: dict[str, Any],
    timeout: float,
    keepalive: Keepalive | None = None,
) -> tuple[int, str]:
    log_method_entry("query", timeout=round(timeout, 3), has_data=context["data"] is not None)
    command = [
        "alipay-bot",
        "402-query-payment-status",
        "--out-shake-no",
        context["out_shake_no"],
        "--resource-url",
        context["resource_url"],
        "--method",
        context["method"],
    ]
    if context["data"] is not None:
        command.extend(["--data", str(context["data"])])
    for key, value in context["headers"].items():
        command.extend(["--header", f"{key}:{value}"])
    return run_alipay_bot(command, timeout, keepalive)


def main() -> int:
    args = parse_arguments()
    if args.max_attempts <= 0:
        return fail("MAX_ATTEMPTS_INVALID")
    if not math.isfinite(args.heartbeat_interval) or args.heartbeat_interval <= 0:
        return fail("HEARTBEAT_INTERVAL_INVALID")
    state = input_state(args)
    context, error = validate_state(state)
    if error or context is None:
        return fail(error or "STATE_INVALID")

    log_path = configure_logging(args.log_file, enabled=args.debug_log)
    log_method_entry("main", log_file=log_path)
    keepalive = Keepalive(args.heartbeat_interval)
    for attempts in range(1, args.max_attempts + 1):
        # Every query, including a retry after a transient failure, consumes
        # one slot. No nested retry loop can exceed the configured limit.
        keepalive.update("PAYMENT_POLLING", attempts)
        keepalive_sleep(INTERVAL_SECONDS, keepalive)
        LOGGER.info("payment_query_started attempt=%d max_attempts=%d", attempts, args.max_attempts)
        keepalive.update("PAYMENT_QUERY", attempts)
        returncode, output = query(context, QUERY_TIMEOUT_SECONDS, keepalive)
        classification = classify(returncode, output, context["out_shake_no"])
        LOGGER.info("payment_query_finished attempt=%d returncode=%d classification=%s",
                    attempts, returncode, classification)
        if classification == "PAID_WITH_RESOURCE":
            parsed_result = parse_json_payload(output)
            if parsed_result is None:
                parsed_result = parse_java_payment_payload(output)
            fulfillment_proof = extract_fulfillment_proof(parsed_result)
            if not fulfillment_proof:
                fulfillment_proof = extract_fulfillment_proof(parse_java_payment_payload(output))
            if not fulfillment_proof:
                LOGGER.warning(
                    "polling_finished error_code=FULFILLMENT_PROOF_MISSING attempts=%d",
                    attempts,
                )
                return fail(
                    "FULFILLMENT_PROOF_MISSING",
                    attempts=attempts,
                    failed_stage="RESOURCE",
                )
            LOGGER.info("skillpay_started attempts=%d", attempts)
            keepalive.update("SKILLPAY_INSTALLING", attempts)
            skillpay_code, skillpay_output = install_with_fulfillment_proof(
                context, fulfillment_proof, SKILLPAY_TIMEOUT_SECONDS, keepalive
            )
            result_code, result = verified_install_result(
                skillpay_code, skillpay_output, context["skills_root"], attempts
            )
            LOGGER.info(
                "polling_finished stage=%s attempts=%d",
                result.get("stage", "FAILED"),
                attempts,
            )
            print(
                json.dumps(result, ensure_ascii=False, separators=(",", ":")),
                flush=True,
            )
            return result_code
        if classification in {"PENDING", "TRANSIENT_ERROR"}:
            LOGGER.info("polling_continue reason=%s attempts=%d", classification, attempts)
            continue
        LOGGER.warning("polling_finished stage=FAILED error_code=%s attempts=%d", classification, attempts)
        return fail(classification, attempts=attempts, failed_stage="PAYMENT_QUERY")

    LOGGER.warning("polling_finished stage=PAYMENT_PENDING error_code=POLL_ATTEMPTS_EXHAUSTED attempts=%d", attempts)
    print(json.dumps({
        "terminal": True,
        "stage": "PAYMENT_PENDING",
        "status": "pending",
        "errorCode": "POLL_ATTEMPTS_EXHAUSTED",
        "attempts": attempts,
    }, ensure_ascii=False, separators=(",", ":")), flush=True)
    return 10


if __name__ == "__main__":
    sys.exit(main())
