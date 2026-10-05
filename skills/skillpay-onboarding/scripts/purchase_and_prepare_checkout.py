#!/usr/bin/env python3
"""发起一次 Skill 购买，并在待支付时准备本地收银台二维码。

该脚本是首次购买的单一入口：同步执行 ``alipay-bot curl-proxy``，
分类完整输出；待支付时生成二维码，免支付时直接安装并校验。
stdout 只输出一个终态 JSON，下载凭证仅在进程内传递。

退出码：0 表示安装完成或购买结果可继续处理；10 表示履约待处理；20 表示失败。
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from gen_pay_qrcode import render as render_qrcode
from skillpay_common import (
    DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    SKILLPAY_TIMEOUT_SECONDS,
    Keepalive,
    install_with_fulfillment_proof,
    normalized_skills_root,
    run_alipay_bot,
    verified_install_result,
)


PRODUCT_REF_PATTERN = re.compile(r"^[0-9]+/[A-Za-z0-9_-]+$")
ORDER_PATTERN = re.compile(r"^[0-9]{32}$")
MARKDOWN_LINK_PATTERN = re.compile(r"\]\(\s*<?(https?://[^\s)>]+)>?\s*\)")


def extract_http_body(output: str) -> str:
    """Remove one or more curl ``-i`` header blocks from a response."""
    text = output.replace("\r\n", "\n").strip()
    offset = 0
    while text[offset:].startswith("HTTP/"):
        boundary = text.find("\n\n", offset)
        if boundary < 0:
            return text
        offset = boundary + 2
        if offset >= len(text):
            return ""
    return text[offset:].strip()


def parse_json_response(output: str) -> dict[str, Any] | None:
    body = extract_http_body(output)
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def labeled_value(output: str, label: str) -> str | None:
    match = re.search(
        rf"(?m)^\s*\*\*{re.escape(label)}\*\*[：:]\s*(.*?)\s*$",
        output,
    )
    return match.group(1).strip() if match else None


def parse_pending_payment(output: str) -> dict[str, Any] | None:
    if "支付待确认" not in output or "**支付方式**" not in output:
        return None

    product_name = labeled_value(output, "商品名称")
    raw_amount = labeled_value(output, "订单金额")
    out_shake_no = labeled_value(output, "订单号")
    if not product_name or not raw_amount or not out_shake_no:
        return None

    amount_match = re.fullmatch(
        r"\*\*\s*[¥￥]\s*(\d+(?:\.\d{1,2})?)\s*\*\*",
        raw_amount,
    )
    if not amount_match:
        return None
    if not ORDER_PATTERN.fullmatch(out_shake_no) or out_shake_no[10:14] != "8282":
        return None

    payment_section = output.split("**支付方式**", 1)[1]
    payment_urls: list[str] = []
    for url in MARKDOWN_LINK_PATTERN.findall(payment_section):
        if url not in payment_urls:
            payment_urls.append(url)
    if not payment_urls:
        return None

    return {
        "productName": product_name,
        "amount": amount_match.group(1),
        "outShakeNo": out_shake_no,
        "paymentUrl": payment_urls[0],
        "paymentUrls": payment_urls,
    }


def build_notice_markdown(
    product_name: str,
    amount: str,
    out_shake_no: str,
    payment_url: str,
    qrcode_path: str | None,
) -> str:
    notice = (
        "**支付待确认**\n\n"
        "请扫码完成支付，系统将自动查询支付结果；达到本次查询次数上限后会停止等待。\n\n"
        f"**商品名称**：{product_name}\n"
        f"**订单金额**：**¥{amount}**\n"
        f"**订单号**：{out_shake_no}\n"
        f"**支付方式**：[点击此处支付](<{payment_url}>)，或者复制 "
        f"<{payment_url}> 到浏览器中，打开支付宝扫码支付。"
    )
    if qrcode_path:
        notice += f"\n\n![支付宝支付二维码](<{qrcode_path}>)"
    return notice


def valid_https_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def first_text(record: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def failure(
    error_code: str,
    message: str,
) -> dict[str, Any]:
    return {
        "stage": "FAILED",
        "status": "failed",
        "errorCode": error_code,
        "failedStage": "PURCHASE",
        "errorMessage": message,
    }


def classify_purchase_output(
    output: str,
    stderr: str,
    returncode: int,
    output_dir: Path,
) -> dict[str, Any]:
    if returncode != 0:
        return failure(
            "CURL_PROXY_FAILED",
            f"alipay-bot curl-proxy 退出码为 {returncode}",
        )

    parsed = parse_json_response(output)
    if parsed is not None and parsed.get("success") is True:
        proof = parsed.get("fulfillment_proof")
        if isinstance(proof, str) and proof.strip():
            proof = proof.strip()
            if not valid_https_url(proof):
                return failure(
                    "INVALID_FULFILLMENT_PROOF",
                    "购买响应中的下载凭证不是有效的 HTTPS 地址",
                )
            result: dict[str, Any] = {
                "stage": "PAY_EXEMPT",
                "status": "ready",
                "fulfillment_proof": proof,
                "purchaseOutput": output,
                "purchaseStderr": stderr,
            }
            external_order_id = first_text(
                parsed, "external_order_id", "externalOrderId"
            )
            if external_order_id:
                result["externalOrderId"] = external_order_id
            return result

    pending = parse_pending_payment(output)
    if pending is not None:
        qrcode_path = (
            output_dir.expanduser().resolve()
            / f"pay-qrcode-{pending['outShakeNo'][-6:]}.png"
        )
        result = {
            "stage": "PAYMENT_PENDING",
            "status": "payment_pending",
            **pending,
            "qrcodePath": None,
            "purchaseOutput": output,
            "purchaseStderr": stderr,
        }
        try:
            render_qrcode(
                pending["paymentUrl"],
                qrcode_path,
                "扫码授权付款",
                pending["amount"],
            )
            result["qrcodePath"] = str(qrcode_path)
        except Exception as exc:
            result["warningCode"] = "QRCODE_GENERATION_FAILED"
            result["warningMessage"] = str(exc)
        result["noticeMarkdown"] = build_notice_markdown(
            pending["productName"],
            pending["amount"],
            pending["outShakeNo"],
            pending["paymentUrl"],
            result["qrcodePath"],
        )
        return result

    if parsed is not None and parsed.get("success") is False:
        return failure(
            first_text(parsed, "code", "errorCode", "error_code")
            or "PURCHASE_REJECTED",
            first_text(
                parsed,
                "message",
                "displayMessage",
                "errorMsg",
                "error_message",
            )
            or "购买请求失败",
        )

    if parsed is not None and parsed.get("success") is True:
        return {
            "stage": "DIRECT_RESPONSE",
            "status": "response_received",
            "response": parsed,
            "purchaseOutput": output,
            "purchaseStderr": stderr,
        }

    return failure(
        "PURCHASE_RESPONSE_UNCLASSIFIED",
        "首次购买响应无法分类或缺少必需字段",
    )


def purchase(
    product_ref: str, output_dir: Path, keepalive: Keepalive | None = None,
    timeout: float = SKILLPAY_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    if not PRODUCT_REF_PATTERN.fullmatch(product_ref):
        return failure("INVALID_PRODUCT_REF", "商品标识无效，未发起购买请求")

    resource_url = f"https://agentpay.alipay.com/ai-pay/proxy/{product_ref}"
    command = [
        "alipay-bot",
        "curl-proxy",
        "--",
        "-i",
        "-X",
        "POST",
        resource_url,
        "-H",
        "Content-Type: application/json",
        "-d",
        '{"prompt":"firsttimebuy"}',
    ]
    stderr_parts: list[str] = []
    returncode, output = run_alipay_bot(command, timeout, keepalive, stderr_parts=stderr_parts)
    if returncode == 127:
        return failure(
            "ALIPAY_BOT_NOT_FOUND",
            "请在智能体用以下命令安装支付宝AI付npx -y @alipay/agent-payment@latest install",
        )
    if returncode in {124, 125}:
        return failure(
            "CURL_PROXY_TIMEOUT" if returncode == 124 else "CURL_PROXY_START_FAILED",
            "购买请求未完成，不自动重新购买",
        )

    return classify_purchase_output(
        output,
        "".join(stderr_parts),
        returncode,
        output_dir,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="购买 Skill，准备收银台或直接安装并校验")
    parser.add_argument("--product-ref", required=True, help="merchant_id/product_id")
    parser.add_argument("--output-dir", required=True, help="二维码输出目录")
    parser.add_argument("--skills-root", required=True)
    parser.add_argument("--target-agent")
    parser.add_argument("--heartbeat-interval", type=float, default=DEFAULT_HEARTBEAT_INTERVAL_SECONDS)
    parser.add_argument("--timeout", type=float, default=SKILLPAY_TIMEOUT_SECONDS,
                        help="每次 CLI 调用的超时秒数")
    args = parser.parse_args()

    skills_root = normalized_skills_root(args.skills_root)
    if not skills_root:
        result = failure("SKILLS_ROOT_INVALID", "安装根目录必须为非根目录的绝对路径")
        code = 20
    elif not math.isfinite(args.heartbeat_interval) or args.heartbeat_interval <= 0:
        result = failure("HEARTBEAT_INTERVAL_INVALID", "心跳间隔必须为有限正数")
        code = 20
    elif not math.isfinite(args.timeout) or args.timeout <= 0:
        result = failure("TIMEOUT_INVALID", "超时必须为有限正数")
        code = 20
    else:
        keepalive = Keepalive(args.heartbeat_interval)
        keepalive.update("PURCHASE")
        result = purchase(args.product_ref, Path(args.output_dir), keepalive, args.timeout)
        if result["stage"] == "PAY_EXEMPT":
            keepalive.update("PAY_EXEMPT_INSTALLING")
            context = {
                "skills_root": skills_root,
                "target_agent": args.target_agent,
                "external_order_id": result.get("externalOrderId"),
            }
            install_code, output = install_with_fulfillment_proof(
                context, result["fulfillment_proof"], args.timeout, keepalive
            )
            code, result = verified_install_result(install_code, output, skills_root, 0)
        else:
            code = 20 if result["stage"] == "FAILED" else 0
    result["terminal"] = True
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
