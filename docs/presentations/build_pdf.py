"""Build a styled PDF deck from project-overview-slides.md.

This script intentionally uses only the Python standard library.
It is not a full presentation engine, but it creates a clean meeting deck PDF
without adding another dependency to the POC.
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
SLIDES_MD = HERE / "project-overview-slides.md"
OUTPUT_PDF = HERE / "emergency-training-poc-overview.pdf"

PAGE_WIDTH = 792
PAGE_HEIGHT = 612
MARGIN_X = 62
BODY_Y = 468
LINE_HEIGHT = 18
MAX_BODY_CHARS = 78
MAX_BODY_LINES = 20
CONTENT_BOTTOM_Y = 82

COLOR_BACKGROUND = (0.975, 0.988, 1.000)
COLOR_HEADER = (0.02, 0.17, 0.31)
COLOR_AZURE = (0.02, 0.29, 0.52)
COLOR_ACCENT = (0.96, 0.58, 0.12)
COLOR_MUTED_ACCENT = (0.16, 0.36, 0.53)
COLOR_BODY = (0.09, 0.11, 0.13)
COLOR_MUTED = (0.42, 0.45, 0.48)
COLOR_CODE_BG = (0.92, 0.96, 0.98)
COLOR_PANEL = (1.0, 1.0, 1.0)
COLOR_AMBER_SOFT = (1.00, 0.94, 0.82)
COLOR_AZURE_SOFT = (0.89, 0.96, 1.00)


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


def _phase_label(page_number: int, total_pages: int) -> str:
    labels = (
        "PROJECT UPDATE", "FOUNDATION", "ROOM STUDIO", "ASSET WORKFLOW",
        "EVIDENCE", "NEXT CHECKS", "BOUNDARIES", "REVIEW + FEEDBACK",
    )
    return labels[page_number - 1] if 1 <= page_number <= len(labels) else "PROJECT UPDATE"


def _cover_stream(title: str, body: list[str], total_pages: int) -> bytes:
    title = _clean_for_pdf(title)
    lines = [_clean_for_pdf(line.strip()) for line in body if line.strip()]
    subtitle = lines[0] if lines else "Backend-first proof of concept"
    audience = lines[1] if len(lines) > 1 else "Project update for Dr. Melissa Cameron"

    commands: list[str] = [
        _rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, COLOR_BACKGROUND),
        _rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, COLOR_HEADER),
        _rect(0, 0, PAGE_WIDTH, 104, COLOR_AZURE),
        _rect(0, PAGE_HEIGHT - 28, PAGE_WIDTH, 28, COLOR_ACCENT),
        _rect(54, 116, 310, 9, COLOR_ACCENT),
        _rect(PAGE_WIDTH - 218, 88, 140, 140, COLOR_AMBER_SOFT),
        _rect(PAGE_WIDTH - 178, 128, 140, 140, COLOR_AZURE_SOFT),
        _rect(54, PAGE_HEIGHT - 162, 124, 26, COLOR_ACCENT),
        *_text(
            x=69,
            y=PAGE_HEIGHT - 153,
            value="POC UPDATE",
            font="F3",
            size=10,
            color=COLOR_HEADER,
        ),
        *_text(
            x=54,
            y=PAGE_HEIGHT - 238,
            value=title,
            font="F3",
            size=38,
            color=(1, 1, 1),
        ),
        *_text(
            x=54,
            y=PAGE_HEIGHT - 278,
            value=subtitle[:82],
            font="F1",
            size=16,
            color=(0.86, 0.93, 0.98),
        ),
        *_text(
            x=54,
            y=PAGE_HEIGHT - 326,
            value=audience[:82],
            font="F3",
            size=14,
            color=COLOR_AMBER_SOFT,
        ),
        *_text(
            x=54,
            y=PAGE_HEIGHT - 386,
            value="Traceable plans. Reviewable assets. Measured next steps.",
            font="F1",
            size=13,
            color=(0.86, 0.93, 0.98),
        ),
        *_text(
            x=54,
            y=34,
            value="POC only - not clinical, operational, or production guidance",
            font="F1",
            size=8.8,
            color=(0.78, 0.84, 0.88),
        ),
        *_text(
            x=PAGE_WIDTH - 124,
            y=34,
            value=f"1/{total_pages}",
            font="F1",
            size=8.8,
            color=(0.78, 0.84, 0.88),
        ),
    ]
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


def _content_stream(title: str, body: list[str], page_number: int, total_pages: int) -> bytes:
    title = _clean_for_pdf(title)
    if page_number == 1:
        return _cover_stream(title, body, total_pages)

    lines = [_clean_for_pdf(line) for line in _format_body(body)]
    visible_line_count = sum(1 for line in lines if line)
    dynamic_line_height = LINE_HEIGHT
    if 0 < visible_line_count <= 12:
        available_height = BODY_Y - CONTENT_BOTTOM_Y
        dynamic_line_height = min(28, max(LINE_HEIGHT, available_height / (visible_line_count + 1)))
    body_size = 14.2 if visible_line_count <= 10 else 12.8
    phase_label = _phase_label(page_number, total_pages)

    commands: list[str] = [
        _rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, COLOR_BACKGROUND),
        _rect(0, PAGE_HEIGHT - 104, PAGE_WIDTH, 104, COLOR_HEADER),
        _rect(0, PAGE_HEIGHT - 104, PAGE_WIDTH, 7, COLOR_ACCENT),
        _rect(0, 0, 16, PAGE_HEIGHT, COLOR_AZURE_SOFT),
        _rect(MARGIN_X, 70, PAGE_WIDTH - (MARGIN_X * 2), 414, COLOR_PANEL),
        _rect(MARGIN_X, 70, 6, 414, COLOR_ACCENT),
        _rect(PAGE_WIDTH - 174, PAGE_HEIGHT - 88, 112, 22, COLOR_AMBER_SOFT),
        *_text(
            x=MARGIN_X,
            y=PAGE_HEIGHT - 46,
            value=title,
            font="F3",
            size=25,
            color=(1, 1, 1),
        ),
        *_text(
            x=MARGIN_X,
            y=PAGE_HEIGHT - 73,
            value="Meeting deck / FIELDWORK progress / October 28, 2026",
            font="F1",
            size=9.5,
            color=(0.78, 0.84, 0.88),
        ),
        *_text(
            x=PAGE_WIDTH - 163,
            y=PAGE_HEIGHT - 82,
            value=phase_label,
            font="F3",
            size=8.8,
            color=COLOR_HEADER,
        ),
        *_text(
            x=PAGE_WIDTH - 92,
            y=PAGE_HEIGHT - 32,
            value=f"{page_number:02d}",
            font="F3",
            size=20,
            color=COLOR_AMBER_SOFT,
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
        x = MARGIN_X + 24 + (10 if line.startswith("  - ") else 0)

        if is_code:
            commands.append(
                _rect(MARGIN_X + 16, y - 4, PAGE_WIDTH - (MARGIN_X * 2) - 26, 16, COLOR_CODE_BG)
            )

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
