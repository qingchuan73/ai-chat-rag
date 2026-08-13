import re


TARGET_CHUNK_SIZE = 900
MAX_CHUNK_SIZE = 1300

SECTION_TITLE_PATTERN = re.compile(
    r"^\s*(第[一二三四五六七八九十百]+[章节部分][^\n]{0,40}|"
    r"\d+(?:\.\d+){0,5}[\.、\s]+[^\n]{2,80})\s*$"
)

YEAR_PATTERN = re.compile(r"(20\d{2})\s*年?|R1[5-9]|R2[0-9]")
LOW_VALUE_PATTERNS = (
    "目录",
    "附录",
    "版本更新记录",
    "修订记录",
    "参考文献",
    "引用标准",
    "封面",
)


def normalize_text(text):
    if not text:
        return ""

    lines = []

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()

        if not line:
            continue

        if re.fullmatch(r"\d+", line):
            continue

        if re.fullmatch(r"[-—_=]{3,}", line):
            continue

        lines.append(line)

    return "\n".join(lines)


def is_section_title(line):
    if not line:
        return False

    if len(line) > 90:
        return False

    return bool(SECTION_TITLE_PATTERN.match(line))


def get_content_type(text, page):
    normalized = text.strip()

    if page == 1:
        return "cover"

    if "目录" in normalized[:120]:
        return "toc"

    if "附录" in normalized[:80] or "版本更新记录" in normalized[:180]:
        return "appendix"

    return "body"


def get_priority(content_type):
    if content_type == "body":
        return 1

    if content_type in {"toc", "appendix"}:
        return 3

    return 2


def extract_year_labels(text):
    years = sorted(set(YEAR_PATTERN.findall(text or "")))
    return ",".join(years) if years else "general"


def split_sentences(paragraph):
    parts = re.split(r"(?<=[。！？；;])", paragraph)
    return [
        part.strip()
        for part in parts
        if part.strip()
    ]


def split_long_text(text, max_size=MAX_CHUNK_SIZE):
    units = split_sentences(text)

    if not units:
        return []

    chunks = []
    current = ""

    for unit in units:
        candidate = f"{current}{unit}" if not current else f"{current}\n{unit}"

        if len(candidate) <= max_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        current = unit

    if current:
        chunks.append(current)

    return chunks


def detect_page_sections(page_text, current_chapter):
    sections = []
    active_title = current_chapter
    active_lines = []

    for line in page_text.split("\n"):
        if is_section_title(line):
            if active_lines:
                sections.append(
                    {
                        "chapter": active_title or "未识别章节",
                        "content": "\n".join(active_lines).strip()
                    }
                )
                active_lines = []

            active_title = line
            continue

        active_lines.append(line)

    if active_lines:
        sections.append(
            {
                "chapter": active_title or "未识别章节",
                "content": "\n".join(active_lines).strip()
            }
        )

    return sections, active_title


def build_semantic_chunks(section_text):
    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(r"\n{1,}", section_text)
        if paragraph.strip()
    ]

    chunks = []
    current = ""

    for paragraph in paragraphs:
        paragraph_parts = split_long_text(paragraph)

        for part in paragraph_parts:
            candidate = part if not current else f"{current}\n{part}"

            if len(candidate) <= TARGET_CHUNK_SIZE:
                current = candidate
                continue

            if current:
                chunks.append(current)

            current = part

    if current:
        chunks.append(current)

    return chunks


def should_skip_chunk(text, content_type):
    stripped = text.strip()

    if len(stripped) < 40:
        return True

    if content_type in {"cover", "toc"}:
        return True

    low_value_hits = sum(
        1
        for pattern in LOW_VALUE_PATTERNS
        if pattern in stripped[:240]
    )

    return low_value_hits >= 2 and len(stripped) < 500


def split_document_pages(pages):
    chunks = []
    metadatas = []
    current_chapter = None

    for page in pages:
        page_number = page.get("page")
        page_text = normalize_text(
            page.get("content", "")
        )

        if not page_text:
            continue

        content_type = get_content_type(
            page_text,
            page_number
        )
        priority = get_priority(content_type)
        sections, current_chapter = detect_page_sections(
            page_text,
            current_chapter
        )

        for section in sections:
            section_chunks = build_semantic_chunks(
                section["content"]
            )

            for chunk in section_chunks:
                if should_skip_chunk(chunk, content_type):
                    continue

                chunks.append(chunk)
                metadatas.append(
                    {
                        "page": page_number,
                        "chapter": section["chapter"],
                        "section_path": section["chapter"],
                        "content_type": content_type,
                        "year_labels": extract_year_labels(chunk),
                        "priority": priority,
                    }
                )

    return chunks, metadatas
