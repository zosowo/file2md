import pytest
from file2md.core.factory import ConverterFactory
from file2md.converters.txt import TxtConverter
from file2md.converters.html import HtmlConverter
from file2md.converters.url import UrlConverter


class TestConverterFactory:
    def test_txt_returns_txt_converter(self):
        converter = ConverterFactory.get_converter("file.txt")
        assert isinstance(converter, TxtConverter)

    def test_html_returns_html_converter(self):
        converter = ConverterFactory.get_converter("page.html")
        assert isinstance(converter, HtmlConverter)

    def test_htm_returns_html_converter(self):
        converter = ConverterFactory.get_converter("page.htm")
        assert isinstance(converter, HtmlConverter)

    def test_url_returns_url_converter(self):
        converter = ConverterFactory.get_converter("https://example.com")
        assert isinstance(converter, UrlConverter)

    def test_http_url_returns_url_converter(self):
        converter = ConverterFactory.get_converter("http://example.com")
        assert isinstance(converter, UrlConverter)

    def test_unsupported_format_raises_value_error(self):
        with pytest.raises(ValueError, match="지원하지 않는 형식"):
            ConverterFactory.get_converter("file.xyz")

    def test_supported_formats_not_empty(self):
        formats = ConverterFactory.supported_formats()
        assert len(formats) > 0
        assert "txt" in formats
        assert "pdf" in formats

    def test_custom_converter_registration(self):
        from file2md.core.base import BaseConverter, ConvertResult

        class FakeConverter(BaseConverter):
            @property
            def supported_formats(self):
                return ("fake",)

            def convert(self, source):
                return ConvertResult(markdown_content="fake", source=source, format="fake")

        ConverterFactory.register("fake", FakeConverter)
        converter = ConverterFactory.get_converter("file.fake")
        assert isinstance(converter, FakeConverter)
