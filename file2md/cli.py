"""
file2md CLI

사용법:
    python -m file2md report.pdf
    python -m file2md report.pdf -o ./output/result.md
    python -m file2md --url https://example.com
    python -m file2md --batch a.docx b.xlsx c.pptx --output-dir ./out/
"""

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file2md",
        description="다양한 파일 형식을 마크다운(.md)으로 변환합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 단일 파일
  python -m file2md report.pdf
  python -m file2md report.pdf -o ./output/report.md

  # URL
  python -m file2md --url https://example.com
  python -m file2md --url https://example.com -o page.md

  # 배치 변환
  python -m file2md --batch a.docx b.xlsx c.pptx
  python -m file2md --batch *.pdf --output-dir ./output/ --workers 8

  # 마크다운을 파일로 저장하지 않고 stdout으로만 출력
  python -m file2md report.pdf --no-save
        """,
    )

    # ── 입력 ──────────────────────────────────────
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "input",
        nargs="?",
        metavar="FILE",
        help="변환할 파일 경로",
    )
    input_group.add_argument(
        "--url",
        metavar="URL",
        help="변환할 웹 페이지 URL",
    )
    input_group.add_argument(
        "--batch",
        nargs="+",
        metavar="FILE",
        help="배치 변환할 파일 목록",
    )

    # ── 출력 ──────────────────────────────────────
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="출력 파일 경로 (단일 변환에만 사용)",
    )
    output_group.add_argument(
        "--output-dir",
        metavar="DIR",
        help="출력 디렉토리 (배치 변환에 사용)",
    )

    # ── 옵션 ──────────────────────────────────────
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="파일로 저장하지 않고 stdout으로 출력",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        metavar="N",
        help="배치 변환 병렬 스레드 수 (기본값: 4)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="상세 정보 출력",
    )
    parser.add_argument(
        "--formats",
        action="store_true",
        help="지원하는 파일 형식 목록 출력 후 종료",
    )

    return parser


def main(argv=None) -> int:
    # --formats는 입력 없이도 동작해야 하므로 먼저 처리
    if argv is None:
        import sys
        argv = sys.argv[1:]
    if "--formats" in argv:
        from file2md.core.factory import ConverterFactory
        print("지원 형식:", ", ".join(ConverterFactory.supported_formats()))
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    from file2md import convert, convert_batch

    save_file = not args.no_save

    # ── 단일 파일 ──────────────────────────────
    if args.input or args.url:
        source = args.url or args.input
        try:
            result = convert(source, output_path=args.output, save_file=save_file)
        except ValueError as e:
            print(f"오류: {e}", file=sys.stderr)
            return 1

        if result.success:
            if args.no_save:
                print(result.markdown_content)
            else:
                output = args.output or _default_output(source)
                if args.verbose:
                    print(f"변환 완료: {output}")
                    if result.page_count:
                        print(f"  페이지: {result.page_count}")
                    if result.table_count:
                        print(f"  테이블: {result.table_count}")
                    if result.image_count:
                        print(f"  이미지: {result.image_count}")
                else:
                    print(f"변환 완료: {output}")
            return 0
        else:
            print(f"오류: {result.error}", file=sys.stderr)
            return 1

    # ── 배치 변환 ──────────────────────────────
    if args.batch:
        results = convert_batch(
            args.batch,
            output_dir=args.output_dir,
            workers=args.workers,
        )

        success = sum(1 for r in results if r.success)
        fail = len(results) - success

        for src, result in zip(args.batch, results):
            status = "✓" if result.success else "✗"
            msg = result.error or ""
            print(f"  {status} {src}  {msg}")

        print(f"\n완료: {success}개 성공, {fail}개 실패")
        return 0 if fail == 0 else 1

    return 0


def _default_output(source: str) -> str:
    if source.startswith(("http://", "https://")):
        from urllib.parse import urlparse
        return urlparse(source).netloc.replace("www.", "") + ".md"
    return str(Path(source).with_suffix(".md"))


if __name__ == "__main__":
    sys.exit(main())
