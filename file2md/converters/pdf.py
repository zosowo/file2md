from pathlib import Path

from file2md.core.base import BaseConverter, ConvertResult
from file2md.utils.markdown import table_to_markdown


class PdfConverter(BaseConverter):
    """
    .pdf 파일을 마크다운으로 변환한다.

    변환 규칙:
        - 페이지별로 ## Page N 섹션을 만든다.
        - 각 페이지에서 텍스트를 추출한다.
        - 테이블이 감지되면 마크다운 테이블로 변환한다.
        - 스캔된 PDF(텍스트 없음)는 경고 메시지를 삽입한다.
        - 암호화된 PDF는 에러를 반환한다.

    의존성:
        pip install pdfplumber
    """

    @property
    def supported_formats(self) -> tuple:
        return ("pdf",)

    def convert(self, source: str) -> ConvertResult:
        path = Path(source)

        if not path.exists():
            return ConvertResult.failure(source, "pdf", f"파일을 찾을 수 없습니다: {source}")

        try:
            import pdfplumber
        except ImportError:
            return ConvertResult.failure(source, "pdf", "pdfplumber가 설치되어 있지 않습니다. pip install pdfplumber")

        try:
            return self._convert(path, pdfplumber)
        except Exception as e:
            return ConvertResult.failure(source, "pdf", str(e))

    def _convert(self, path: Path, pdfplumber) -> ConvertResult:
        source = str(path)
        parts: list[str] = []
        total_tables = 0
        total_images = 0

        with pdfplumber.open(path) as pdf:
            # 암호화 감지
            if pdf.doc.is_encrypted:
                return ConvertResult.failure(source, "pdf", "암호화된 PDF입니다. 비밀번호 해제 후 다시 시도하세요.")

            total_pages = len(pdf.pages)

            # 메타데이터 추출
            raw_meta = pdf.metadata or {}
            metadata = {
                "title": raw_meta.get("Title") or path.stem,
                "author": raw_meta.get("Author") or "",
                "source": str(path.resolve()),
                "format": "pdf",
                "pages": total_pages,
            }
            # 빈 값 제거
            metadata = {k: v for k, v in metadata.items() if v != ""}
            frontmatter = self.build_frontmatter(metadata)

            for page_num, page in enumerate(pdf.pages, start=1):
                parts.append(f"\n## Page {page_num}\n")

                # 1. 테이블 추출 (텍스트보다 먼저 처리해 중복 방지)
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        md_table = table_to_markdown(table)
                        if md_table:
                            parts.append(md_table)
                    total_tables += len(tables)

                # 2. 텍스트 추출
                text = page.extract_text()
                if text and text.strip():
                    parts.append(text.strip())
                elif not tables:
                    parts.append("*(텍스트를 추출할 수 없습니다 — 스캔된 이미지일 수 있습니다)*")

                # 3. 이미지 개수 집계
                total_images += len(page.images)

        markdown = frontmatter + self.sanitize("\n".join(parts))

        return ConvertResult(
            markdown_content=markdown,
            source=source,
            format="pdf",
            page_count=total_pages,
            table_count=total_tables,
            image_count=total_images,
        )
