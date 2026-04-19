"""Unit tests for document parsers (PDF / TXT / DOCX).

All tests create real temporary files and verify parsing output.
"""
import tempfile
from pathlib import Path

import pymupdf
import pytest
from docx import Document as DocxDocument

from app.services.parser import (
    ParsedDocument,
    parse_docx,
    parse_file,
    parse_pdf,
    parse_txt,
)

pytestmark = pytest.mark.unit


# ── TXT ──────────────────────────────────────────────────────────────────

class TestParseTxt:
    def test_basic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("Hello World", encoding="utf-8")
        result = parse_txt(f)
        assert result.page_count == 1
        assert result.pages[0].text == "Hello World"
        assert result.pages[0].page_number == 1

    def test_chinese_content(self, tmp_path):
        f = tmp_path / "中文.txt"
        f.write_text("知识库系统\n第二行", encoding="utf-8")
        result = parse_txt(f)
        assert "知识库系统" in result.full_text
        assert "第二行" in result.full_text

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        result = parse_txt(f)
        assert result.page_count == 1
        assert result.full_text == ""

    def test_multiline(self, tmp_path):
        content = "line1\nline2\nline3"
        f = tmp_path / "multi.txt"
        f.write_text(content, encoding="utf-8")
        result = parse_txt(f)
        assert result.full_text == content


# ── PDF ──────────────────────────────────────────────────────────────────

class TestParsePdf:
    def _make_pdf(self, path: Path, pages_text: list[str]):
        doc = pymupdf.open()
        for text in pages_text:
            page = doc.new_page()
            page.insert_text((72, 72), text, fontsize=12)
        doc.save(str(path))
        doc.close()

    def test_single_page(self, tmp_path):
        f = tmp_path / "single.pdf"
        self._make_pdf(f, ["Hello from PDF"])
        result = parse_pdf(f)
        assert result.page_count == 1
        assert "Hello from PDF" in result.pages[0].text

    def test_multi_page(self, tmp_path):
        f = tmp_path / "multi.pdf"
        self._make_pdf(f, ["Page one content", "Page two content"])
        result = parse_pdf(f)
        assert result.page_count == 2
        assert result.pages[0].page_number == 1
        assert result.pages[1].page_number == 2
        assert "Page one" in result.pages[0].text
        assert "Page two" in result.pages[1].text

    def test_full_text_joins_pages(self, tmp_path):
        f = tmp_path / "join.pdf"
        self._make_pdf(f, ["AAA", "BBB"])
        result = parse_pdf(f)
        assert "AAA" in result.full_text
        assert "BBB" in result.full_text


# ── DOCX ─────────────────────────────────────────────────────────────────

class TestParseDocx:
    def _make_docx(self, path: Path, paragraphs: list[str]):
        doc = DocxDocument()
        for p in paragraphs:
            doc.add_paragraph(p)
        doc.save(str(path))

    def test_basic(self, tmp_path):
        f = tmp_path / "test.docx"
        self._make_docx(f, ["Hello", "World"])
        result = parse_docx(f)
        assert result.page_count == 1
        assert "Hello" in result.full_text
        assert "World" in result.full_text

    def test_chinese_paragraphs(self, tmp_path):
        f = tmp_path / "cn.docx"
        self._make_docx(f, ["第一段", "第二段", "第三段"])
        result = parse_docx(f)
        assert "第一段" in result.full_text
        assert "第三段" in result.full_text

    def test_empty_paragraphs_filtered(self, tmp_path):
        f = tmp_path / "gaps.docx"
        self._make_docx(f, ["有内容", "", "  ", "也有内容"])
        result = parse_docx(f)
        assert "有内容" in result.full_text
        assert "也有内容" in result.full_text


# ── parse_file dispatch ──────────────────────────────────────────────────

class TestParseFile:
    def test_dispatch_txt(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("dispatch test", encoding="utf-8")
        result = parse_file(f, "txt")
        assert isinstance(result, ParsedDocument)
        assert "dispatch test" in result.full_text

    def test_unsupported_type(self, tmp_path):
        f = tmp_path / "test.xyz"
        f.write_text("data", encoding="utf-8")
        with pytest.raises(ValueError, match="No parser for file type"):
            parse_file(f, "xyz")
