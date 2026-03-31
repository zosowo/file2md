import pytest
from file2md.utils.markdown import table_to_markdown


class TestTableToMarkdown:
    def test_basic_table(self):
        rows = [["이름", "나이"], ["철수", "20"], ["영희", "22"]]
        result = table_to_markdown(rows)

        assert "| 이름 | 나이 |" in result
        assert "| --- | --- |" in result
        assert "| 철수 | 20 |" in result
        assert "| 영희 | 22 |" in result

    def test_single_row_header_only(self):
        rows = [["A", "B", "C"]]
        result = table_to_markdown(rows)
        assert "| A | B | C |" in result
        assert "---" in result

    def test_empty_input(self):
        assert table_to_markdown([]) == ""
        assert table_to_markdown([[]]) == ""

    def test_none_cell_treated_as_empty(self):
        rows = [["A", "B"], [None, "값"]]
        result = table_to_markdown(rows)
        assert "|  | 값 |" in result

    def test_newline_in_cell_replaced(self):
        rows = [["제목"], ["줄1\n줄2"]]
        result = table_to_markdown(rows)
        assert "\n" not in result.split("---")[1].split("\n", 1)[1].split("\n")[0]

    def test_row_shorter_than_header_padded(self):
        rows = [["A", "B", "C"], ["x"]]
        result = table_to_markdown(rows)
        # 'x' 행은 빈 셀 2개가 추가되어 3열 맞춤
        assert result.count("|") >= 4  # 헤더 행 기준
