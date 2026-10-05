#!/usr/bin/env python3
"""生成支付宝 AI 付的紧凑支付二维码卡片。

用法:
    python3 gen_pay_qrcode.py <payment_url> <output_png> --amount <订单金额>
        [--title 扫码授权付款]

当 payment_url 是 pay.html 唤端页时，二维码编码其 ``schema`` 参数，
与网页本身展示的二维码内容保持一致；普通 http(s) 支付链接则直接编码。

退出码: 0 成功; 1 参数错误; 2 渲染失败（缺依赖、素材等）。
"""

import argparse
import binascii
import re
import struct
import sys
import zlib
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    import qrcode
    from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_M, ERROR_CORRECT_Q
    HAS_PIL = True
except ImportError:
    # qrcode is vendored with this skill; Pillow remains optional for the
    # high-fidelity card renderer. The fallback writes PNG with stdlib only.
    sys.path.insert(0, str(Path(__file__).resolve().parent / "_vendor"))
    try:
        import qrcode
        from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_M, ERROR_CORRECT_Q
        HAS_PIL = False
    except ImportError as exc:  # pragma: no cover
        print(f"二维码编码器不可用: {exc}", file=sys.stderr)
        sys.exit(2)


SCRIPT_DIR = Path(__file__).resolve().parent
ASSET_DIR = SCRIPT_DIR / "assets"
BADGE_ASSET = ASSET_DIR / "asset_8.png"

WHITE = (255, 255, 255, 255)
TEXT_DARK = (51, 51, 51, 255)

REGULAR_FONTS = [
    ("/System/Library/Fonts/PingFang.ttc", 0),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
    ("/System/Library/Fonts/STHeiti Light.ttc", 0),
    ("/System/Library/Fonts/PingFang.ttc", None),
]
MEDIUM_FONTS = [
    ("/System/Library/Fonts/PingFang.ttc", 1),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 1),
    ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
]


def load_font(size, medium=False):
    for path, idx in (MEDIUM_FONTS if medium else REGULAR_FONTS):
        try:
            if idx is None:
                return ImageFont.truetype(path, size)
            return ImageFont.truetype(path, size, index=idx)
        except Exception:
            continue
    return ImageFont.load_default()


def resolve_qr_value(payment_url):
    """复刻唤端页的 schema 解析规则，返回网页实际写入二维码的值。"""
    parsed = urlsplit(payment_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("支付链接无效，需为完整的 http/https 链接")

    schema_values = parse_qs(parsed.query, keep_blank_values=True).get("schema")
    if not schema_values:
        return payment_url

    schema = schema_values[0]
    if schema.startswith(("alipays://", "alipay://")):
        return schema
    if schema.startswith("https://u.alipay.cn"):
        return (
            "alipays://platformapi/startapp?appId=20000067&url="
            + quote(schema, safe="")
        )
    raise ValueError("支付页 schema 无效，无法生成与参考页一致的二维码")


def qr_error_correction(value):
    """与参考页一致：按二维码内容的 UTF-8 字节数选择纠错等级。"""
    size = len(value.encode("utf-8"))
    if size <= 900:
        return ERROR_CORRECT_H
    if size <= 1663:
        return ERROR_CORRECT_Q
    return ERROR_CORRECT_M


def build_qr_layer(value, target):
    """生成无额外静区的二维码，并以最近邻方式缩放至目标尺寸。"""
    qr = qrcode.QRCode(
        error_correction=qr_error_correction(value),
        box_size=8,
        border=0,
    )
    qr.add_data(value)
    qr.make(fit=True)
    layer = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return layer.resize((target, target), Image.Resampling.NEAREST)


def _png_rgba(width, height, pixels):
    """Encode an RGBA pixel buffer without Pillow (portable fallback)."""
    raw = b"".join(b"\0" + bytes(pixels[y * width * 4:(y + 1) * width * 4]) for y in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xffffffff)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def render_without_pillow(value, output, title, amount):
    """Generate a readable QR PNG when Pillow is unavailable."""
    qr = qrcode.QRCode(error_correction=qr_error_correction(value), box_size=1, border=4)
    qr.add_data(value)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    modules = len(matrix)
    scale = max(3, min(8, 520 // modules))
    size = modules * scale
    width, height = size + 48, size + 48
    pixels = bytearray([255, 255, 255, 255] * (width * height))
    for row, line in enumerate(matrix):
        for col, dark in enumerate(line):
            if dark:
                for y in range(row * scale + 24, (row + 1) * scale + 24):
                    start = (y * width + col * scale + 24) * 4
                    pixels[start:start + scale * 4] = b"\x00\x00\x00\xff" * scale
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(_png_rgba(width, height, pixels))


def contain(asset, size):
    """按比例缩放素材并置于透明目标画布中央。"""
    max_w, max_h = size
    copy = asset.copy()
    copy.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
    out = Image.new("RGBA", (max_w, max_h), (0, 0, 0, 0))
    out.alpha_composite(copy, ((max_w - copy.width) // 2, (max_h - copy.height) // 2))
    return out


def normalize_amount(amount):
    """接受 0.01、¥0.01、￥0.01 或 0.01元，返回纯数字金额。"""
    match = re.fullmatch(r"\s*[¥￥]?\s*(\d+(?:\.\d{1,2})?)\s*(?:元)?\s*", amount)
    if not match:
        raise ValueError("订单金额无效，应为 0.01、¥0.01 或 0.01元 等格式")
    return match.group(1)


def render(payment_url, output, title, amount):
    qr_value = resolve_qr_value(payment_url)
    amount = normalize_amount(amount)
    if not HAS_PIL:
        render_without_pillow(qr_value, output, title, amount)
        return qr_value
    if not BADGE_ASSET.is_file():
        raise FileNotFoundError(f"缺少二维码样式素材: {BADGE_ASSET}")

    # 参考图为透明画布上的单张白色支付卡片。
    width, height = 834, 662
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    card_x0, card_y0, card_x1, card_y1 = 48, 58, 786, 603
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (card_x0, card_y0 + 4, card_x1, card_y1 + 8),
        radius=20,
        fill=(20, 36, 48, 46),
    )
    image = Image.alpha_composite(image, shadow.filter(ImageFilter.GaussianBlur(16)))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (card_x0, card_y0, card_x1, card_y1),
        radius=20,
        fill=WHITE,
    )

    draw.text(
        (width / 2, 91),
        title,
        font=load_font(30, medium=True),
        fill=TEXT_DARK,
        anchor="mm",
    )
    draw.text(
        (width / 2, 184),
        f"¥ {amount}",
        font=load_font(64, medium=True),
        fill=TEXT_DARK,
        anchor="mm",
    )

    qr_size = 204
    padding = 31
    card_size = qr_size + padding * 2
    card_x = (width - card_size) // 2
    card_y = 262

    qr_shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(qr_shadow).rounded_rectangle(
        (card_x, card_y + 8, card_x + card_size, card_y + card_size + 10),
        radius=18,
        fill=(148, 156, 173, 52),
    )
    image = Image.alpha_composite(image, qr_shadow.filter(ImageFilter.GaussianBlur(14)))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (card_x, card_y, card_x + card_size, card_y + card_size),
        radius=18,
        fill=WHITE,
    )

    qr_layer = build_qr_layer(qr_value, qr_size)
    qr_x, qr_y = card_x + padding, card_y + padding
    image.paste(qr_layer, (qr_x, qr_y))

    badge = contain(Image.open(BADGE_ASSET).convert("RGBA"), (54, 62))
    image.alpha_composite(
        badge,
        (
            qr_x + (qr_size - badge.width) // 2,
            qr_y + (qr_size - badge.height) // 2,
        ),
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG", optimize=True)
    return qr_value


def main():
    parser = argparse.ArgumentParser(description="生成支付宝 AI 付紧凑支付二维码卡片")
    parser.add_argument("url", help="支付链接（http/https）")
    parser.add_argument("output", help="输出 PNG 路径")
    parser.add_argument("--amount", required=True, help="真实订单金额，如 0.01 或 ¥0.01")
    parser.add_argument("--title", default="扫码授权付款")
    args = parser.parse_args()

    payment_url = args.url.strip().strip("<>")
    try:
        render(payment_url, Path(args.output).expanduser(), args.title, args.amount)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(f"OK {args.output}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover
        print(f"渲染失败: {exc}", file=sys.stderr)
        sys.exit(2)
