"""Unit tests for parse_html."""
import pytest

from app.services.parser import parse_file, parse_html

pytestmark = pytest.mark.unit


ARTICLE_HTML = b"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>How to write a knowledge base</title>
</head>
<body>
  <header><nav>Home | About</nav></header>
  <main>
    <article>
      <h1>How to write a knowledge base</h1>
      <p>Building a great knowledge base starts with collecting the right sources.
      You should always cite authoritative documentation and cross-check claims.</p>
      <p>Chunking strategy matters: a sliding window with modest overlap preserves
      local context while keeping chunks embedding-friendly.</p>
      <p>Finally, retrieval quality improves when you embed both the question
      and the candidate passages with the same model.</p>
    </article>
  </main>
  <footer><p>(c) 2026 Example Corp</p></footer>
  <script>window.analytics=true;</script>
</body>
</html>"""


class TestParseHtml:
    def test_extracts_main_article_text(self, tmp_path):
        f = tmp_path / "page.html"
        f.write_bytes(ARTICLE_HTML)
        result = parse_html(f)
        assert result.page_count == 1
        text = result.full_text.lower()
        assert "knowledge base" in text
        assert "chunking strategy" in text
        # Boilerplate (nav / scripts) should not leak in.
        assert "home | about" not in text
        assert "window.analytics" not in text

    def test_empty_page_returns_empty_text(self, tmp_path):
        f = tmp_path / "empty.html"
        f.write_bytes(b"<html><body></body></html>")
        result = parse_html(f)
        assert result.page_count == 1
        assert result.full_text.strip() == ""

    def test_dispatch_via_parse_file(self, tmp_path):
        f = tmp_path / "page.html"
        f.write_bytes(ARTICLE_HTML)
        result = parse_file(f, "html")
        assert "chunking strategy" in result.full_text.lower()

    def test_fallback_handles_plain_body_only(self, tmp_path):
        # Page without <article>/<main> — trafilatura may return None; fallback
        # should pull body text via BeautifulSoup.
        raw = b"""<html><body>
            <div>just some words sitting in a plain div here.</div>
        </body></html>"""
        f = tmp_path / "plain.html"
        f.write_bytes(raw)
        result = parse_html(f)
        assert "just some words" in result.full_text.lower()
