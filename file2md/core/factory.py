from pathlib import Path

from file2md.core.base import BaseConverter


class ConverterFactory:
    """
    파일 확장자 또는 URL을 보고 적절한 컨버터를 반환하는 팩토리 클래스.

    새로운 형식을 지원하려면:
        1. BaseConverter를 상속한 새 컨버터 클래스 작성
        2. ConverterFactory._registry에 확장자:클래스 등록

    등록은 register() 클래스 메서드로도 가능하다.
    """

    # 확장자 → 컨버터 클래스 매핑 (지연 임포트로 순환 의존 방지)
    _registry: dict[str, type[BaseConverter]] = {}

    @classmethod
    def _ensure_registered(cls) -> None:
        """처음 호출될 때 기본 컨버터들을 등록한다."""
        if cls._registry:
            return

        from file2md.converters.txt import TxtConverter
        from file2md.converters.pdf import PdfConverter
        from file2md.converters.docx import DocxConverter
        from file2md.converters.excel import ExcelConverter
        from file2md.converters.html import HtmlConverter
        from file2md.converters.pptx import PptxConverter
        from file2md.converters.url import UrlConverter

        cls._registry = {
            "txt": TxtConverter,
            "pdf": PdfConverter,
            "docx": DocxConverter,
            "doc": DocxConverter,
            "xlsx": ExcelConverter,
            "xls": ExcelConverter,
            "html": HtmlConverter,
            "htm": HtmlConverter,
            "pptx": PptxConverter,
            "ppt": PptxConverter,
            "_url": UrlConverter,   # URL은 특수 키로 처리
        }

    @classmethod
    def register(cls, ext: str, converter_cls: type[BaseConverter]) -> None:
        """외부에서 새 컨버터를 등록할 때 사용"""
        cls._ensure_registered()
        cls._registry[ext.lower().lstrip(".")] = converter_cls

    @classmethod
    def get_converter(cls, source: str) -> BaseConverter:
        """
        source(파일 경로 또는 URL)에 맞는 컨버터 인스턴스를 반환한다.

        Raises:
            ValueError: 지원하지 않는 형식일 때
        """
        cls._ensure_registered()

        if source.startswith(("http://", "https://")):
            return cls._registry["_url"]()

        ext = Path(source).suffix.lower().lstrip(".")
        if ext not in cls._registry:
            supported = [k for k in cls._registry if not k.startswith("_")]
            raise ValueError(
                f"지원하지 않는 형식: '.{ext}'\n"
                f"지원 형식: {', '.join(sorted(supported))}"
            )

        return cls._registry[ext]()

    @classmethod
    def supported_formats(cls) -> list[str]:
        """현재 지원하는 확장자 목록"""
        cls._ensure_registered()
        return sorted(k for k in cls._registry if not k.startswith("_"))
