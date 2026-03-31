"""
pytest 공통 픽스처

테스트용 샘플 파일은 tests/fixtures/samples/ 에 위치한다.
실제 파일이 없는 경우 pytest.skip()으로 건너뛴다.
"""

import pytest
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "samples"


def fixture_path(filename: str) -> Path:
    return FIXTURES_DIR / filename


# ── 간단한 샘플 파일을 tmp_path에 동적 생성 ──────────────

@pytest.fixture
def sample_txt(tmp_path) -> Path:
    f = tmp_path / "sample.txt"
    f.write_text("Hello, World!\n한글 텍스트 테스트입니다.", encoding="utf-8")
    return f


@pytest.fixture
def empty_txt(tmp_path) -> Path:
    f = tmp_path / "empty.txt"
    f.write_text("", encoding="utf-8")
    return f


@pytest.fixture
def sample_html(tmp_path) -> Path:
    f = tmp_path / "sample.html"
    f.write_text(
        """<!DOCTYPE html>
<html>
<head><title>테스트 페이지</title></head>
<body>
  <h1>제목 1</h1>
  <h2>제목 2</h2>
  <p>단락 텍스트입니다. <strong>굵게</strong> <em>기울임</em></p>
  <table>
    <tr><th>이름</th><th>나이</th></tr>
    <tr><td>철수</td><td>20</td></tr>
    <tr><td>영희</td><td>22</td></tr>
  </table>
  <ul>
    <li>항목 1</li>
    <li>항목 2</li>
  </ul>
  <a href="https://example.com">링크 텍스트</a>
</body>
</html>""",
        encoding="utf-8",
    )
    return f
