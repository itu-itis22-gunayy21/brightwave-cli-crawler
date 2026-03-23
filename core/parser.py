from html.parser import HTMLParser
from urllib.parse import urljoin, urldefrag, urlparse
import re


TOKEN_RE = re.compile(r"[a-zA-Z0-9]{2,}")


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_chunks: list[str] = []
        self.title_chunks: list[str] = []
        self._ignore_content = False
        self._inside_title = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag in {"script", "style"}:
            self._ignore_content = True
            return

        if tag == "title":
            self._inside_title = True

        if tag == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.links.append(value)

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag in {"script", "style"}:
            self._ignore_content = False
            return

        if tag == "title":
            self._inside_title = False

    def handle_data(self, data):
        if self._ignore_content:
            return

        cleaned = data.strip()
        if not cleaned:
            return

        self.text_chunks.append(cleaned)
        if self._inside_title:
            self.title_chunks.append(cleaned)

    def get_text(self) -> str:
        return " ".join(self.text_chunks)

    def get_title(self) -> str:
        return " ".join(self.title_chunks)


def normalize_url(base_url: str, href: str) -> str | None:
    if not href:
        return None

    absolute = urljoin(base_url, href)
    absolute, _ = urldefrag(absolute)
    parsed = urlparse(absolute)

    if parsed.scheme not in {"http", "https"}:
        return None

    normalized = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower()
    ).geturl()

    return normalized


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(text)]


def parse_html(html: str, base_url: str) -> tuple[str, str, list[str]]:
    parser = PageParser()
    parser.feed(html)

    links: list[str] = []
    seen: set[str] = set()

    for raw_link in parser.links:
        normalized = normalize_url(base_url, raw_link)
        if normalized and normalized not in seen:
            seen.add(normalized)
            links.append(normalized)

    return parser.get_title(), parser.get_text(), links