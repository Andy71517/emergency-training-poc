"""Build a denser report PDF from project-overview-report.md.

This is a small no-dependency PDF writer. It is intentionally simple, but it
produces a more report-like PDF than the slide deck export.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import textwrap


HERE = Path(__file__).resolve().parent
REPORT_MD = HERE / "project-overview-report.md"
OUTPUT_PDF = HERE / "emergency-training-poc-report.pdf"

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN_X = 54
TOP_Y = 724
BOTTOM_Y = 58
MAX_CHARS = 92

COLOR_TEXT = (0.08, 0.09, 0.10)
COLOR_MUTED = (0.38, 0.40, 0.43)
COLOR_HEADER = (0.055, 0.105, 0.165)
COLOR_ACCENT = (0.95, 0.42, 0.16)
COLOR_CODE_BG = (0.94, 0.935, 0.91)


@dataclass(frozen=True)
class Line:
    text: str
    font: str = "F1"
    size: float = 10.2
    leading: float = 13.2
    before: float = 0
    color: tuple[float, float, float] = COLOR_TEXT
    code: bool = False


def _clean(text: str) -> str:
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


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _rgb(color: tuple[float, float, float]) -> str:
    return f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f}"


def _rect(x: float, y: float, width: float, height: float, color: tuple[float, float, float]) -> str:
    return f"{_rgb(color)} rg\n{x:.1f} {y:.1f} {width:.1f} {height:.1f} re f"


def _text(x: float, y: float, line: Line) -> list[str]:
    return [
        "BT",
        f"/{line.font} {line.size:.1f} Tf",
        f"{_rgb(line.color)} rg",
        f"{x:.1f} {y:.1f} Td",
        f"({_escape(_clean(line.text))}) Tj",
        "ET",
    ]


def markdown_to_lines(markdown: str) -> list[Line]:
    output: list[Line] = []
    in_code = False
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph:
            return
        text = " ".join(paragraph)
        for part in textwrap.wrap(text, width=MAX_CHARS):
            output.append(Line(part))
        output.append(Line("", leading=6))
        paragraph.clear()

    for raw in markdown.splitlines():
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            in_code = not in_code
            continue

        if in_code:
            for part in textwrap.wrap(stripped, width=88, replace_whitespace=False) or [""]:
                output.append(Line(part, font="F2", size=8.8, leading=11.5, color=(0.14, 0.28, 0.38), code=True))
            continue

        if not stripped:
            flush_paragraph()
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            output.append(Line(stripped[2:], font="F3", size=21, leading=27, before=6, color=COLOR_HEADER))
            output.append(Line("", leading=4))
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            output.append(Line(stripped[3:], font="F3", size=14.5, leading=19, before=10, color=COLOR_HEADER))
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            output.append(Line(stripped[4:], font="F3", size=12, leading=16, before=8, color=COLOR_HEADER))
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            wrapped = textwrap.wrap(stripped[2:], width=MAX_CHARS - 5)
            if wrapped:
                output.append(Line("- " + wrapped[0], leading=12.5))
                for part in wrapped[1:]:
                    output.append(Line("  " + part, leading=12.5))
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            flush_paragraph()
            prefix = numbered.group(1) + ". "
            wrapped = textwrap.wrap(numbered.group(2), width=MAX_CHARS - len(prefix))
            if wrapped:
                output.append(Line(prefix + wrapped[0], leading=12.5))
                for part in wrapped[1:]:
                    output.append(Line(" " * len(prefix) + part, leading=12.5))
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            output.append(Line(stripped[2:], font="F3", size=10.5, leading=14, before=4, color=COLOR_ACCENT))
            continue

        paragraph.append(stripped)

    flush_paragraph()
    return output


def paginate(lines: list[Line]) -> list[list[tuple[float, Line]]]:
    pages: list[list[tuple[float, Line]]] = []
    page: list[tuple[float, Line]] = []
    y = TOP_Y

    for line in lines:
        y -= line.before
        if y - line.leading < BOTTOM_Y and page:
            pages.append(page)
            page = []
            y = TOP_Y
            y -= line.before
        page.append((y, line))
        y -= line.leading

    if page:
        pages.append(page)
    return pages


def page_stream(page: list[tuple[float, Line]], page_number: int, total_pages: int) -> bytes:
    commands: list[str] = [
        _rect(0, PAGE_HEIGHT - 44, PAGE_WIDTH, 44, COLOR_HEADER),
        _rect(0, PAGE_HEIGHT - 44, 8, 44, COLOR_ACCENT),
        *_text(MARGIN_X, PAGE_HEIGHT - 27, Line("Emergency Training Simulator POC Report", font="F3", size=10, color=(1, 1, 1))),
        *_text(PAGE_WIDTH - 96, 28, Line(f"{page_number}/{total_pages}", size=8.5, color=COLOR_MUTED)),
        _rect(MARGIN_X, 48, PAGE_WIDTH - (MARGIN_X * 2), 1, (0.78, 0.76, 0.70)),
    ]
    for y, line in page:
        if line.code and line.text:
            commands.append(_rect(MARGIN_X - 6, y - 3, PAGE_WIDTH - (MARGIN_X * 2) + 12, 11, COLOR_CODE_BG))
        if line.text:
            commands.extend(_text(MARGIN_X, y, line))
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


def build_pdf(pages: list[list[tuple[float, Line]]]) -> bytes:
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
    for index, page in enumerate(pages, start=1):
        stream = page_stream(page, index, len(pages))
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
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_mono_id} 0 R /F3 {font_bold_id} 0 R >> >> "
                f"/Contents {stream_id} 0 R >>"
            ).encode("ascii")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")

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
    markdown = REPORT_MD.read_text(encoding="utf-8")
    pages = paginate(markdown_to_lines(markdown))
    OUTPUT_PDF.write_bytes(build_pdf(pages))
    print(f"Wrote {OUTPUT_PDF} ({len(pages)} pages)")


if __name__ == "__main__":
    main()

