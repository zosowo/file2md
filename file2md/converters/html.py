from pathlib import Path
from typing import Optional

from file2md.core.base import BaseConverter, ConvertResult
from file2md.utils.markdown import table_to_markdown


class HtmlConverter(BaseConverter):
    """
    .html / .htm 파일을 마크다운으로 변환한다.

    변환 규칙:
        - h1~h6  → # ~ ######
        - p       → 단락
        - a       → [텍스트](href)
        - img     → ![alt](src)
        - table   → 마크다운 테이블
        - ul/ol   → - 또는 1. 리스트
        - pre/code → 코드블록
        - script, style, nav, footer 태그는 제거
    """

    @property
    def supported_formats(self) -> tuple:
        return ("html", "htm")

    def convert(self, source: str) -> ConvertResult:
        path = Path(source)

        if not path.exists():
            return ConvertResult.failure(source, "html", f"파일을 찾을 수 없습니다: {source}")

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return ConvertResult.failure(source, "html", "beautifulsoup4가 설치되어 있지 않습니다. pip install beautifulsoup4")

        try:
            raw = path.read_bytes()
            soup = BeautifulSoup(raw, "html.parser")
        except Exception as e:
            return ConvertResult.failure(source, "html", str(e))

        title = self._extract_title(soup) or path.stem
        metadata = {
            "title": title,
            "source": str(path.resolve()),
            "format": "html",
        }
        frontmatter = self.build_frontmatter(metadata)

        markdown, table_count, image_count = self._parse(soup)
        markdown = frontmatter + self.sanitize(markdown)

        return ConvertResult(
            markdown_content=markdown,
            source=source,
            format="html",
            table_count=table_count,
            image_count=image_count,
        )

    # ──────────────────────────────────────────────
    # 내부 파싱 메서드 (UrlConverter에서도 재사용)
    # ──────────────────────────────────────────────

    def _parse(self, soup) -> tuple[str, int, int]:
        """BeautifulSoup 객체를 받아 (마크다운, 테이블 수, 이미지 수) 반환"""
        from bs4 import BeautifulSoup

        # 불필요한 태그 제거
        for tag in soup(["script", "style", "nav", "footer", "aside"]):
            tag.decompose()

        body = soup.find("body") or soup
        parts: list[str] = []
        table_count = 0
        image_count = 0

        for element in body.descendants:
            # 직접 자식만 처리 (descendants 순회는 중복 포함)
            # 실제로는 _convert_node를 재귀 호출하는 방식이 더 명확
            pass

        md, tc, ic = self._convert_node(body)
        return md, tc, ic

    def _convert_node(self, node) -> tuple[str, int, int]:
        """
        재귀적으로 HTML 노드를 마크다운으로 변환한다.
        반환: (마크다운 문자열, 테이블 수, 이미지 수)
        """
        from bs4 import NavigableString, Tag

        if isinstance(node, NavigableString):
            text = str(node)
            # 공백만 있는 텍스트 노드는 무시
            return (text if text.strip() else ""), 0, 0

        if not isinstance(node, Tag):
            return "", 0, 0

        tag = node.name
        tc = 0  # table count
        ic = 0  # image count

        # ── 헤딩 ──────────────────────────────────
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            text = node.get_text(separator=" ", strip=True)
            return f"\n{'#' * level} {text}\n", 0, 0

        # ── 단락 ──────────────────────────────────
        if tag == "p":
            inner, tc, ic = self._children_md(node)
            return f"\n{inner.strip()}\n", tc, ic

        # ── 링크 ──────────────────────────────────
        if tag == "a":
            href = node.get("href", "#")
            text = node.get_text(strip=True)
            return f"[{text}]({href})", 0, 0

        # ── 이미지 ────────────────────────────────
        if tag == "img":
            src = node.get("src", "")
            alt = node.get("alt", "image")
            return f"![{alt}]({src})", 0, 1

        # ── 코드 블록 ─────────────────────────────
        if tag == "pre":
            code_tag = node.find("code")
            lang = ""
            if code_tag:
                classes = code_tag.get("class", [])
                for cls in classes:
                    if cls.startswith("language-"):
                        lang = cls.replace("language-", "")
                        break
            code = node.get_text()
            return f"\n```{lang}\n{code}\n```\n", 0, 0

        if tag == "code":
            # pre 안의 code는 위에서 처리됨, 인라인 코드
            if node.parent and node.parent.name == "pre":
                return "", 0, 0
            return f"`{node.get_text()}`", 0, 0

        # ── 테이블 ────────────────────────────────
        if tag == "table":
            rows = []
            for tr in node.find_all("tr"):
                cells = [td.get_text(separator=" ", strip=True) for td in tr.find_all(["th", "td"])]
                if cells:
                    rows.append(cells)
            if rows:
                return f"\n{table_to_markdown(rows)}\n", 1, 0
            return "", 0, 0

        # ── 순서 없는 목록 ────────────────────────
        if tag == "ul":
            items = []
            for li in node.find_all("li", recursive=False):
                text = li.get_text(separator=" ", strip=True)
                items.append(f"- {text}")
            return "\n" + "\n".join(items) + "\n", 0, 0

        # ── 순서 있는 목록 ────────────────────────
        if tag == "ol":
            items = []
            for i, li in enumerate(node.find_all("li", recursive=False), 1):
                text = li.get_text(separator=" ", strip=True)
                items.append(f"{i}. {text}")
            return "\n" + "\n".join(items) + "\n", 0, 0

        # ── 수평선 ────────────────────────────────
        if tag == "hr":
            return "\n---\n", 0, 0

        # ── 강조 ──────────────────────────────────
        if tag in ("strong", "b"):
            return f"**{node.get_text(strip=True)}**", 0, 0

        if tag in ("em", "i"):
            return f"*{node.get_text(strip=True)}*", 0, 0

        # ── 줄바꿈 ────────────────────────────────
        if tag == "br":
            return "\n", 0, 0

        # ── 그 외: 자식 노드 재귀 처리 ────────────
        return self._children_md(node)

    def _children_md(self, node) -> tuple[str, int, int]:
        """자식 노드들을 순서대로 변환해 합친다."""
        parts = []
        total_tc = 0
        total_ic = 0
        for child in node.children:
            md, tc, ic = self._convert_node(child)
            parts.append(md)
            total_tc += tc
            total_ic += ic
        return "".join(parts), total_tc, total_ic

    @staticmethod
    def _extract_title(soup) -> Optional[str]:
        """<title> 또는 <h1> 태그에서 제목을 추출한다."""
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return None
