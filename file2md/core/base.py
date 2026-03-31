from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ConvertResult:
    """변환 결과를 담는 데이터 클래스"""
    markdown_content: str
    source: str
    format: str
    success: bool = True
    error: Optional[str] = None
    page_count: Optional[int] = None
    table_count: Optional[int] = None
    image_count: Optional[int] = None
    converted_at: datetime = field(default_factory=datetime.now)

    def has_error(self) -> bool:
        return self.error is not None

    @classmethod
    def failure(cls, source: str, fmt: str, error: str) -> "ConvertResult":
        return cls(
            markdown_content="",
            source=source,
            format=fmt,
            success=False,
            error=error,
        )


class BaseConverter(ABC):
    """모든 컨버터가 상속하는 추상 기반 클래스"""

    @abstractmethod
    def convert(self, source: str) -> ConvertResult:
        """
        source를 마크다운으로 변환한다.

        Args:
            source: 파일 경로 또는 URL 문자열

        Returns:
            ConvertResult: 변환 결과
        """

    @property
    @abstractmethod
    def supported_formats(self) -> tuple:
        """이 컨버터가 처리할 수 있는 확장자 목록"""

    def can_handle(self, source: str) -> bool:
        """source를 이 컨버터가 처리할 수 있는지 확인"""
        from pathlib import Path
        ext = Path(source).suffix.lower().lstrip(".")
        return ext in self.supported_formats

    # ──────────────────────────────────────────────
    # 공통 헬퍼: 하위 클래스에서 재사용
    # ──────────────────────────────────────────────

    @staticmethod
    def build_frontmatter(metadata: dict) -> str:
        """딕셔너리를 YAML frontmatter 문자열로 변환"""
        lines = ["---"]
        for key, value in metadata.items():
            if isinstance(value, datetime):
                value = value.isoformat()
            lines.append(f"{key}: {value}")
        lines.append("---\n")
        return "\n".join(lines)

    @staticmethod
    def sanitize(text: str) -> str:
        """연속된 빈 줄을 최대 2줄로 정리"""
        import re
        return re.sub(r"\n{3,}", "\n\n", text).strip()
