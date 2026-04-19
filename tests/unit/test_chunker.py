"""Unit tests for text chunker — sliding window with overlap."""
import pytest

from app.services.chunker import ChunkResult, chunk_document
from app.services.parser import ParsedDocument, ParsedPage

pytestmark = pytest.mark.unit


def _make_doc(text: str, page_number: int = 1) -> ParsedDocument:
    return ParsedDocument(pages=[ParsedPage(page_number=page_number, text=text)])


def _make_multi_page_doc(pages: list[str]) -> ParsedDocument:
    return ParsedDocument(
        pages=[ParsedPage(page_number=i + 1, text=t) for i, t in enumerate(pages)]
    )


class TestBasicChunking:
    def test_short_text_single_chunk(self):
        doc = _make_doc("Hello World")
        chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 1
        assert chunks[0].content == "Hello World"
        assert chunks[0].chunk_index == 0
        assert chunks[0].page_number == 1

    def test_long_text_produces_multiple_chunks(self):
        text = "A" * 1000
        doc = _make_doc(text)
        chunks = chunk_document(doc, chunk_size=200, chunk_overlap=30)
        assert len(chunks) > 1
        # All content should be covered
        combined = "".join(c.content for c in chunks)
        assert len(combined) >= len(text.strip())

    def test_chunk_indices_sequential(self):
        text = "Word. " * 200
        doc = _make_doc(text)
        chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))


class TestOverlap:
    def test_chunks_overlap(self):
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 5  # 130 chars
        doc = _make_doc(text)
        chunks = chunk_document(doc, chunk_size=50, chunk_overlap=10)
        assert len(chunks) >= 2
        # Check that the end of chunk N overlaps with start of chunk N+1
        for i in range(len(chunks) - 1):
            tail = chunks[i].content[-10:]
            head = chunks[i + 1].content[:15]
            # There should be some shared characters
            assert any(c in head for c in tail)


class TestBoundaryBreaking:
    def test_breaks_at_newline(self):
        text = "A" * 80 + "\n" + "B" * 80
        doc = _make_doc(text)
        chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
        # Should break at the newline rather than mid-word
        assert len(chunks) >= 2
        assert chunks[0].content.endswith("A")

    def test_breaks_at_chinese_period(self):
        text = "这是一段测试文本" * 10 + "。" + "这是另一段内容" * 10
        doc = _make_doc(text)
        chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
        assert len(chunks) >= 2


class TestMultiPage:
    def test_page_numbers_preserved(self):
        doc = _make_multi_page_doc(["Page 1 content here", "Page 2 content here"])
        chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 2
        assert chunks[0].page_number == 1
        assert chunks[1].page_number == 2

    def test_empty_page_skipped(self):
        doc = _make_multi_page_doc(["Content", "", "More content"])
        chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
        assert len(chunks) == 2
        page_nums = [c.page_number for c in chunks]
        assert 2 not in page_nums  # empty page skipped

    def test_index_continuous_across_pages(self):
        doc = _make_multi_page_doc(["A" * 300, "B" * 300])
        chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))


class TestCharOffsets:
    def test_offsets_cover_text(self):
        text = "Hello World! This is a test."
        doc = _make_doc(text)
        chunks = chunk_document(doc, chunk_size=500, chunk_overlap=0)
        assert len(chunks) == 1
        assert chunks[0].char_start == 0
        assert chunks[0].char_end == len(text)


class TestEdgeCases:
    def test_empty_document(self):
        doc = ParsedDocument(pages=[])
        chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
        assert chunks == []

    def test_whitespace_only_document(self):
        doc = _make_doc("   \n\n   ")
        chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
        assert chunks == []

    def test_invalid_chunk_size(self):
        doc = _make_doc("test")
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_document(doc, chunk_size=0, chunk_overlap=0)

    def test_overlap_exceeds_size(self):
        doc = _make_doc("test")
        with pytest.raises(ValueError, match="chunk_overlap must be less than"):
            chunk_document(doc, chunk_size=50, chunk_overlap=50)


class TestWithSampleContent:
    """Integration-style test with realistic document content."""

    def test_realistic_document(self, sample_txt_content):
        doc = _make_doc(sample_txt_content)
        chunks = chunk_document(doc, chunk_size=150, chunk_overlap=20)
        assert len(chunks) >= 3
        # All chunk contents should be non-empty
        assert all(c.content.strip() for c in chunks)
        # Indices are sequential
        assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
