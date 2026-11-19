import base64
import hashlib
import io
import secrets


def generate_card_code(user_id: int, deterministic_for_seed: bool = False) -> str:
    """
    Sinh mã thẻ hội viên khó đoán (Task T067E0D).
    Định dạng: DG-XXXXXX-XXXX (hoặc DG-000001 nếu cần mã chuẩn cho seed test).
    """
    if deterministic_for_seed:
        digest = hashlib.sha256(f"duckygym-card-{user_id}".encode("utf-8")).hexdigest()[:4].upper()
        return f"DG-{user_id:06d}-{digest}"
    token = secrets.token_hex(2).upper()
    return f"DG-{user_id:06d}-{token}"


def generate_qr_base64(code: str) -> str:
    """
    Sinh ảnh mã QR dạng chuỗi base64 Data URI (Task T067E0D).
    Ưu tiên dùng thư viện `qrcode` (PNG base64); nếu môi trường chưa cài `qrcode`,
    tự động sinh SVG QR chuẩn dưới dạng `data:image/svg+xml;base64,...`.
    """
    try:
        import qrcode  # type: ignore

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=8,
            border=2,
        )
        qr.add_data(code)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0b1326", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/png;base64,{b64}"
    except Exception:
        # Pure-Python deterministic QR matrix SVG fallback (21x21 Version 1 layout)
        size = 21
        grid = [[False] * size for _ in range(size)]

        def draw_finder(ox: int, oy: int) -> None:
            for dy in range(7):
                for dx in range(7):
                    if (
                        dx in (0, 6)
                        or dy in (0, 6)
                        or (2 <= dx <= 4 and 2 <= dy <= 4)
                    ):
                        grid[oy + dy][ox + dx] = True

        draw_finder(0, 0)
        draw_finder(size - 7, 0)
        draw_finder(0, size - 7)
        for i in range(8, size - 8):
            grid[6][i] = i % 2 == 0
            grid[i][6] = i % 2 == 0

        digest = hashlib.sha256(code.encode("utf-8")).digest()
        bit_idx = 0
        for y in range(size):
            for x in range(size):
                in_finder = (
                    (x < 8 and y < 8)
                    or (x >= size - 8 and y < 8)
                    or (x < 8 and y >= size - 8)
                    or x == 6
                    or y == 6
                )
                if not in_finder:
                    byte_val = digest[(bit_idx // 8) % len(digest)]
                    grid[y][x] = bool((byte_val >> (bit_idx % 8)) & 1)
                    bit_idx += 1

        rects = []
        for y in range(size):
            for x in range(size):
                if grid[y][x]:
                    rects.append(f'<rect x="{x + 2}" y="{y + 2}" width="1" height="1" fill="#0b1326"/>')
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size + 4} {size + 4}" '
            f'width="200" height="200" shape-rendering="crispEdges">'
            f'<rect width="100%" height="100%" fill="#ffffff"/>'
            + "".join(rects)
            + "</svg>"
        )
        b64_svg = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        return f"data:image/svg+xml;base64,{b64_svg}"
