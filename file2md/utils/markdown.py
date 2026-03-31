"""마크다운 변환에 공통으로 쓰이는 유틸 함수들"""


def table_to_markdown(rows: list[list[str]]) -> str:
    """
    2차원 리스트를 마크다운 테이블로 변환한다.

    Args:
        rows: 행(row) 리스트. 첫 번째 행이 헤더로 사용된다.

    Returns:
        마크다운 테이블 문자열. rows가 비어있으면 빈 문자열 반환.

    Example:
        >>> table_to_markdown([["이름", "나이"], ["철수", "20"]])
        '| 이름 | 나이 |\\n| --- | --- |\\n| 철수 | 20 |\\n'
    """
    if not rows or not rows[0]:
        return ""

    def _clean(cell) -> str:
        return str(cell).strip().replace("\n", " ") if cell is not None else ""

    header = rows[0]
    md = "| " + " | ".join(_clean(c) for c in header) + " |\n"
    md += "| " + " | ".join("---" for _ in header) + " |\n"

    for row in rows[1:]:
        # 열 수가 헤더보다 적을 경우 빈 셀로 채운다
        padded = list(row) + [""] * (len(header) - len(row))
        md += "| " + " | ".join(_clean(c) for c in padded[: len(header)]) + " |\n"

    return md
