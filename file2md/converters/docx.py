from pathlib import Path

from file2md.core.base import BaseConverter, ConvertResult
from file2md.utils.markdown import table_to_markdown


class DocxConverter(BaseConverter):
    """
    .docx / .doc 파일을 마크다운으로 변환한다.

    변환 규칙:
        - Heading 1~6 스타일 → # ~ ######
        - 일반 단락 → 텍스트 줄
        - 테이블 → 마크다운 테이블
        - 굵게/기울임 인라인 서식 보존
        - 문서 속성(제목, 작성자)을 frontmatter에 포함

    의존성:
        pip install python-docx
    """

    @property
    def supported_formats(self) -> tuple:
        return ("docx", "doc")

    def convert(self, source: str) -> ConvertResult:
        path = Path(source)

        if not path.exists():
            return ConvertResult.failure(source, "docx", f"파일을 찾을 수 없습니다: {source}")

        try:
            from docx import Document
        except ImportError:
            return ConvertResult.failure(source, "docx", "python-docx가 설치되어 있지 않습니다. pip install python-docx")

        try:
            doc = Document(str(path))
        except Exception as e:
            return ConvertResult.failure(source, "docx", f"파일을 열 수 없습니다: {e}")

        # 문서 속성 추출
        props = doc.core_properties
        metadata = {
            "title": props.title or path.stem,
            "author": props.author or "",
            "source": str(path.resolve()),
            "format": "docx",
        }
        metadata = {k: v for k, v in metadata.items() if v != ""}
        frontmatter = self.build_frontmatter(metadata)

        parts: list[str] = []
        table_count = 0

        # python-docx의 body는 단락과 테이블이 섞인 순서를 보존하지 않는다.
        # XML을 직접 순회해 원본 순서를 유지한다.
        from docx.oxml.ns import qn

        for child in doc.element.body:
            tag = child.tag

            if tag == qn("w:p"):
                # 단락 처리
                from docx.text.paragraph import Paragraph
                para = Paragraph(child, doc)
                md = self._paragraph_to_md(para)
                if md:
                    parts.append(md)

            elif tag == qn("w:tbl"):
                # 테이블 처리
                from docx.table import Table
                table = Table(child, doc)
                rows = []
                for row in table.rows:
                    cells = [cell.text.strip() for cell in row.cells]
                    rows.append(cells)
                md_table = table_to_markdown(rows)
                if md_table:
                    parts.append(md_table)
                    table_count += 1

        markdown = frontmatter + self.sanitize("\n".join(parts))

        return ConvertResult(
            markdown_content=markdown,
            source=source,
            format="docx",
            table_count=table_count,
        )

    @staticmethod
    def _paragraph_to_md(para) -> str:
        """단락 객체를 마크다운 문자열로 변환한다."""
        style_name = para.style.name if para.style else ""

        # 헤딩 처리
        if "Heading" in style_name:
            # 'Heading 1' → 1, 'Heading 2' → 2
            parts = style_name.split()
            level = int(parts[-1]) if parts[-1].isdigit() else 1
            level = min(level, 6)
            text = para.text.strip()
            return f"{'#' * level} {text}" if text else ""

        # 일반 단락: 인라인 서식 처리
        result = []
        for run in para.runs:
            text = run.text
            if not text:
                continue
            if run.bold and run.italic:
                text = f"***{text}***"
            elif run.bold:
                text = f"**{text}**"
            elif run.italic:
                text = f"*{text}*"
            result.append(text)

        return "".join(result)
