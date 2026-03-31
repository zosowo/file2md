"""
file2md — 다양한 파일 형식을 마크다운으로 변환하는 라이브러리

공개 API:
    convert(source, output_path, save_file) -> ConvertResult
    convert_batch(sources, output_dir, workers) -> list[ConvertResult]

기본 사용법:
    from file2md import convert

    result = convert("report.pdf")
    print(result.markdown_content)
"""

from file2md.core.base import ConvertResult
from file2md.core.factory import ConverterFactory


def convert(
    source: str,
    output_path: str | None = None,
    save_file: bool = True,
) -> ConvertResult:
    """
    파일 경로 또는 URL을 마크다운으로 변환한다.

    Args:
        source: 파일 경로 또는 URL 문자열
        output_path: 저장할 .md 파일 경로.
                     None이면 source와 같은 디렉토리에 같은 이름으로 저장.
        save_file: True이면 변환 결과를 파일로 저장한다.

    Returns:
        ConvertResult: 변환 결과 객체.
                       result.success로 성공 여부 확인,
                       result.markdown_content로 마크다운 내용 접근.

    Raises:
        ValueError: 지원하지 않는 파일 형식일 때
    """
    converter = ConverterFactory.get_converter(source)
    result = converter.convert(source)

    if result.success and save_file:
        _save(result, source, output_path)

    return result


def convert_batch(
    sources: list[str],
    output_dir: str | None = None,
    workers: int = 4,
) -> list[ConvertResult]:
    """
    여러 파일/URL을 병렬로 변환한다.

    Args:
        sources: 파일 경로 또는 URL 목록
        output_dir: 변환 결과를 저장할 디렉토리.
                    None이면 각 파일과 같은 디렉토리에 저장.
        workers: 병렬 처리 스레드 수 (기본값: 4)

    Returns:
        list[ConvertResult]: 각 source에 대응하는 변환 결과 목록
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from pathlib import Path

    def _convert_one(src: str) -> ConvertResult:
        out = None
        if output_dir:
            stem = Path(src).stem if not src.startswith("http") else src.split("/")[-1] or "page"
            out = str(Path(output_dir) / f"{stem}.md")
        return convert(src, output_path=out)

    results: list[ConvertResult | None] = [None] * len(sources)

    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_idx = {executor.submit(_convert_one, src): i for i, src in enumerate(sources)}
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            results[idx] = future.result()

    return results  # type: ignore[return-value]


def _save(result: ConvertResult, source: str, output_path: str | None) -> None:
    """변환 결과를 파일로 저장한다."""
    from pathlib import Path

    if output_path:
        path = Path(output_path)
    elif source.startswith(("http://", "https://")):
        from urllib.parse import urlparse
        netloc = urlparse(source).netloc.replace("www.", "")
        path = Path(f"{netloc}.md")
    else:
        path = Path(source).with_suffix(".md")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.markdown_content, encoding="utf-8")


__all__ = ["convert", "convert_batch", "ConvertResult", "ConverterFactory"]
