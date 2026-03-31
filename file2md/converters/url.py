from urllib.parse import urlparse

from file2md.core.base import ConvertResult
from file2md.converters.html import HtmlConverter


class UrlConverter(HtmlConverter):
    """
    URL을 다운로드해 마크다운으로 변환한다.

    HtmlConverter를 상속하므로 HTML 파싱 로직을 그대로 재사용한다.
    변환 규칙은 HtmlConverter와 동일하며, 추가로:
        - User-Agent를 설정해 봇 차단을 우회한다.
        - 타임아웃 10초, 최대 3회 재시도한다.
        - 리다이렉트를 따라가며 최종 URL을 메타데이터에 기록한다.
    """

    TIMEOUT = 10
    MAX_RETRIES = 3
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    @property
    def supported_formats(self) -> tuple:
        return ()   # URL은 확장자 기반이 아님

    def can_handle(self, source: str) -> bool:
        return source.startswith(("http://", "https://"))

    def convert(self, source: str) -> ConvertResult:
        try:
            import requests
        except ImportError:
            return ConvertResult.failure(source, "url", "requests가 설치되어 있지 않습니다. pip install requests")

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return ConvertResult.failure(source, "url", "beautifulsoup4가 설치되어 있지 않습니다. pip install beautifulsoup4")

        session = self._make_session()
        try:
            response = session.get(
                source,
                headers={"User-Agent": self.USER_AGENT},
                timeout=self.TIMEOUT,
                allow_redirects=True,
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding
        except requests.exceptions.Timeout:
            return ConvertResult.failure(source, "url", f"타임아웃 ({self.TIMEOUT}초 초과)")
        except requests.exceptions.ConnectionError:
            return ConvertResult.failure(source, "url", "연결 실패: 네트워크 또는 DNS 오류")
        except requests.exceptions.HTTPError as e:
            return ConvertResult.failure(source, "url", f"HTTP 오류: {e}")
        except Exception as e:
            return ConvertResult.failure(source, "url", str(e))

        soup = BeautifulSoup(response.text, "html.parser")
        title = self._extract_title(soup) or urlparse(response.url).netloc

        metadata = {
            "title": title,
            "url": response.url,
            "format": "url",
            "status_code": response.status_code,
        }
        frontmatter = self.build_frontmatter(metadata)

        markdown, table_count, image_count = self._parse(soup)
        markdown = frontmatter + self.sanitize(markdown)

        return ConvertResult(
            markdown_content=markdown,
            source=source,
            format="url",
            table_count=table_count,
            image_count=image_count,
        )

    def _make_session(self):
        """재시도 로직이 적용된 requests 세션 생성"""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        session = requests.Session()
        retry = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
