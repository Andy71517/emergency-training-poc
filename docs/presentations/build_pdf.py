"""Build a styled PDF deck from project-overview-slides.md.

This script intentionally uses only the Python standard library.
It is not a full presentation engine, but it creates a denser, cleaner PDF
that is easy to share without adding another dependency to the POC.
"""

from __future__ import annotations

from pathlib import Path
import re
import textwrap


HERE = Path(__file__).resolve().parent
SLIDES_MD = HERE / "project-overview-slides.md"
OUTPUT_PDF = HERE / "emergency-training-poc-overview.pdf"

PAGE_WIDTH = 792
PAGE_HEIGHT = 612
MARGIN_X = 62
BODY_Y = 468
LINE_HEIGHT = 14.5
MAX_BODY_CHARS = 96
MAX_BODY_LINES = 29
CONTENT_BOTTOM_Y = 82

COLOR_BACKGROUND = (0.985, 0.976, 0.945)
COLOR_HEADER = (0.055, 0.105, 0.165)
COLOR_ACCENT = (0.95, 0.42, 0.16)
COLOR_MUTED_ACCENT = (0.18, 0.39, 0.55)
COLOR_BODY = (0.09, 0.11, 0.13)
COLOR_MUTED = (0.42, 0.45, 0.48)
COLOR_CODE_BG = (0.93, 0.925, 0.90)


def _clean_for_pdf(text: str) -> str:
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2192": "->",
        "\u00a0": " ",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _parse_slides(markdown: str) -> list[tuple[str, list[str]]]:
    sections = [section.strip() for section in markdown.split("\n---\n") if section.strip()]
    slides: list[tuple[str, list[str]]] = []
    for section in sections:
        lines = section.splitlines()
        title = "Untitled"
        body: list[str] = []
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
            else:
                body.append(line.rstrip())
        slides.append((title, body))
    return slides


def _format_body(lines: list[str]) -> list[str]:
    formatted: list[str] = []
    in_code_block = False

    for raw_line in lines:
        line = raw_line.strip()

        if line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if not line:
            formatted.append("")
            continue

        if in_code_block:
            formatted.append("    " + line)
            continue

        if line.startswith("- "):
            wrapped = textwrap.wrap(line[2:], width=MAX_BODY_CHARS - 4)
            if not wrapped:
                formatted.append("  -")
            else:
                formatted.append("  - " + wrapped[0])
                formatted.extend("    " + part for part in wrapped[1:])
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", line)
        if numbered:
            prefix = numbered.group(1) + ". "
            wrapped = textwrap.wrap(numbered.group(2), width=MAX_BODY_CHARS - len(prefix))
            if wrapped:
                formatted.append(prefix + wrapped[0])
                formatted.extend(" " * len(prefix) + part for part in wrapped[1:])
            continue

        formatted.extend(textwrap.wrap(line, width=MAX_BODY_CHARS) or [""])

    return formatted


def _rgb(color: tuple[float, float, float]) -> str:
    return f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f}"


def _rect(
    x: float,
    y: float,
    width: float,
    height: float,
    color: tuple[float, float, float],
) -> str:
    return f"{_rgb(color)} rg\n{x:.1f} {y:.1f} {width:.1f} {height:.1f} re f"


def _text(
    *,
    x: float,
    y: float,
    value: str,
    font: str,
    size: float,
    color: tuple[float, float, float],
) -> list[str]:
    return [
        "BT",
        f"/{font} {size:.1f} Tf",
        f"{_rgb(color)} rg",
        f"{x:.1f} {y:.1f} Td",
        f"({_escape_pdf_text(value)}) Tj",
        "ET",
    ]


def _content_stream(title: str, body: list[str], page_number: int, total_pages: int) -> bytes:
    title = _clean_for_pdf(title)
    lines = [_clean_for_pdf(line) for line in _format_body(body)]
    visible_line_count = sum(1 for line in lines if line)
    dynamic_line_height = LINE_HEIGHT
    if 0 < visible_line_count <= 16:
        available_height = BODY_Y - CONTENT_BOTTOM_Y
        dynamic_line_height = min(24, max(LINE_HEIGHT, available_height / (visible_line_count + 1)))
    body_size = 12.2 if visible_line_count <= 12 else 11.3

    commands: list[str] = [
        _rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, COLOR_BACKGROUND),
        _rect(0, PAGE_HEIGHT - 108, PAGE_WIDTH, 108, COLOR_HEADER),
        _rect(0, PAGE_HEIGHT - 108, 11, 108, COLOR_ACCENT),
        _rect(MARGIN_X, PAGE_HEIGHT - 126, PAGE_WIDTH - (MARGIN_X * 2), 4, COLOR_ACCENT),
        *_text(
            x=MARGIN_X,
            y=PAGE_HEIGHT - 48,
            value=title,
            font="F3",
            size=24,
            color=(1, 1, 1),
        ),
        *_text(
            x=MARGIN_X,
            y=PAGE_HEIGHT - 76,
            value="Emergency Training Simulator POC / backend-first local proof",
            font="F1",
            size=9.5,
            color=(0.78, 0.84, 0.88),
        ),
    ]

    y = BODY_Y
    rendered_lines = 0
    for line in lines:
        if rendered_lines >= MAX_BODY_LINES:
            commands.extend(
                _text(
                    x=MARGIN_X,
                    y=y,
                    value="...",
                    font="F1",
                    size=11,
                    color=COLOR_MUTED,
                )
            )
            break

        if not line:
            y -= 8
            continue

        is_code = line.startswith("    ")
        font = "F2" if is_code else "F1"
        size = 9.5 if is_code else body_size
        color = COLOR_MUTED_ACCENT if is_code else COLOR_BODY
        x = MARGIN_X + (10 if line.startswith("  - ") else 0)

        if is_code:
            commands.append(_rect(MARGIN_X - 6, y - 3, PAGE_WIDTH - (MARGIN_X * 2) + 12, 13, COLOR_CODE_BG))

        commands.extend(_text(x=x, y=y, value=line, font=font, size=size, color=color))
        y -= dynamic_line_height
        rendered_lines += 1

    commands.append(_rect(MARGIN_X, 44, PAGE_WIDTH - (MARGIN_X * 2), 1.2, (0.78, 0.76, 0.70)))
    commands.extend(
        _text(
            x=MARGIN_X,
            y=27,
            value="POC only - not clinical, operational, or production guidance",
            font="F1",
            size=8.5,
            color=COLOR_MUTED,
        )
    )
    commands.extend(
        _text(
            x=PAGE_WIDTH - 124,
            y=27,
            value=f"{page_number}/{total_pages}",
            font="F1",
            size=8.5,
            color=COLOR_MUTED,
        )
    )
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


def _build_pdf(slides: list[tuple[str, list[str]]]) -> bytes:
    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_regular_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_mono_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    font_bold_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")

    page_ids: list[int] = []
    for index, (title, body) in enumerate(slides, start=1):
        stream = _content_stream(title, body, index, len(slides))
        stream_id = add_object(
            b"<< /Length "
            + str(len(stream)).encode("ascii")
            + b" >>\nstream\n"
            + stream
            + b"endstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R "
                f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << "
                f"/F1 {font_regular_id} 0 R "
                f"/F2 {font_mono_id} 0 R "
                f"/F3 {font_bold_id} 0 R "
                f">> >> "
                f"/Contents {stream_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode(
        "ascii"
    )

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj_id, data in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{obj_id} 0 obj\n".encode("ascii"))
        pdf.extend(data)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def main() -> None:
    markdown = SLIDES_MD.read_text(encoding="utf-8")
    slides = _parse_slides(markdown)
    OUTPUT_PDF.write_bytes(_build_pdf(slides))
    print(f"Wrote {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
