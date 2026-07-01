"""Build a simple PDF deck from project-overview-slides.md.

This script intentionally uses only the Python standard library.
It is not a full presentation engine. It creates a readable PDF that is
easy to share without adding another dependency to the POC.
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
MARGIN_X = 58
TITLE_Y = 548
BODY_Y = 492
LINE_HEIGHT = 20
MAX_BODY_CHARS = 78


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


def _content_stream(title: str, body: list[str], page_number: int, total_pages: int) -> bytes:
    title = _clean_for_pdf(title)
    lines = [_clean_for_pdf(line) for line in _format_body(body)]

    commands: list[str] = [
        "BT",
        "/F1 26 Tf",
        f"{MARGIN_X} {TITLE_Y} Td",
        f"({_escape_pdf_text(title)}) Tj",
        "ET",
        "BT",
        "/F1 14 Tf",
        f"{MARGIN_X} {BODY_Y} Td",
    ]

    y_lines = 0
    for line in lines:
        if y_lines > 19:
            commands.append(f"(...) Tj")
            break
        commands.append(f"({_escape_pdf_text(line)}) Tj")
        commands.append(f"0 -{LINE_HEIGHT} Td")
        y_lines += 1

    commands.extend(
        [
            "ET",
            "BT",
            "/F1 10 Tf",
            f"{PAGE_WIDTH - 120} 32 Td",
            f"(Slide {page_number} of {total_pages}) Tj",
            "ET",
        ]
    )
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


def _build_pdf(slides: list[tuple[str, list[str]]]) -> bytes:
    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

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
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
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

