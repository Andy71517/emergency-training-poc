"""Build the small submission packet from Markdown docs.

Markdown stays the editable source. This script creates the cleaner PDF packet
that is useful for Dr. Cameron, reviewers, clients, or future teammates.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import textwrap


ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / "docs" / "submission-packet"

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN_X = 54
TOP_Y = 718
BOTTOM_Y = 58
MAX_CHARS = 92

COLOR_TEXT = (0.08, 0.10, 0.12)
COLOR_MUTED = (0.39, 0.43, 0.47)
COLOR_AZURE = (0.02, 0.29, 0.52)
COLOR_AZURE_DARK = (0.02, 0.17, 0.31)
COLOR_AZURE_SOFT = (0.89, 0.96, 1.00)
COLOR_AMBER = (0.96, 0.58, 0.12)
COLOR_AMBER_SOFT = (1.00, 0.94, 0.82)
COLOR_CODE_BG = (0.92, 0.96, 0.98)
COLOR_PAGE_BG = (0.975, 0.988, 1.00)


@dataclass(frozen=True)
class PacketDoc:
    source: Path
    output_name: str
    label: str
    layout: str = "document"


@dataclass(frozen=True)
class Line:
    text: str
    font: str = "F1"
    size: float = 10.2
    leading: float = 13.2
    before: float = 0
    color: tuple[float, float, float] = COLOR_TEXT
    code: bool = False


PACKET_DOCS = (
    PacketDoc(
        Path("docs/reports/project-overview-report.md"),
        "01-project-overview-report.pdf",
        "Submission report",
    ),
    PacketDoc(
        Path("docs/presentations/project-overview-one-page-handout.md"),
        "02-one-page-handout.pdf",
        "One-page handout",
        "handout",
    ),
    PacketDoc(Path("docs/roadmap.md"), "03-roadmap.pdf", "Project roadmap"),
    PacketDoc(
        Path("docs/full-project-vision.md"),
        "04-full-project-vision.pdf",
        "Full project vision",
    ),
)


def clean_text(value: str) -> str:
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
        value = value.replace(source, replacement)
    return value.encode("latin-1", "replace").decode("latin-1")


def escape_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


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
                        color=COLOR_AZURE_DARK,
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
                    color=COLOR_AZURE_DARK,
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
                    color=COLOR_AZURE,
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
                    color=COLOR_AZURE,
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
                    color=COLOR_AMBER,
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


def markdown_to_handout_lines(markdown: str) -> list[Line]:
    output: list[Line] = []
    in_code = False
    paragraph: list[str] = []
    max_chars = 58

    def flush_paragraph() -> None:
        if not paragraph:
            return
        value = strip_markdown_links(" ".join(paragraph))
        for part in textwrap.wrap(value, width=max_chars):
            output.append(Line(part, size=7.7, leading=9.2))
        output.append(Line("", leading=2.5))
        paragraph.clear()

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            in_code = not in_code
            continue

        if in_code:
            wrapped = textwrap.wrap(stripped, width=max_chars, replace_whitespace=False) or [""]
            for part in wrapped:
                output.append(
                    Line(
                        part,
                        font="F2",
                        size=7.0,
                        leading=8.4,
                        color=COLOR_AZURE_DARK,
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
                    size=15.5,
                    leading=18,
                    before=0,
                    color=COLOR_AZURE_DARK,
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
                    size=9.7,
                    leading=11.2,
                    before=4,
                    color=COLOR_AZURE,
                )
            )
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            value = strip_markdown_links(stripped[2:])
            wrapped = textwrap.wrap(value, width=max_chars - 3)
            if wrapped:
                output.append(Line("- " + wrapped[0], size=7.5, leading=8.8))
                for part in wrapped[1:]:
                    output.append(Line("  " + part, size=7.5, leading=8.8))
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            flush_paragraph()
            prefix = numbered.group(1) + ". "
            value = strip_markdown_links(numbered.group(2))
            wrapped = textwrap.wrap(value, width=max_chars - len(prefix))
            if wrapped:
                output.append(Line(prefix + wrapped[0], size=7.5, leading=8.8))
                for part in wrapped[1:]:
                    output.append(Line(" " * len(prefix) + part, size=7.5, leading=8.8))
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            output.append(
                Line(
                    strip_markdown_links(stripped[2:]),
                    font="F3",
                    size=8.2,
                    leading=9.8,
                    before=3,
                    color=COLOR_AMBER,
                )
            )
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
    label: str,
) -> bytes:
    commands: list[str] = [
        rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, (1, 1, 1)),
        rect(0, PAGE_HEIGHT - 50, PAGE_WIDTH, 50, COLOR_AZURE_DARK),
        rect(0, PAGE_HEIGHT - 50, PAGE_WIDTH, 5, COLOR_AMBER),
        rect(0, 0, 10, PAGE_HEIGHT, COLOR_AZURE_SOFT),
        *text(MARGIN_X, PAGE_HEIGHT - 30, Line(label.upper(), font="F3", size=8.7, color=COLOR_AMBER_SOFT)),
        *text(MARGIN_X + 112, PAGE_HEIGHT - 30, Line(document_title[:70], font="F3", size=9.4, color=(1, 1, 1))),
        *text(PAGE_WIDTH - 96, 28, Line(f"{page_number}/{total_pages}", size=8.5, color=COLOR_MUTED)),
        rect(MARGIN_X, 48, PAGE_WIDTH - (MARGIN_X * 2), 1, (0.78, 0.84, 0.88)),
    ]
    for y, line in page:
        if line.code and line.text:
            commands.append(rect(MARGIN_X - 6, y - 3, PAGE_WIDTH - (MARGIN_X * 2) + 12, 11, COLOR_CODE_BG))
        if line.text:
            commands.extend(text(MARGIN_X, y, line))
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


def cover_stream(document_title: str, source_path: Path, total_pages: int, label: str) -> bytes:
    source_label = source_path.as_posix()
    commands: list[str] = [
        rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, COLOR_PAGE_BG),
        rect(0, PAGE_HEIGHT - 190, PAGE_WIDTH, 190, COLOR_AZURE_DARK),
        rect(0, PAGE_HEIGHT - 190, 18, 190, COLOR_AMBER),
        rect(PAGE_WIDTH - 132, PAGE_HEIGHT - 190, 132, 190, COLOR_AZURE),
        rect(MARGIN_X, 494, PAGE_WIDTH - (MARGIN_X * 2), 3, COLOR_AMBER),
        *text(MARGIN_X, PAGE_HEIGHT - 74, Line("Emergency Training", font="F3", size=26, color=(1, 1, 1))),
        *text(MARGIN_X, PAGE_HEIGHT - 108, Line("Simulator POC", font="F3", size=26, color=(1, 1, 1))),
        *text(MARGIN_X, PAGE_HEIGHT - 142, Line("Submission Packet", size=12, color=COLOR_AMBER_SOFT)),
        *text(MARGIN_X, 452, Line(document_title[:78], font="F3", size=17, color=COLOR_AZURE_DARK)),
        *text(MARGIN_X, 421, Line(label, font="F3", size=11, color=COLOR_AMBER)),
        *text(MARGIN_X, 391, Line(f"Source: {source_label[:82]}", size=10.5, color=COLOR_MUTED)),
        *text(
            MARGIN_X,
            338,
            Line("Prepared for review, discussion, and project handoff.", size=11.5),
        ),
        *text(
            MARGIN_X,
            308,
            Line("Markdown stays editable. This PDF is the clean reading copy.", size=11.5),
        ),
        *text(
            MARGIN_X,
            278,
            Line(
                "Boundary: this is still a POC, not operational or clinical guidance.",
                size=10.5,
                color=COLOR_MUTED,
            ),
        ),
        *text(PAGE_WIDTH - 96, 28, Line(f"1/{total_pages}", size=8.5, color=COLOR_MUTED)),
    ]
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


@dataclass(frozen=True)
class HandoutSection:
    title: str
    items: tuple[str, ...]


def parse_handout_sections(markdown: str) -> tuple[str, list[HandoutSection]]:
    document_title = "Emergency Training Simulator POC"
    sections: list[HandoutSection] = []
    current_title: str | None = None
    current_items: list[str] = []

    def flush_section() -> None:
        nonlocal current_items, current_title
        if current_title:
            sections.append(HandoutSection(current_title, tuple(current_items)))
        current_title = None
        current_items = []

    for raw_line in markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("# "):
            document_title = strip_markdown_links(line[2:])
            continue
        if line.startswith("## "):
            flush_section()
            current_title = strip_markdown_links(line[3:])
            continue
        if line.startswith("- "):
            current_items.append(strip_markdown_links(line[2:]))
            continue
        if line.startswith("> "):
            current_items.append(strip_markdown_links(line[2:]))
            continue
        if not line.startswith("```"):
            current_items.append(strip_markdown_links(line))

    flush_section()
    return document_title, sections


def wrapped_parts(value: str, width: int) -> list[str]:
    return textwrap.wrap(strip_markdown_links(value), width=width) or [""]


def add_wrapped_text(
    commands: list[str],
    x: float,
    y: float,
    value: str,
    width: int,
    line: Line,
    max_lines: int,
) -> float:
    parts = wrapped_parts(value, width)[:max_lines]
    for part in parts:
        commands.extend(text(x, y, Line(part, line.font, line.size, line.leading, color=line.color)))
        y -= line.leading
    return y


def draw_card(
    commands: list[str],
    x: float,
    y: float,
    width: float,
    height: float,
    section: HandoutSection,
    accent: tuple[float, float, float],
) -> None:
    commands.append(rect(x, y, width, height, (0.985, 0.992, 1.000)))
    commands.append(rect(x, y + height - 24, width, 24, accent))
    commands.append(rect(x, y, 3.5, height, COLOR_AMBER))
    commands.extend(
        text(
            x + 12,
            y + height - 16,
            Line(section.title.upper()[:34], font="F3", size=8.4, color=COLOR_AZURE_DARK),
        )
    )

    cursor_y = y + height - 40
    remaining_lines = 9
    for item in section.items[:5]:
        wrapped = wrapped_parts(item, 38)
        for index, part in enumerate(wrapped[:2]):
            prefix = "- " if index == 0 else "  "
            if remaining_lines <= 0:
                return
            commands.extend(
                text(
                    x + 12,
                    cursor_y,
                    Line(prefix + part, size=8.2, leading=10.1, color=COLOR_TEXT),
                )
            )
            cursor_y -= 10.1
            remaining_lines -= 1
        cursor_y -= 1.8


def handout_stream(markdown: str, document_title: str, source_path: Path, label: str) -> bytes:
    width = 792
    height = 612
    source_label = source_path.as_posix()
    parsed_title, sections = parse_handout_sections(markdown)
    document_title = parsed_title or document_title
    section_map = {section.title.lower(): section for section in sections}
    card_titles = [
        "What this is",
        "What works today",
        "Current demo",
        "Current scenario",
        "Boundaries",
        "Next direction",
    ]
    cards = [
        section_map.get(title.lower(), HandoutSection(title, ()))
        for title in card_titles
    ]
    takeaway = section_map.get("main takeaway", HandoutSection("Main takeaway", ()))
    takeaway_text = takeaway.items[0] if takeaway.items else ""

    commands: list[str] = [
        rect(0, 0, width, height, (1, 1, 1)),
        rect(0, height - 88, width, 88, COLOR_AZURE_DARK),
        rect(0, height - 88, width, 7, COLOR_AMBER),
        rect(0, 0, 14, height, COLOR_AZURE_SOFT),
        *text(42, height - 34, Line(document_title[:70], font="F3", size=18, color=(1, 1, 1))),
        *text(42, height - 59, Line(label.upper(), font="F3", size=8.8, color=COLOR_AMBER_SOFT)),
        *text(
            268,
            height - 59,
            Line("Project packet / quick read for Dr. Cameron", size=8.8, color=(0.82, 0.90, 0.96)),
        ),
        rect(42, 50, 708, 44, COLOR_AMBER_SOFT),
        *text(55, 76, Line("MAIN TAKEAWAY", font="F3", size=8.6, color=COLOR_AZURE_DARK)),
        *text(42, 24, Line(f"Source: {source_label}", size=7.2, color=COLOR_MUTED)),
        *text(724, 24, Line("1/1", size=7.2, color=COLOR_MUTED)),
    ]
    card_positions = [
        (42, 354),
        (284, 354),
        (526, 354),
        (42, 138),
        (284, 138),
        (526, 138),
    ]
    for index, section in enumerate(cards):
        accent = COLOR_AZURE_SOFT if index % 2 == 0 else COLOR_AMBER_SOFT
        draw_card(commands, card_positions[index][0], card_positions[index][1], 224, 158, section, accent)

    add_wrapped_text(
        commands,
        55,
        64,
        takeaway_text,
        112,
        Line("", font="F3", size=9.2, leading=10.2, color=COLOR_AZURE_DARK),
        2,
    )
    return ("\n".join(commands) + "\n").encode("latin-1", "replace")


def build_single_page_pdf(stream: bytes, width: int, height: int) -> bytes:
    objects: list[bytes] = []

    def add_object(data: bytes) -> int:
        objects.append(data)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_regular_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_mono_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    font_bold_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
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
            f"/MediaBox [0 0 {width} {height}] "
            f"/Resources << /Font << /F1 {font_regular_id} 0 R "
            f"/F2 {font_mono_id} 0 R /F3 {font_bold_id} 0 R >> >> "
            f"/Contents {stream_id} 0 R >>"
        ).encode("ascii")
    )
    objects[pages_id - 1] = f"<< /Type /Pages /Kids [{page_id} 0 R] /Count 1 >>".encode(
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


def build_handout_pdf(markdown: str, document_title: str, source_path: Path, label: str) -> bytes:
    stream = handout_stream(markdown, document_title, source_path, label)
    return build_single_page_pdf(stream, width=792, height=612)


def build_pdf(
    pages: list[list[tuple[float, Line]]],
    document_title: str,
    source_path: Path,
    label: str,
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
    streams = [cover_stream(document_title, source_path, total_pages, label)] + [
        page_stream(page, index, total_pages, document_title, label)
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


def clean_packet_dir() -> None:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    for old_pdf in PACKET_DIR.glob("*.pdf"):
        old_pdf.unlink()


def output_name_for(markdown_path: Path) -> str:
    stem = markdown_path.stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return f"{stem}.pdf"


def build_one(source: Path, output_name: str, label: str, layout: str) -> Path:
    markdown_path = ROOT / source
    if markdown_path.suffix.lower() != ".md":
        raise SystemExit(f"Not a Markdown file: {markdown_path}")
    if not markdown_path.exists():
        raise SystemExit(f"Missing Markdown file: {markdown_path}")
    if markdown_path.name.lower() == "readme.md":
        raise SystemExit("README files stay on GitHub and are not part of the PDF packet.")

    markdown = markdown_path.read_text(encoding="utf-8")
    title = title_from_markdown(markdown, markdown_path.stem.replace("-", " ").title())
    output_path = PACKET_DIR / output_name
    if layout == "handout":
        output_path.write_bytes(build_handout_pdf(markdown, title, source, label))
    else:
        pages = paginate(markdown_to_lines(markdown))
        output_path.write_bytes(build_pdf(pages, title, source, label))
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the small documentation submission packet.")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional Markdown files. If omitted, the default four-file packet is built.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    clean_packet_dir()

    if args.paths:
        docs = [
            PacketDoc(Path(path), output_name_for(Path(path)), "Custom packet document")
            for path in args.paths
        ]
    else:
        docs = list(PACKET_DOCS)

    written = [build_one(doc.source, doc.output_name, doc.label, doc.layout) for doc in docs]

    print(f"Wrote {len(written)} PDF file(s) under {PACKET_DIR.relative_to(ROOT)}")
    for path in written:
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
