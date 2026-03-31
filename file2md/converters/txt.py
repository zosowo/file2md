from pathlib import Path

from file2md.core.base import BaseConverter, ConvertResult


class TxtConverter(BaseConverter):
    """
    .txt 파일을 마크다운으로 변환한다.

    변환 규칙:
        - 텍스트를 그대로 보존한다.
        - 파일명을 H1 제목으로 추가한다.
        - 인코딩은 UTF-8 → EUC-KR → CP1252 순서로 자동 감지한다.
    """

    ENCODINGS = ("utf-8-sig", "utf-8", "euc-kr", "cp1252", "latin-1")

    @property
    def supported_formats(self) -> tuple:
        return ("txt",)

    def convert(self, source: str) -> ConvertResult:
        path = Path(source)

        if not path.exists():
            return ConvertResult.failure(source, "txt", f"파일을 찾을 수 없습니다: {source}")

        if not path.is_file():
            return ConvertResult.failure(source, "txt", f"파일이 아닙니다: {source}")

        # 인코딩 자동 감지
        text, used_encoding = self._read_with_encoding(path)
        if text is None:
            return ConvertResult.failure(source, "txt", "파일 인코딩을 감지할 수 없습니다.")

        metadata = {
            "title": path.stem,
            "source": str(path.resolve()),
            "format": "txt",
            "encoding": used_encoding,
        }
        frontmatter = self.build_frontmatter(metadata)

        # 파일명을 H1 제목으로, 본문은 그대로
        body = f"# {path.stem}\n\n{text}"
        markdown = frontmatter + self.sanitize(body)

        return ConvertResult(
            markdown_content=markdown,
            source=source,
            format="txt",
        )

    def _read_with_encoding(self, path: Path) -> tuple[str | None, str | None]:
        """여러 인코딩을 순서대로 시도해 파일을 읽는다."""
        for enc in self.ENCODINGS:
            try:
                text = path.read_text(encoding=enc)
                return text, enc
            except (UnicodeDecodeError, LookupError):
                continue
        return None, None
