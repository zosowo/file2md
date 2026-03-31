from pathlib import Path

from file2md.core.base import BaseConverter, ConvertResult
from file2md.utils.markdown import table_to_markdown


class ExcelConverter(BaseConverter):
    """
    .xlsx / .xls 파일을 마크다운으로 변환한다.

    변환 규칙:
        - 시트별로 ## 시트명 섹션을 만든다.
        - 각 시트의 데이터를 마크다운 테이블로 변환한다.
        - 빈 시트는 *(빈 시트)* 메시지를 삽입한다.
        - 병합된 셀은 첫 번째 셀 값을 사용한다.

    의존성:
        pip install openpyxl pandas tabulate
        (tabulate는 pandas의 to_markdown()에 필요)
    """

    @property
    def supported_formats(self) -> tuple:
        return ("xlsx", "xls")

    def convert(self, source: str) -> ConvertResult:
        path = Path(source)

        if not path.exists():
            return ConvertResult.failure(source, "xlsx", f"파일을 찾을 수 없습니다: {source}")

        try:
            import pandas as pd
        except ImportError:
            return ConvertResult.failure(source, "xlsx", "pandas가 설치되어 있지 않습니다. pip install pandas openpyxl")

        try:
            excel = pd.ExcelFile(path, engine="openpyxl")
        except Exception as e:
            return ConvertResult.failure(source, "xlsx", f"파일을 열 수 없습니다: {e}")

        metadata = {
            "title": path.stem,
            "source": str(path.resolve()),
            "format": "xlsx",
            "sheets": len(excel.sheet_names),
        }
        frontmatter = self.build_frontmatter(metadata)

        parts: list[str] = []
        total_tables = 0

        for sheet_name in excel.sheet_names:
            parts.append(f"\n## {sheet_name}\n")

            try:
                df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
            except Exception as e:
                parts.append(f"*(시트를 읽을 수 없습니다: {e})*\n")
                continue

            if df.empty:
                parts.append("*(빈 시트)*\n")
                continue

            # NaN을 빈 문자열로 치환
            df = df.fillna("")

            # 헤더 + 행 데이터를 직접 변환 (tabulate 의존성 제거)
            rows = [list(df.columns.astype(str))]
            for _, row in df.iterrows():
                rows.append([str(v) for v in row])

            md_table = table_to_markdown(rows)
            if md_table:
                parts.append(md_table)
                total_tables += 1

        markdown = frontmatter + self.sanitize("\n".join(parts))

        return ConvertResult(
            markdown_content=markdown,
            source=source,
            format="xlsx",
            table_count=total_tables,
        )
