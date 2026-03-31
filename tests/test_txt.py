import pytest
from pathlib import Path

from file2md.converters.txt import TxtConverter


class TestTxtConverter:
    def setup_method(self):
        self.converter = TxtConverter()

    # ── supported_formats ──────────────────────────────
    def test_supported_formats(self):
        assert "txt" in self.converter.supported_formats

    def test_can_handle_txt(self):
        assert self.converter.can_handle("file.txt") is True

    def test_cannot_handle_pdf(self):
        assert self.converter.can_handle("file.pdf") is False

    # ── 정상 변환 ──────────────────────────────────────
    def test_basic_conversion(self, sample_txt):
        result = self.converter.convert(str(sample_txt))
        assert result.success is True
        assert "Hello, World!" in result.markdown_content

    def test_korean_preserved(self, sample_txt):
        result = self.converter.convert(str(sample_txt))
        assert result.success is True
        assert "한글" in result.markdown_content

    def test_filename_as_heading(self, sample_txt):
        result = self.converter.convert(str(sample_txt))
        assert "# sample" in result.markdown_content

    def test_frontmatter_included(self, sample_txt):
        result = self.converter.convert(str(sample_txt))
        assert result.markdown_content.startswith("---")
        assert "format: txt" in result.markdown_content

    def test_format_field(self, sample_txt):
        result = self.converter.convert(str(sample_txt))
        assert result.format == "txt"

    # ── 경계 케이스 ────────────────────────────────────
    def test_empty_file(self, empty_txt):
        result = self.converter.convert(str(empty_txt))
        assert result.success is True

    def test_multiline_text(self, tmp_path):
        f = tmp_path / "multi.txt"
        f.write_text("line1\nline2\nline3", encoding="utf-8")
        result = self.converter.convert(str(f))
        assert result.success is True
        assert "line1" in result.markdown_content
        assert "line3" in result.markdown_content

    def test_encoding_euc_kr(self, tmp_path):
        f = tmp_path / "euckr.txt"
        f.write_bytes("안녕하세요".encode("euc-kr"))
        result = self.converter.convert(str(f))
        assert result.success is True

    # ── 오류 케이스 ────────────────────────────────────
    def test_file_not_found(self):
        result = self.converter.convert("/nonexistent/path/file.txt")
        assert result.success is False
        assert result.error is not None

    def test_directory_as_input(self, tmp_path):
        result = self.converter.convert(str(tmp_path))
        assert result.success is False
