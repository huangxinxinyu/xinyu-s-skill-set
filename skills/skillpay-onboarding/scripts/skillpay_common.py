"""Shared CLI supervision, heartbeats, and Skill installation verification."""

from __future__ import annotations

from datetime import datetime
import json
import logging
import os
import re
import stat
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

SKILLPAY_TIMEOUT_SECONDS = 180.0
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 3.0
INSTALL_RECEIPT_FILE = ".alipay-skill-install.json"
MAX_PUBLIC_INSTALL_BYTES = 64 * 1024
CONTROL_HEADERS = {
    "authorization",
    "payment-proof",
    "host",
    "content-length",
    "externalid",
    "sign",
    "timestamp",
}

LOGGER = logging.getLogger("skillpay.poll")
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False
LOGGER.addHandler(logging.NullHandler())
DEBUG_LOGGING_ENABLED = False


class Keepalive:
    """Emit safe progress records to stderr while this foreground run is active."""

    def __init__(self, interval: float, stream: Any = None) -> None:
        self.interval = interval
        self.stream = stream if stream is not None else sys.stderr
        self.started_at = time.monotonic()
        self.next_emit_at = self.started_at + interval
        self.phase = "PAYMENT_POLLING"
        self.attempt = 0

    def update(self, phase: str, attempt: int | None = None) -> None:
        self.phase = phase
        if attempt is not None:
            self.attempt = attempt

    def seconds_until_next(self) -> float:
        return max(0.01, self.next_emit_at - time.monotonic())

    def maybe_emit(self) -> bool:
        now = time.monotonic()
        if now < self.next_emit_at:
            return False
        payload: dict[str, Any] = {
            "event": "heartbeat",
            "terminal": False,
            "phase": self.phase,
            "elapsedSeconds": int(max(0.0, now - self.started_at)),
        }
        if self.attempt > 0:
            payload["attempt"] = self.attempt
        print(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            file=self.stream,
            flush=True,
        )
        while self.next_emit_at <= now:
            self.next_emit_at += self.interval
        return True


def keepalive_sleep(seconds: float, keepalive: Keepalive) -> None:
    """Sleep without leaving the foreground process silent past one heartbeat."""
    deadline = time.monotonic() + seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return
        time.sleep(min(remaining, keepalive.seconds_until_next()))
        keepalive.maybe_emit()


def log_method_entry(method: str, **details: Any) -> None:
    if details:
        detail_text = " ".join(f"{key}={value}" for key, value in details.items())
        LOGGER.info("method_entry method=%s %s", method, detail_text)
    else:
        LOGGER.info("method_entry method=%s", method)


def configure_logging(log_file: str | None = None, *, enabled: bool = False) -> str:
    global DEBUG_LOGGING_ENABLED
    DEBUG_LOGGING_ENABLED = enabled
    cache = os.environ.get("XDG_CACHE_HOME")
    root = Path(cache) if cache and Path(cache).is_absolute() else Path.home() / ".cache"
    log_path = Path(log_file) if log_file else root / "skillpay-onboarding" / "poll" / (
        f"skillpay-debug-{datetime.now().strftime('%H%M%S')}.log"
    )
    for handler in LOGGER.handlers[:]:
        LOGGER.removeHandler(handler)
        handler.close()

    if not DEBUG_LOGGING_ENABLED:
        LOGGER.addHandler(logging.NullHandler())
        return str(log_path)

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    LOGGER.addHandler(stderr_handler)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        if file_handler.stream is not None:
            file_handler.stream.reconfigure(line_buffering=True)
        file_handler.setFormatter(formatter)
        LOGGER.addHandler(file_handler)
    except OSError as exc:
        LOGGER.error("log_file_unavailable path=%s error=%s", log_path, exc)
    LOGGER.info(
        "method_entry method=configure_logging log_file=%s debug_logging_enabled=%s",
        log_path,
        DEBUG_LOGGING_ENABLED,
    )
    return str(log_path)


def redact_log_text(text: str) -> str:
    log_method_entry("redact_log_text", text_length=len(text))
    if DEBUG_LOGGING_ENABLED:
        return text
    sensitive_fields = r"authorization|payment-proof|paymentProof|payment_proof|requestToken|accessToken|token|sign|signature|md5Val|externalId"
    redacted = re.sub(
        rf'("?(?:{sensitive_fields})"?\s*:\s*)"(?:\\.|[^"\\])*"',
        r'\1"<redacted>"',
        text,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(
        rf"((?:{sensitive_fields})\s*[=:]\s*)(?:(?:Bearer|Basic)\s+)?[^,\s\]\}}]+",
        r"\1<redacted>",
        redacted,
        flags=re.IGNORECASE,
    )
    return re.sub(
        r"(Bearer\s+|Basic\s+)([^\s,\]\}]+)",
        r"\1<redacted>",
        redacted,
        flags=re.IGNORECASE,
    )


def log_child_output(output: str) -> None:
    log_method_entry("log_child_output", output_length=len(output))
    for line in output.splitlines() or ([output] if output else []):
        LOGGER.info("child_output %s", line)


def log_alipay_bot_call(command: list[str]) -> None:
    log_method_entry("log_alipay_bot_call", argument_count=len(command))
    safe_command = [redact_log_text(argument) for argument in command]
    serialized_command = json.dumps(safe_command, ensure_ascii=False, separators=(",", ":"))
    LOGGER.info("alipay_bot_call args=%s", serialized_command)
    LOGGER.info("alipay_bot_input_begin argument_count=%d", len(safe_command))
    for index, argument in enumerate(safe_command):
        LOGGER.info("alipay_bot_input_arg index=%d value=%s", index, argument)
    LOGGER.info("alipay_bot_input_args=%s", serialized_command)
    LOGGER.info("alipay_bot_input_end")


def log_alipay_bot_return(returncode: int, output: str) -> None:
    log_method_entry("log_alipay_bot_return", returncode=returncode, output_length=len(output))
    safe_output = redact_log_text(output)
    output_lines = safe_output.splitlines() or ([safe_output] if safe_output else [])
    LOGGER.info(
        "alipay_bot_return returncode=%d output_length=%d line_count=%d",
        returncode,
        len(output),
        len(output_lines),
    )
    LOGGER.info(
        "alipay_bot_output_begin returncode=%d output_length=%d line_count=%d",
        returncode,
        len(output),
        len(output_lines),
    )
    for index, line in enumerate(output_lines):
        LOGGER.info("alipay_bot_output_line index=%d value=%s", index, line)
    LOGGER.info("alipay_bot_output_end returncode=%d", returncode)


def parse_json_payload(text: str) -> Any:
    """Extract the last JSON value from CLI output that may contain log lines."""
    log_method_entry("parse_json_payload", text_length=len(text))
    decoder = json.JSONDecoder()
    candidates: list[Any] = []
    for match in re.finditer(r"[\[{]", text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        candidates.append(value)
    return max(candidates, key=lambda value: len(json.dumps(value, ensure_ascii=False))) if candidates else None


def regular_file(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False


def real_directory(path: Path) -> bool:
    try:
        return stat.S_ISDIR(path.lstat().st_mode)
    except OSError:
        return False


def frontmatter_value(text: str, key: str) -> str | None:
    match = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|\Z)", text, flags=re.DOTALL)
    if not match:
        return None
    field = re.search(
        rf"(?m)^{re.escape(key)}\s*:\s*([^\n]+?)\s*$",
        match.group(1),
    )
    if not field:
        return None
    value = field.group(1).strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return None
        value = decoded.strip() if isinstance(decoded, str) else ""
    elif value.startswith("'") and value.endswith("'"):
        value = value[1:-1].replace("''", "'").strip()
    else:
        comment = re.search(r"\s+#", value)
        if comment:
            value = value[:comment.start()].strip()
    return value or None


def validate_installed_artifacts(
    result: dict[str, Any], skills_root: str
) -> tuple[dict[str, Any] | None, str | None]:
    """Verify the installed tree and return only safe customer-facing metadata."""
    raw_install_path = result.get("installPath")
    if not isinstance(raw_install_path, str) or not raw_install_path.strip():
        return None, "INSTALL_PATH_MISSING"
    install_path = Path(raw_install_path).expanduser()
    root_path = Path(skills_root).expanduser()
    if not install_path.is_absolute() or not root_path.is_absolute():
        return None, "INSTALL_PATH_INVALID"
    try:
        root = root_path.resolve(strict=True)
        installed = install_path.resolve(strict=True)
    except OSError:
        return None, "INSTALL_PATH_NOT_FOUND"
    if not real_directory(root) or not real_directory(install_path):
        return None, "INSTALL_PATH_INVALID"
    if installed.parent != root:
        return None, "INSTALL_PATH_OUTSIDE_SKILLS_ROOT"

    manifest = install_path / "SKILL.md"
    if not regular_file(manifest):
        return None, "SKILL_MANIFEST_MISSING_AFTER_INSTALL"
    try:
        manifest_text = manifest.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None, "SKILL_MANIFEST_INVALID_AFTER_INSTALL"
    manifest_name = frontmatter_value(manifest_text, "name")
    cli_name = result.get("skillName")
    if not manifest_name or manifest_name != install_path.name:
        return None, "SKILL_NAME_MISMATCH_AFTER_INSTALL"
    if not isinstance(cli_name, str) or not cli_name.strip():
        return None, "SKILL_NAME_MISSING_AFTER_INSTALL"
    if cli_name.strip() != manifest_name:
        return None, "SKILL_NAME_MISMATCH_AFTER_INSTALL"

    receipt_path = install_path / INSTALL_RECEIPT_FILE
    if not regular_file(receipt_path):
        return None, "INSTALL_RECEIPT_MISSING"
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "INSTALL_RECEIPT_INVALID"
    if not isinstance(receipt, dict):
        return None, "INSTALL_RECEIPT_INVALID"
    archive_hash = receipt.get("archiveSha256")
    installed_at = receipt.get("installedAt")
    if not isinstance(archive_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", archive_hash):
        return None, "INSTALL_RECEIPT_INVALID"
    if not isinstance(installed_at, str) or not installed_at.strip():
        return None, "INSTALL_RECEIPT_INVALID"

    response_backup = result.get("backupPath")
    receipt_backup = receipt.get("backupPath")
    if response_backup is None:
        response_backup = ""
    if receipt_backup is None:
        receipt_backup = ""
    if not isinstance(response_backup, str) or not isinstance(receipt_backup, str):
        return None, "BACKUP_PATH_INVALID"
    if response_backup.strip() != receipt_backup.strip():
        return None, "BACKUP_PATH_MISMATCH"
    if response_backup.strip():
        backup_path = Path(response_backup.strip()).expanduser()
        if not backup_path.is_absolute():
            return None, "BACKUP_PATH_INVALID"
        try:
            backup = backup_path.resolve(strict=True)
        except OSError:
            return None, "BACKUP_PATH_INVALID"
        if backup.parent != root or not real_directory(backup_path):
            return None, "BACKUP_PATH_INVALID"

    file_count = 0
    directory_count = 0

    def raise_walk_error(error: OSError) -> None:
        raise error

    try:
        for current_root, directories, files in os.walk(
            install_path, followlinks=False, onerror=raise_walk_error
        ):
            current = Path(current_root)
            for name in directories:
                path = current / name
                if path.is_symlink():
                    return None, "INSTALL_TREE_INVALID"
                directory_count += 1
            for name in files:
                path = current / name
                if not regular_file(path):
                    return None, "INSTALL_TREE_INVALID"
                file_count += 1
    except OSError:
        return None, "INSTALL_TREE_INVALID"

    evidence: dict[str, Any] = {
        "verificationCompleted": True,
        "manifestName": manifest_name,
        "installedFileCount": file_count,
        "installedDirectoryCount": directory_count,
        "installReceiptValid": True,
        "installPathUnderSkillsRoot": True,
    }
    description = frontmatter_value(manifest_text, "description")
    if description:
        evidence["skillDescription"] = description
    public_install = install_path / "public-files" / "INSTALL.md"
    if regular_file(public_install):
        try:
            if public_install.stat().st_size <= MAX_PUBLIC_INSTALL_BYTES:
                instructions = public_install.read_text(encoding="utf-8").strip()
                if instructions:
                    evidence["publicInstallInstructions"] = instructions
        except (OSError, UnicodeError):
            pass
    return evidence, None


def normalize_headers(value: Any) -> dict[Any, Any] | None:
    """Accept the header shapes emitted by different Codex state serializers.

    The canonical state shape is an object, but empty headers may be serialized
    as null and header collections may be serialized as ``["Name: value"]`` or
    ``[["Name", "value"]]``.  Normalize those representations without changing
    the saved state; malformed entries remain invalid.
    """
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        entries = [value]
    elif isinstance(value, list):
        entries = value
    else:
        return None

    normalized: dict[Any, Any] = {}
    for entry in entries:
        if isinstance(entry, dict):
            if set(entry) != {"name", "value"}:
                return None
            key, item = entry["name"], entry["value"]
        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
            key, item = entry
        elif isinstance(entry, str):
            key, separator, item = entry.partition(":")
            if not separator:
                return None
            key, item = key.strip(), item.strip()
        else:
            return None
        if not isinstance(key, str) or not key.strip() or item is None:
            return None
        normalized[key.strip()] = item
    return normalized


def run_alipay_bot(
    command: list[str], timeout: float, keepalive: Keepalive | None = None,
    *, stderr_parts: list[str] | None = None,
) -> tuple[int, str]:
    """Supervise one CLI child; optionally capture stderr separately from stdout."""
    log_alipay_bot_call(command)
    child_started_at = time.monotonic()
    LOGGER.info("alipay_bot_execution_started timeout_seconds=%.3f", timeout)
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if stderr_parts is not None else subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        LOGGER.info(
            "alipay_bot_process_started pid=%d timeout_seconds=%.3f",
            process.pid,
            timeout,
        )
        output_parts: list[str] = []

        def forward_output(stream: Any, parts: list[str]) -> None:
            if stream is None:
                return
            try:
                for line in stream:
                    parts.append(line)
                    log_child_output(redact_log_text(line))
            except (OSError, ValueError) as exc:
                LOGGER.error("child_output_read_failed error=%s", exc)
            finally:
                stream.close()

        reader = threading.Thread(target=forward_output, args=(process.stdout, output_parts),
                                  name="skillpay-child-output", daemon=True)
        reader.start()
        stderr_reader = None
        if stderr_parts is not None:
            stderr_reader = threading.Thread(target=forward_output, args=(process.stderr, stderr_parts),
                                             name="skillpay-child-stderr", daemon=True)
            stderr_reader.start()
        deadline = child_started_at + timeout
        while process.poll() is None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            wait_for = remaining
            if keepalive is not None:
                wait_for = min(wait_for, keepalive.seconds_until_next())
            try:
                process.wait(timeout=max(0.01, wait_for))
            except subprocess.TimeoutExpired:
                pass
            if keepalive is not None:
                keepalive.maybe_emit()
        if process.poll() is None:
            elapsed = time.monotonic() - child_started_at
            LOGGER.warning(
                "alipay_bot_call_timeout pid=%d timeout_seconds=%.3f elapsed_seconds=%.3f output_length=%d",
                process.pid,
                timeout,
                elapsed,
                sum(len(part) for part in output_parts),
            )
            LOGGER.warning("alipay_bot_process_kill_requested pid=%d", process.pid)
            process.kill()
            kill_wait_started_at = time.monotonic()
            killed_returncode = process.wait()
            LOGGER.info(
                "alipay_bot_process_killed pid=%d returncode=%d wait_seconds=%.3f",
                process.pid,
                killed_returncode,
                time.monotonic() - kill_wait_started_at,
            )
            reader.join(timeout=1.0)
            if stderr_reader is not None:
                stderr_reader.join(timeout=1.0)
            if reader.is_alive() and process.stdout is not None:
                process.stdout.close()
                reader.join(timeout=1.0)
            LOGGER.info(
                "alipay_bot_output_reader_finished pid=%d reader_alive=%s output_length=%d",
                process.pid,
                reader.is_alive(),
                sum(len(part) for part in output_parts),
            )
            output = "".join(output_parts)
            log_alipay_bot_return(124, output)
            return 124, output
        returncode = process.wait()
        reader.join(timeout=1.0)
        if stderr_reader is not None:
            stderr_reader.join(timeout=1.0)
        output = "".join(output_parts)
        LOGGER.info(
            "alipay_bot_process_exited pid=%d returncode=%d elapsed_seconds=%.3f output_length=%d",
            process.pid,
            returncode,
            time.monotonic() - child_started_at,
            len(output),
        )
        log_alipay_bot_return(returncode, output)
        return returncode, output
    except FileNotFoundError:
        LOGGER.error(
            "alipay_bot_process_start_failed reason=command_not_found elapsed_seconds=%.3f",
            time.monotonic() - child_started_at,
        )
        LOGGER.error("child_process_unavailable command=alipay-bot")
        output = "ALIPAY_BOT_UNAVAILABLE"
        log_alipay_bot_return(127, output)
        return 127, output
    except OSError as exc:
        LOGGER.error(
            "alipay_bot_process_start_failed reason=os_error elapsed_seconds=%.3f error=%s",
            time.monotonic() - child_started_at,
            exc,
        )
        LOGGER.error("child_process_os_error error=%s", exc)
        output = str(exc)
        log_alipay_bot_return(125, output)
        return 125, output


def install_with_fulfillment_proof(
    context: dict[str, Any],
    fulfillment_proof: str,
    timeout: float,
    keepalive: Keepalive | None = None,
) -> tuple[int, str]:
    """Run the proof-based skillpay entry point using literal subprocess args."""
    command = [
        "alipay-bot",
        "skillpay",
        "--fulfillment-proof",
        fulfillment_proof,
        "--skills-root",
        context["skills_root"],
    ]
    if context.get("external_order_id"):
        command.extend(["--external-order-id", context["external_order_id"]])
    if context.get("target_agent"):
        command.extend(["--target-agent", context["target_agent"]])
    return run_alipay_bot(command, timeout, keepalive)


def verified_install_result(
    returncode: int, output: str, skills_root: str, attempts: int
) -> tuple[int, dict[str, Any]]:
    """Validate and reduce skillpay output to the safe fields needed by the Agent."""
    transport_errors = {
        124: "SKILLPAY_TIMEOUT",
        125: "SKILLPAY_START_FAILED",
        127: "ALIPAY_BOT_NOT_FOUND",
    }
    if returncode in transport_errors:
        return 20, {
            "terminal": True,
            "stage": "FAILED",
            "status": "failed",
            "errorCode": transport_errors[returncode],
            "failedStage": "SKILLPAY",
            "attempts": attempts,
        }
    parsed = parse_json_payload(output)
    if not isinstance(parsed, dict):
        return 20, {
            "terminal": True,
            "stage": "FAILED",
            "status": "failed",
            "errorCode": "SKILLPAY_RESPONSE_INVALID",
            "failedStage": "SKILLPAY",
            "attempts": attempts,
        }

    stage = str(parsed.get("stage", ""))
    if returncode == 0:
        install_path = parsed.get("installPath")
        if (
            stage != "VERIFIED"
            or parsed.get("status") != "completed"
            or parsed.get("installationCompleted") is not True
        ):
            return 20, {
                "terminal": True,
                "stage": "FAILED",
                "status": "failed",
                "errorCode": "SKILLPAY_VERIFICATION_INCOMPLETE",
                "failedStage": "SKILLPAY",
                "attempts": attempts,
            }
        if not isinstance(install_path, str) or not install_path.strip():
            return 20, {
                "terminal": True,
                "stage": "FAILED",
                "status": "failed",
                "errorCode": "INSTALL_PATH_MISSING",
                "failedStage": "SKILLPAY",
                "attempts": attempts,
            }
        verification, verification_error = validate_installed_artifacts(parsed, skills_root)
        if verification_error or verification is None:
            return 20, {
                "terminal": True,
                "stage": "FAILED",
                "status": "failed",
                "errorCode": verification_error or "INSTALL_VERIFY_FAILED",
                "failedStage": "INSTALL_VERIFY",
                "attempts": attempts,
            }
        safe_result = {
            key: parsed[key]
            for key in (
                "stage",
                "status",
                "skillName",
                "installPath",
                "backupPath",
                "installationCompleted",
            )
            if key in parsed
        }
        safe_result["terminal"] = True
        safe_result["attempts"] = attempts
        safe_result.update(verification)
        return 0, safe_result

    error_code = parsed.get("errorCode")
    result = {
        "terminal": True,
        "stage": stage or ("SKILLPAY_PENDING" if returncode == 10 else "FAILED"),
        "status": parsed.get("status", "pending" if returncode == 10 else "failed"),
        "errorCode": error_code or ("SKILLPAY_PENDING" if returncode == 10 else "SKILLPAY_FAILED"),
        "failedStage": parsed.get("failedStage", "SKILLPAY"),
        "attempts": attempts,
    }
    return (10 if returncode == 10 else 20), result


def normalized_skills_root(value: str) -> str | None:
    path = Path(value).expanduser()
    if not path.is_absolute():
        return None
    try:
        resolved = path.resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if resolved == Path(resolved.anchor):
        return None
    return str(resolved)
