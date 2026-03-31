# file2md

다양한 파일 형식을 마크다운(.md)으로 변환하는 Python 라이브러리입니다.
RAG(Retrieval-Augmented Generation) 시스템에서 문서를 LLM에 공급하기 위한 전처리 용도로 설계되었습니다.

## 지원 형식

| 형식 | 확장자 | 의존 라이브러리 |
|------|--------|----------------|
| 텍스트 | `.txt` | 없음 (built-in) |
| PDF | `.pdf` | `pdfplumber` |
| Word | `.docx`, `.doc` | `python-docx` |
| Excel | `.xlsx`, `.xls` | `pandas`, `openpyxl` |
| HTML | `.html`, `.htm` | `beautifulsoup4` |
| PowerPoint | `.pptx`, `.ppt` | `python-pptx` |
| URL | `http://`, `https://` | `requests`, `beautifulsoup4` |

---

## 폴더 구조

```
parser/                        ← 프로젝트 루트
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── setup.py                   ← pip install -e . 로 패키지 설치
│
├── file2md/                   ← 패키지 루트 (import file2md)
│   ├── __init__.py            ← 공개 API: convert(), convert_batch()
│   ├── __main__.py            ← python -m file2md 진입점
│   ├── cli.py                 ← CLI argparse 정의
│   │
│   ├── core/
│   │   ├── base.py            ← BaseConverter(ABC), ConvertResult
│   │   └── factory.py         ← ConverterFactory (확장자→컨버터 라우팅)
│   │
│   ├── converters/
│   │   ├── txt.py             ← TxtConverter
│   │   ├── pdf.py             ← PdfConverter
│   │   ├── docx.py            ← DocxConverter
│   │   ├── excel.py           ← ExcelConverter
│   │   ├── html.py            ← HtmlConverter
│   │   ├── pptx.py            ← PptxConverter
│   │   └── url.py             ← UrlConverter (HtmlConverter 상속)
│   │
│   └── utils/
│       └── markdown.py        ← table_to_markdown() 등 공통 유틸
│
└── tests/
    ├── conftest.py            ← pytest 픽스처
    ├── fixtures/samples/      ← 테스트용 샘플 파일 보관 위치
    ├── test_txt.py
    ├── test_html.py
    ├── test_markdown_utils.py
    ├── test_factory.py
    └── test_api.py
```

---

## 설치

### 1. 의존성 설치

```bash
cd parser
pip install -r requirements.txt
```

### 2. 패키지로 설치 (다른 프로젝트에서 import 하려면)

```bash
cd parser
pip install -e .
```

`-e`(editable) 옵션으로 설치하면 소스 코드를 수정해도 재설치 없이 즉시 반영됩니다.

> **import가 안 될 때 확인사항**
> - `pip install -e .` 를 `parser/` 디렉토리에서 실행했는지 확인
> - `setup.py`가 있는 위치와 같은 디렉토리인지 확인
> - `python -c "import file2md; print(file2md.__file__)"` 으로 경로 확인

---

## CLI 사용법

### 단일 파일 변환

```bash
# PDF → output/report.md
python -m file2md report.pdf -o output/report.md

# 출력 경로 생략 시 같은 위치에 .md 파일 생성
python -m file2md report.pdf
# → report.md 생성

# 저장 없이 터미널 출력
python -m file2md report.pdf --no-save
```

### URL 변환

```bash
python -m file2md --url https://example.com
python -m file2md --url https://example.com -o page.md
```

### 배치 변환 (여러 파일 한번에)

```bash
# 파일 목록 나열
python -m file2md --batch a.docx b.xlsx c.pptx

# 출력 디렉토리 지정
python -m file2md --batch *.pdf --output-dir ./output/

# 병렬 처리 수 조절 (기본값 4)
python -m file2md --batch *.pdf --output-dir ./output/ --workers 8
```

### 기타 옵션

```bash
# 변환 결과 상세 출력
python -m file2md report.pdf -v

# 지원 형식 목록 확인
python -m file2md --formats
```

---

## Python API 사용법

### 기본 사용

```python
from file2md import convert

# 파일 변환 (같은 경로에 .md 파일 저장)
result = convert("report.pdf")

# 성공 여부 확인
if result.success:
    print(result.markdown_content)
else:
    print(f"오류: {result.error}")
```

### 저장 경로 지정

```python
from file2md import convert

result = convert("report.pdf", output_path="./output/report.md")
```

### 파일 저장 없이 마크다운만 가져오기

```python
from file2md import convert

result = convert("data.xlsx", save_file=False)
markdown_text = result.markdown_content
```

### URL 변환

```python
from file2md import convert

result = convert("https://docs.python.org/3/", save_file=False)
print(result.markdown_content[:500])
```

### 배치 변환

```python
from file2md import convert_batch

sources = ["report.pdf", "data.xlsx", "slide.pptx"]
results = convert_batch(sources, output_dir="./output/", workers=4)

for src, result in zip(sources, results):
    status = "성공" if result.success else f"실패: {result.error}"
    print(f"{src} → {status}")
```

### RAG 파이프라인 연동 예시

```python
from file2md import convert

def load_documents(file_paths: list[str]) -> list[dict]:
    """파일들을 읽어 RAG용 문서 리스트로 반환"""
    docs = []
    for path in file_paths:
        result = convert(path, save_file=False)
        if result.success:
            docs.append({
                "content": result.markdown_content,
                "metadata": {
                    "source": result.source,
                    "format": result.format,
                    "pages": result.page_count,
                    "tables": result.table_count,
                }
            })
    return docs

# 사용
docs = load_documents(["report.pdf", "data.xlsx", "slide.pptx"])
# → LangChain, LlamaIndex 등에 전달
```

### ConvertResult 구조

```python
@dataclass
class ConvertResult:
    markdown_content: str    # 변환된 마크다운 내용
    source: str              # 입력 파일 경로 또는 URL
    format: str              # 'txt', 'pdf', 'docx', 'xlsx', 'html', 'pptx', 'url'
    success: bool            # 변환 성공 여부
    error: str | None        # 실패 시 오류 메시지
    page_count: int | None   # PDF, PPTX의 페이지 수
    table_count: int | None  # 감지된 테이블 수
    image_count: int | None  # 감지된 이미지 수
    converted_at: datetime   # 변환 시각
```

---

## 마크다운 출력 형식

모든 변환 결과는 YAML frontmatter로 시작합니다.

```markdown
---
title: 문서 제목
source: /path/to/file.pdf
format: pdf
pages: 10
---

# 본문 내용...
```

---

## 새로운 파일 형식 추가하기

1. `file2md/converters/` 에 새 파일 생성

```python
# file2md/converters/csv.py
from file2md.core.base import BaseConverter, ConvertResult
from file2md.utils.markdown import table_to_markdown
from pathlib import Path

class CsvConverter(BaseConverter):
    @property
    def supported_formats(self) -> tuple:
        return ("csv",)

    def convert(self, source: str) -> ConvertResult:
        import csv
        path = Path(source)
        with open(path, encoding="utf-8") as f:
            rows = list(csv.reader(f))
        markdown = table_to_markdown(rows)
        return ConvertResult(
            markdown_content=markdown,
            source=source,
            format="csv",
        )
```

2. `ConverterFactory`에 등록

```python
# file2md/core/factory.py 의 _ensure_registered() 안에 추가
from file2md.converters.csv import CsvConverter
cls._registry["csv"] = CsvConverter
```

또는 외부에서 동적 등록:

```python
from file2md.core.factory import ConverterFactory
from my_converters import CsvConverter

ConverterFactory.register("csv", CsvConverter)
```

---

## 테스트 실행

```bash
cd parser

# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=file2md --cov-report=term-missing

# 특정 파일만
pytest tests/test_txt.py -v

# 특정 테스트만
pytest tests/test_txt.py::TestTxtConverter::test_korean_preserved -v
```

---

## 아키텍처 요약

```
convert("file.pdf")
    │
    ▼
ConverterFactory.get_converter("file.pdf")
    │  확장자 "pdf" 감지
    ▼
PdfConverter 인스턴스 반환
    │
    ▼
PdfConverter.convert("file.pdf")
    │  pdfplumber로 텍스트/테이블 추출
    │  frontmatter 생성
    │  sanitize (빈 줄 정리)
    ▼
ConvertResult(markdown_content=..., success=True, ...)
```

- **BaseConverter**: 모든 컨버터의 추상 기반 클래스. `convert()`, `supported_formats` 구현 강제
- **ConverterFactory**: 확장자 → 컨버터 매핑. 새 형식 등록도 담당
- **ConvertResult**: 변환 결과를 담는 데이터 클래스
- **UrlConverter**: `HtmlConverter`를 상속. HTTP 다운로드 후 HTML 파싱 로직 재사용
