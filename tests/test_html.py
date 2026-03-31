import pytest

from file2md.converters.html import HtmlConverter


class TestHtmlConverter:
    def setup_method(self):
        self.converter = HtmlConverter()

    # ── 정상 변환 ──────────────────────────────────────
    def test_basic_conversion(self, sample_html):
        result = self.converter.convert(str(sample_html))
        assert result.success is True
        assert len(result.markdown_content) > 0

    def test_title_extraction(self, sample_html):
        result = self.converter.convert(str(sample_html))
        assert "테스트 페이지" in result.markdown_content

    def test_headings_converted(self, sample_html):
        result = self.converter.convert(str(sample_html))
        assert "# 제목 1" in result.markdown_content
        assert "## 제목 2" in result.markdown_content

    def test_paragraph_extracted(self, sample_html):
        result = self.converter.convert(str(sample_html))
        assert "단락 텍스트" in result.markdown_content

    def test_table_converted(self, sample_html):
        result = self.converter.convert(str(sample_html))
        assert result.table_count == 1
        assert "|" in result.markdown_content
        assert "이름" in result.markdown_content
        assert "철수" in result.markdown_content

    def test_link_converted(self, sample_html):
        result = self.converter.convert(str(sample_html))
        assert "[링크 텍스트](https://example.com)" in result.markdown_content

    def test_list_converted(self, sample_html):
        result = self.converter.convert(str(sample_html))
        assert "- 항목 1" in result.markdown_content

    def test_bold_italic(self, tmp_path):
        f = tmp_path / "bold.html"
        f.write_text("<p><strong>굵게</strong> <em>기울임</em></p>", encoding="utf-8")
        result = self.converter.convert(str(f))
        assert "**굵게**" in result.markdown_content
        assert "*기울임*" in result.markdown_content

    def test_frontmatter_included(self, sample_html):
        result = self.converter.convert(str(sample_html))
        assert result.markdown_content.startswith("---")
        assert "format: html" in result.markdown_content

    def test_script_style_removed(self, tmp_path):
        f = tmp_path / "scripts.html"
        f.write_text(
            "<html><body><script>alert(1)</script><p>본문</p></body></html>",
            encoding="utf-8",
        )
        result = self.converter.convert(str(f))
        assert "alert" not in result.markdown_content
        assert "본문" in result.markdown_content

    # ── 오류 케이스 ────────────────────────────────────
    def test_file_not_found(self):
        result = self.converter.convert("/nonexistent.html")
        assert result.success is False
