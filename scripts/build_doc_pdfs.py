"""Build PDF copies of Markdown docs.

This is a small no-dependency PDF builder for repo documentation. Markdown stays
the source of truth; PDFs are the easier-to-share reading copies.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import textwrap


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "docs" / "pdf"

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
COLOR_PAGE_BG = (0.985, 0.976, 0.945)

SKIPPED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


@dataclass(frozen=True)
class Line:
    text: str
    font: str = "F1"
    size: float = 10.2
    leading: float = 13.2
    before: float = 0
    color: tuple[float, float, float] = COLOR_TEXT
    code: bool = False


def clean_text(text: str) -> str:
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
    for source, replacement in replacements.items():
        text = text.replace(source, replacement)
    return text.encode("latin-1", "replace").decode("latin-1")


def escape_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def rgb(color: tuple[float, float, float]) -> str:
    return f"{color[0]:.3f} {color[1]:.3f} {color[2]:.3f}"


def rect(x: float, y: float, width: float, height: float, color: tuple[float, float, float]) -> str:
    return f"{rgb(color)} rg\n{x:.1f} {y:.1f} {width:.1f} {height:.1f} re f"


def text(x: float, y: float, line: Line) -> list[str]:
    return [
        "BT",
        f"/{line.font} {line.size:.1f} Tf",
        f"{rgb(line.color)} rg",
        f"{x:.1f} {y:.1f} Td",
        f"({escape_text(clean_text(line.text))}) Tj",
        "ET",
    ]


def strip_markdown_links(value: str) -> str:
    value = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = value.replace("**", "").replace("__", "")
    value = value.replace("`", "")
    return value


def title_from_markdown(markdown: str, fallback: str) -> str:
    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if line.startswith("# "):
            return strip_markdown_links(line[2:].strip())
    return fallback


def markdown_to_lines(markdown: str) -> list[Line]:
    output: list[Line] = []
    in_code = False
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if not paragraph:
            return
        value = strip_markdown_links(" ".join(paragraph))
        for part in textwrap.wrap(value, width=MAX_CHARS):
            output.append(Line(part))
        output.append(Line("", leading=6))
        paragraph.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            in_code = not in_code
            continue

        if in_code:
            wrapped = textwrap.wrap(stripped, width=88, replace_whitespace=False) or [""]
            for part in wrapped:
                output.append(
                    Line(
                        part,
                        font="F2",
                        size=8.8,
                        leading=11.5,
                        color=(0.14, 0.28, 0.38),
                        code=True,
                    )
                )
            continue

        if not stripped:
            flush_paragraph()
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            output.append(
                Line(
                    strip_markdown_links(stripped[2:]),
                    font="F3",
                    size=21,
                    leading=27,
                    before=6,
                    color=COLOR_HEADER,
                )
            )
            output.append(Line("", leading=4))
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            output.append(
                Line(
                    strip_markdown_links(stripped[3:]),
                    font="F3",
                    size=14.5,
                    leading=19,
                    before=10,
                    color=COLOR_HEADER,
                )
            )
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            output.append(
                Line(
                    strip_markdown_links(stripped[4:]),
                    font="F3",
                    size=12,
                    leading=16,
                    before=8,
                    color=COLOR_HEADER,
                )
            )
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            value = strip_markdown_links(stripped[2:])
            wrapped = textwrap.wrap(value, width=MAX_CHARS - 5)
            if wrapped:
                output.append(Line("- " + wrapped[0], leading=12.5))
                for part in wrapped[1:]:
                    output.append(Line("  " + part, leading=12.5))
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            flush_paragraph()
            prefix = numbered.group(1) + ". "
            value = strip_markdown_links(numbered.group(2))
            wrapped = textwrap.wrap(value, width=MAX_CHARS - len(prefix))
            if wrapped:
                output.append(Line(prefix + wrapped[0], leading=12.5))
                for part in wrapped[1:]:
                    output.append(Line(" " * len(prefix) + part, leading=12.5))
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            output.append(
                Line(
                    strip_markdown_links(stripped[2:]),
                    font="F3",
                    size=10.5,
                    leading=14,
                    before=4,
                    color=COLOR_ACCENT,
                )
            )
            continue

        if set(stripped) <= {"-", " "}:
            flush_paragraph()
            output.append(Line("", leading=8))
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


def page_stream(
    page: list[tuple[float, Line]],
    page_number: int,
    total_pages: int,
    document_title: str,
) -> bytes:
    commands: list[str] = [
        rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, (1, 1, 1)),
        rect(0, PAGE_HEIGHT - 44, PAGE_WIDTH, 44, COLOR_HEADER),
        rect(0, PAGE_HEIGHT - 44, 8, 44, COLOR_ACCENT),
        *text(
            MARGIN_X,
            PAGE_HEIGHT - 27,
            Line(document_title[:76], font="F3", size=10, color=(1, 1, 1)),
        ),
        *text(PAGE_WIDTH - 96, 28, Line(f"{page_number}/{total_pages}", size=8.5, color=COLOR_MUTED)),
        rect(MARGIN_X, 48, PAGE_WIDTH - (MARGIN_X * 2), 1, (0.78, 0.76, 0.70)),
    ]
    for y, line in page:
        if line.code and line.text:
            commands.append(rect(MARGIN_X - 6, y - 3, PAGE_WIDTH - (MARGIN_X * 2) + 12, 11, COLOR_CODE_BG))
        if line.text:
            commands.extend(text(MARGIN_X, y, line))
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


def cover_stream(document_title: str, source_path: Path, total_pages: int) -> bytes:
    source_label = source_path.as_posix()
    commands: list[str] = [
        rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, COLOR_PAGE_BG),
        rect(0, PAGE_HEIGHT - 178, PAGE_WIDTH, 178, COLOR_HEADER),
        rect(0, PAGE_HEIGHT - 178, 14, 178, COLOR_ACCENT),
        *text(MARGIN_X, PAGE_HEIGHT - 78, Line("Emergency Training", font="F3", size=26, color=(1, 1, 1))),
        *text(MARGIN_X, PAGE_HEIGHT - 111, Line("Simulator POC", font="F3", size=26, color=(1, 1, 1))),
        *text(
            MARGIN_X,
            PAGE_HEIGHT - 144,
            Line("Markdown documentation PDF copy", size=11, color=(0.78, 0.84, 0.88)),
        ),
        rect(MARGIN_X, 494, PAGE_WIDTH - (MARGIN_X * 2), 2, COLOR_ACCENT),
        *text(MARGIN_X, 452, Line(document_title[:78], font="F3", size=17, color=COLOR_HEADER)),
        *text(MARGIN_X, 420, Line(f"Source: {source_label[:82]}", size=10.5, color=COLOR_MUTED)),
        *text(
            MARGIN_X,
            368,
            Line(
                "Markdown stays editable. This PDF is the reading/share copy.",
                size=11.5,
            ),
        ),
        *text(
            MARGIN_X,
            338,
            Line(
                "Boundary: this project is still a POC, not operational guidance.",
                size=10.5,
                color=COLOR_MUTED,
            ),
        ),
        *text(PAGE_WIDTH - 96, 28, Line(f"1/{total_pages}", size=8.5, color=COLOR_MUTED)),
    ]
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


def build_pdf(
    pages: list[list[tuple[float, Line]]],
    document_title: str,
    source_path: Path,
) -> bytes:
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
    total_pages = len(pages) + 1
    streams = [cover_stream(document_title, source_path, total_pages)] + [
        page_stream(page, index, total_pages, document_title)
        for index, page in enumerate(pages, start=2)
    ]
    for stream in streams:
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
                f"/Resources << /Font << /F1 {font_regular_id} 0 R "
                f"/F2 {font_mono_id} 0 R /F3 {font_bold_id} 0 R >> >> "
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


def should_skip_markdown(path: Path) -> bool:
    relative_parts = path.relative_to(ROOT).parts
    if any(part in SKIPPED_DIRS for part in relative_parts):
        return True
    if path.name.lower() == "readme.md":
        return True
    return PDF_DIR in path.parents


def discover_markdown_files() -> list[Path]:
    files = [
        path
        for path in ROOT.rglob("*.md")
        if path.is_file() and not should_skip_markdown(path)
    ]
    return sorted(files, key=lambda item: item.relative_to(ROOT).as_posix().lower())


def output_path_for(markdown_path: Path) -> Path:
    relative = markdown_path.relative_to(ROOT)
    if relative.parts and relative.parts[0] == "docs":
        relative = Path(*relative.parts[1:])
    return PDF_DIR / relative.with_suffix(".pdf")


def build_one(markdown_path: Path) -> Path:
    relative_path = markdown_path.relative_to(ROOT)
    markdown = markdown_path.read_text(encoding="utf-8")
    title = title_from_markdown(markdown, markdown_path.stem.replace("-", " ").title())
    lines = markdown_to_lines(markdown)
    pages = paginate(lines)
    output_path = output_path_for(markdown_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(build_pdf(pages, title, relative_path))
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build PDF copies of Markdown docs.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional Markdown paths. If omitted, every repo Markdown doc is converted.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    markdown_files = [ROOT / path for path in args.paths] if args.paths else discover_markdown_files()

    written: list[Path] = []
    for markdown_path in markdown_files:
        if markdown_path.suffix.lower() != ".md":
            raise SystemExit(f"Not a Markdown file: {markdown_path}")
        if not markdown_path.exists():
            raise SystemExit(f"Missing Markdown file: {markdown_path}")
        if should_skip_markdown(markdown_path):
            continue
        written.append(build_one(markdown_path))

    print(f"Wrote {len(written)} PDF file(s) under {PDF_DIR.relative_to(ROOT)}")
    for path in written:
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
