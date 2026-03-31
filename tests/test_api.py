"""
file2md 공개 API 통합 테스트
"""

import pytest
from pathlib import Path
from file2md import convert, convert_batch, ConvertResult


class TestConvertFunction:
    def test_returns_convert_result(self, sample_txt):
        result = convert(str(sample_txt), save_file=False)
        assert isinstance(result, ConvertResult)

    def test_success_flag(self, sample_txt):
        result = convert(str(sample_txt), save_file=False)
        assert result.success is True

    def test_markdown_content_not_empty(self, sample_txt):
        result = convert(str(sample_txt), save_file=False)
        assert len(result.markdown_content) > 0

    def test_save_file_creates_md(self, sample_txt, tmp_path):
        output = tmp_path / "out.md"
        result = convert(str(sample_txt), output_path=str(output), save_file=True)
        assert result.success is True
        assert output.exists()
        assert output.read_text(encoding="utf-8") == result.markdown_content

    def test_no_save_does_not_create_file(self, sample_txt):
        expected_output = sample_txt.with_suffix(".md")
        result = convert(str(sample_txt), save_file=False)
        assert result.success is True
        assert not expected_output.exists()

    def test_unsupported_format_raises(self, tmp_path):
        f = tmp_path / "data.xyz"
        f.write_text("content")
        with pytest.raises(ValueError):
            convert(str(f), save_file=False)

    def test_html_conversion(self, sample_html):
        result = convert(str(sample_html), save_file=False)
        assert result.success is True
        assert result.format == "html"


class TestConvertBatch:
    def test_batch_returns_list(self, sample_txt, sample_html):
        results = convert_batch(
            [str(sample_txt), str(sample_html)],
            workers=2,
        )
        assert isinstance(results, list)
        assert len(results) == 2

    def test_batch_all_convert_result(self, sample_txt, sample_html):
        results = convert_batch([str(sample_txt), str(sample_html)], workers=2)
        assert all(isinstance(r, ConvertResult) for r in results)

    def test_batch_order_preserved(self, sample_txt, sample_html):
        """결과 순서가 입력 순서와 일치해야 한다."""
        sources = [str(sample_txt), str(sample_html)]
        results = convert_batch(sources, workers=2)
        assert results[0].format == "txt"
        assert results[1].format == "html"

    def test_batch_with_output_dir(self, sample_txt, sample_html, tmp_path):
        out_dir = tmp_path / "batch_output"
        out_dir.mkdir()
        results = convert_batch(
            [str(sample_txt), str(sample_html)],
            output_dir=str(out_dir),
            workers=2,
        )
        assert all(r.success for r in results)
        md_files = list(out_dir.glob("*.md"))
        assert len(md_files) == 2
