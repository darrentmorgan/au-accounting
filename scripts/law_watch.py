# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Law-change watch: fingerprint primary-source pages and report what changed.

Run: uv run scripts/law_watch.py check [--only ID ...] [--update] [--offline DIR]
     uv run scripts/law_watch.py list

The watch list is data/law_watch/pages.yaml (id, url, why, per-page extraction hints on top of shared
profiles). Stored fingerprints are data/law_watch/fingerprints.json. For each page the tool fetches the
HTML, extracts only the relevant part (CSS-like selector, text anchors, strip patterns, so site chrome
and changing boilerplate do not count), normalises the text, hashes it, and compares with the stored
fingerprint. Legislation register pages fingerprint the compilation id and effective date instead of
the text.

Statuses per page: unchanged, changed, new (no stored fingerprint yet), error. Exit code: 0 nothing
changed, 1 at least one page changed or is new, 2 usage or configuration error, 3 errors under
--strict. The exit code reports what was found, not what was written: --update still exits 1 when it
recorded a change.

Blocked pages. Some sites (ato.gov.au, legislation.sa.gov.au, revenuesa.sa.gov.au) return
bot challenges or render values by script. Those are reported as `error: blocked` and are never
treated as a change. The tool sends one honest request per page with an identifying User-Agent,
honours robots.txt, waits between requests to the same host, never retries, stops asking a host that
has refused (or not answered) three requests in a row (--max-blocked), and never tries to get around
a challenge. A blocked page needs a person to check it in a browser and save it for --offline.

Offline mode (--offline DIR) reads DIR/<id>.html (and an optional DIR/<id>.status holding an HTTP
status code) instead of fetching; tests use it. --save DIR keeps each fetched page in that layout.
--only takes ids or globs. Stdlib plus pyyaml only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import gzip
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
import urllib.robotparser
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
PAGES_PATH = ROOT / "data" / "law_watch" / "pages.yaml"
FINGERPRINTS_PATH = ROOT / "data" / "law_watch" / "fingerprints.json"

USER_AGENT = "au-accounting-law-watch/0.1 (low-volume personal research tool; identifies itself, honours robots.txt)"
ROBOTS_TOKEN = "au-accounting-law-watch"
DEFAULT_DELAY = 3.0
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_SECONDS = 900.0
DEFAULT_MAX_BLOCKED = 3
MAX_BYTES = 25 * 1024 * 1024
DEFAULT_MIN_CHARS = 200
SCHEMA = 1

# Strong bot-challenge markers (lower-case substrings of the raw body). Deliberately narrow: a page that
# merely mentions a CAPTCHA in its text must not be flagged.
CHALLENGE_MARKERS = (
    "enable javascript and cookies to continue",
    "/cdn-cgi/challenge-platform",
    "cf-chl-",
    "attention required! | cloudflare",
    "_incapsula_resource",
    "incapsula incident id",
    "pardon our interruption",
    "px-captcha",
    "datadome",
    "errors.edgesuite.net",
    "sec-cpt",
    "request unsuccessful. incapsula",
)
CHALLENGE_TITLES = ("just a moment...", "access denied", "attention required")
BLOCKED_STATUSES = {401, 403, 429}

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP_TAGS = {"script", "style", "noscript", "template", "head", "iframe", "svg"}
BLOCK_TAGS = {
    "address", "article", "aside", "blockquote", "body", "br", "caption", "dd", "details", "div", "dl", "dt",
    "fieldset", "figcaption", "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "li",
    "main", "nav", "ol", "option", "p", "pre", "section", "summary", "table", "tbody", "td", "tfoot", "th", "thead",
    "tr", "ul",
}
TYPOGRAPHY = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                            "−": "-", "​": "", "‌": "", "‍": "", "﻿": "", "­": ""})


class ConfigError(Exception):
    """pages.yaml (or an argument) is invalid."""


# ------------------------------------------------------------------ selectors

@dataclass(frozen=True)
class Selector:
    tag: str | None = None
    id: str | None = None
    classes: tuple[str, ...] = ()
    attrs: tuple[tuple[str, str, str], ...] = ()  # (name, op, value); op in "", "=", "^=", "*="
    text: str = ""

    def matches(self, tag: str, attrs: dict[str, str]) -> bool:
        if self.tag and tag != self.tag:
            return False
        if self.id is not None and attrs.get("id") != self.id:
            return False
        if self.classes:
            have = attrs.get("class", "").split()
            if any(c not in have for c in self.classes):
                return False
        for name, op, value in self.attrs:
            got = attrs.get(name)
            if got is None:
                return False
            if op == "=" and got != value:
                return False
            if op == "^=" and not got.startswith(value):
                return False
            if op == "*=" and value not in got:
                return False
        return True


_SEL_HEAD = re.compile(r"^([A-Za-z][\w-]*)?")
_SEL_PART = re.compile(r"#([\w-]+)|\.([\w-]+)|\[\s*([\w:-]+)\s*(?:(\^=|\*=|=)\s*\"?([^\"\]]*)\"?)?\s*\]")


def parse_selector(text: str) -> Selector:
    """Parse a simple selector: tag, #id, .class, [attr], [attr=v], [attr^=v], [attr*=v], combined (no combinators)."""
    src = text.strip()
    if not src or " " in src or ">" in src or "," in src:
        raise ConfigError(f"unsupported selector {text!r}: use a single compound selector such as 'section#content' or 'div[id^=body]'")
    head = _SEL_HEAD.match(src)
    tag = head.group(1).lower() if head and head.group(1) else None
    pos = head.end() if head else 0
    id_ = None
    classes: list[str] = []
    attrs: list[tuple[str, str, str]] = []
    while pos < len(src):
        m = _SEL_PART.match(src, pos)
        if not m:
            raise ConfigError(f"cannot parse selector {text!r} at {src[pos:]!r}")
        if m.group(1):
            id_ = m.group(1)
        elif m.group(2):
            classes.append(m.group(2))
        else:
            attrs.append((m.group(3).lower(), m.group(4) or "", m.group(5) or ""))
        pos = m.end()
    if tag is None and id_ is None and not classes and not attrs:
        raise ConfigError(f"empty selector {text!r}")
    return Selector(tag, id_, tuple(classes), tuple(attrs), src)


# ------------------------------------------------------------------ text extraction

class _Extractor(HTMLParser):
    """Collect visible text as blocks (one per block-level element boundary) from the selected region."""

    def __init__(self, select: Selector | None, exclude: list[Selector]):
        super().__init__(convert_charrefs=True)
        self.select = select
        self.exclude = exclude
        self.stack: list[str] = []
        self.capture_at: int | None = None if select else -1
        self.skip_at: int | None = None
        self.matched = select is None
        self.blocks: list[str] = []
        self.buf: list[str] = []

    def _flush(self) -> None:
        if self.buf:
            text = "".join(self.buf)
            self.buf = []
            self.blocks.append(text)

    def handle_starttag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self._flush()
        if tag in VOID_TAGS:
            return
        self.stack.append(tag)
        idx = len(self.stack) - 1
        amap = {k.lower(): (v or "") for k, v in attrs}
        if self.skip_at is None and (tag in SKIP_TAGS or any(s.matches(tag, amap) for s in self.exclude)):
            self.skip_at = idx
        if self.capture_at is None and self.select is not None and self.select.matches(tag, amap):
            self.capture_at = idx
            self.matched = True

    def handle_startendtag(self, tag, attrs):
        if tag in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        if tag in BLOCK_TAGS:
            self._flush()
        if tag in VOID_TAGS or tag not in self.stack:
            return
        while self.stack:
            top = self.stack.pop()
            if top == tag:
                break
        depth = len(self.stack)
        if self.capture_at is not None and self.capture_at >= 0 and depth <= self.capture_at:
            self._flush()
            self.capture_at = None
        if self.skip_at is not None and depth <= self.skip_at:
            self.skip_at = None

    def handle_data(self, data):
        if self.skip_at is None and self.capture_at is not None:
            self.buf.append(data)

    def result(self) -> list[str]:
        self.close()
        self._flush()
        return self.blocks


def normalise_text(text: str) -> str:
    """NFKC, unify typographic quotes and dashes, drop zero-width characters, collapse whitespace."""
    text = unicodedata.normalize("NFKC", text).translate(TYPOGRAPHY)
    return re.sub(r"\s+", " ", text).strip()


# ------------------------------------------------------------------ pages and hints

@dataclass
class Page:
    id: str
    url: str
    why: str
    profile: str = ""
    skills: list[str] = field(default_factory=list)
    hints: dict = field(default_factory=dict)  # merged profile + page extract hints

    @property
    def host(self) -> str:
        return urlsplit(self.url).netloc.lower()


HINT_KEYS = {"select", "exclude", "start", "end", "strip", "meta", "fingerprint", "min_chars", "expect", "http_last_modified"}


def _check_hints(where: str, hints: dict) -> None:
    unknown = set(hints) - HINT_KEYS
    if unknown:
        raise ConfigError(f"{where}: unknown extraction hint(s) {sorted(unknown)}; allowed {sorted(HINT_KEYS)}")
    if hints.get("select"):
        parse_selector(hints["select"])
    for s in hints.get("exclude") or []:
        parse_selector(s)
    for pat in list(hints.get("strip") or []) + list((hints.get("meta") or {}).values()):
        try:
            re.compile(pat)
        except re.error as exc:
            raise ConfigError(f"{where}: bad regex {pat!r}: {exc}") from exc
    fp = hints.get("fingerprint")
    if fp is not None:
        if not isinstance(fp, dict) or fp.get("mode") not in {"text", "meta"}:
            raise ConfigError(f"{where}: fingerprint must be a mapping with mode: text or meta")
        if fp["mode"] == "meta":
            keys = fp.get("keys")
            if not keys or any(k not in (hints.get("meta") or {}) for k in keys):
                raise ConfigError(f"{where}: fingerprint mode meta needs keys that are defined under meta")


def load_pages(path: Path = PAGES_PATH) -> list[Page]:
    try:
        doc = yaml.safe_load(path.read_text())
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(doc, dict) or not isinstance(doc.get("pages"), list):
        raise ConfigError(f"{path}: expected a mapping with a `pages` list")
    profiles = doc.get("profiles") or {}
    for name, hints in profiles.items():
        _check_hints(f"profile {name}", hints or {})
    pages: list[Page] = []
    seen: set[str] = set()
    for i, raw in enumerate(doc["pages"]):
        pid = raw.get("id") if isinstance(raw, dict) else None
        where = f"page #{i + 1} ({pid})"
        if not pid or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(pid)):
            raise ConfigError(f"{where}: id must be kebab-case")
        if pid in seen:
            raise ConfigError(f"{where}: duplicate id")
        seen.add(pid)
        for req in ("url", "why"):
            if not raw.get(req):
                raise ConfigError(f"{where}: missing {req}")
        if not str(raw["url"]).startswith("https://"):
            raise ConfigError(f"{where}: url must be https")
        unknown = set(raw) - {"id", "url", "why", "profile", "skills", "extract"}
        if unknown:
            raise ConfigError(f"{where}: unknown field(s) {sorted(unknown)}")
        profile = raw.get("profile") or ""
        if profile and profile not in profiles:
            raise ConfigError(f"{where}: unknown profile {profile!r}")
        hints = dict(profiles.get(profile) or {})
        extra = raw.get("extract") or {}
        for k, v in extra.items():
            if k == "meta":
                hints["meta"] = {**(hints.get("meta") or {}), **v}
            else:
                hints[k] = v
        _check_hints(where, hints)
        pages.append(Page(pid, str(raw["url"]), str(raw["why"]), profile, list(raw.get("skills") or []), hints))
    return pages


# ------------------------------------------------------------------ fetching

@dataclass
class FetchResult:
    status: int = 0
    body: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    error: str = ""  # network-level failure text; status 0 then


def _decode(raw: bytes, headers: dict[str, str]) -> str:
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    ctype = headers.get("content-type", "")
    m = re.search(r"charset=([\w-]+)", ctype, re.I)
    try:
        return raw.decode(m.group(1) if m else "utf-8", errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def _urlopen(req: urllib.request.Request, timeout: float):
    return urllib.request.urlopen(req, timeout=timeout)  # noqa: S310 (https only, validated in load_pages)


def _read_capped(resp, deadline: float, clock: Callable[[], float]) -> bytes | None:
    """Read a response in chunks. None if it is over MAX_BYTES; TimeoutError if the wall-clock deadline passes.

    The socket timeout on urlopen bounds each wait, not the whole download, so a server that trickles bytes could
    otherwise hold a request open indefinitely.
    """
    chunks: list[bytes] = []
    size = 0
    while True:
        if clock() > deadline:
            raise TimeoutError("timed out: request exceeded its wall-clock limit")
        chunk = resp.read(65536)
        if not chunk:
            return b"".join(chunks)
        size += len(chunk)
        if size > MAX_BYTES:
            return None
        chunks.append(chunk)


def fetch_url(url: str, timeout: float = DEFAULT_TIMEOUT, clock: Callable[[], float] = time.monotonic) -> FetchResult:
    """One GET, no retries, at most `timeout` seconds of wall-clock time. HTTP error statuses come back as a FetchResult."""
    deadline = clock() + timeout
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml",
                                               "Accept-Encoding": "gzip"})
    try:
        with _urlopen(req, timeout) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = _read_capped(resp, deadline, clock)
            if raw is None:
                return FetchResult(error=f"response over {MAX_BYTES // (1024 * 1024)} MB")
            return FetchResult(resp.status, _decode(raw, headers), headers)
    except urllib.error.HTTPError as exc:
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        try:
            body = _decode(exc.read(MAX_BYTES), headers)
        except Exception:  # noqa: BLE001
            body = ""
        return FetchResult(exc.code, body, headers)
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        reason = getattr(exc, "reason", exc)
        return FetchResult(error=f"{type(exc).__name__}: {reason}")


class NetworkFetcher:
    """Polite fetcher: identifying UA, robots.txt, per-host delay, one attempt per page."""

    def __init__(self, delay: float = DEFAULT_DELAY, timeout: float = DEFAULT_TIMEOUT,
                 sleep: Callable[[float], None] = time.sleep, clock: Callable[[], float] = time.monotonic,
                 fetch: Callable[..., FetchResult] = fetch_url, max_blocked: int = DEFAULT_MAX_BLOCKED):
        self.delay, self.timeout, self.sleep, self.clock, self._fetch = delay, timeout, sleep, clock, fetch
        self.max_blocked = max_blocked
        self._blocked_streak: dict[str, int] = {}
        self._last: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    def _get(self, host: str, url: str) -> FetchResult:
        wait = self._last.get(host, float("-inf")) + self.delay - self.clock()
        if wait > 0:
            self.sleep(wait)
        result = self._fetch(url, self.timeout)
        self._last[host] = self.clock()
        return result

    def _robots_ok(self, page: Page) -> bool:
        parts = urlsplit(page.url)
        host = parts.netloc.lower()
        if host not in self._robots:
            res = self._get(host, f"{parts.scheme}://{parts.netloc}/robots.txt")
            if res.status == 200 and res.body.lstrip()[:15].lower().startswith(("user-agent", "#", "sitemap", "disallow", "allow")):
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(res.body.splitlines())
                self._robots[host] = rp
            else:
                self._robots[host] = None  # absent, unreadable or a challenge page: no robots restrictions to apply
        rp = self._robots[host]
        path = parts.path + (f"?{parts.query}" if parts.query else "")
        return rp is None or rp.can_fetch(ROBOTS_TOKEN, path or "/")

    def __call__(self, page: Page) -> FetchResult:
        streak = self._blocked_streak.get(page.host, 0)
        if self.max_blocked and streak >= self.max_blocked:
            return FetchResult(error=f"blocked: {page.host} refused or did not answer {streak} requests in a row, so this one was not sent")
        if not self._robots_ok(page):
            return FetchResult(error="robots: disallowed by robots.txt")
        res = self._get(page.host, page.url)
        # A refusal, a challenge page or a request left unanswered all count: some sites drop scripted clients silently.
        refused = (res.status in BLOCKED_STATUSES or detect_challenge(res) is not None
                   or "timed out" in res.error.lower() or "timeout" in res.error.lower())
        self._blocked_streak[page.host] = streak + 1 if refused else 0
        return res


class OfflineFetcher:
    """Read DIR/<id>.html (optional DIR/<id>.status) instead of the network."""

    def __init__(self, directory: Path):
        self.directory = Path(directory)

    def __call__(self, page: Page) -> FetchResult:
        f = self.directory / f"{page.id}.html"
        if not f.is_file():
            return FetchResult(error=f"no offline fixture {f.name}")
        status_file = self.directory / f"{page.id}.status"
        status = int(status_file.read_text().strip()) if status_file.is_file() else 200
        return FetchResult(status, f.read_text(errors="replace"))


# ------------------------------------------------------------------ extraction and fingerprint

class PageError(Exception):
    """A per-page failure reported as `error: <kind> (...)`, never as a change."""

    def __init__(self, kind: str, detail: str):
        super().__init__(f"{kind} ({detail})" if detail else kind)
        self.kind, self.detail = kind, detail


@dataclass
class Extraction:
    blocks: list[str]
    meta: dict[str, str]
    mode: str
    sha256: str


def detect_challenge(res: FetchResult) -> str | None:
    """Return a reason if the response is a bot challenge or access denial, else None."""
    if res.status in BLOCKED_STATUSES:
        return f"http {res.status}"
    body = res.body[:200_000].lower()
    for marker in CHALLENGE_MARKERS:
        if marker in body:
            return "challenge page"
    title = re.search(r"<title[^>]*>(.*?)</title>", body, re.S)
    if title and any(t in title.group(1).strip() for t in CHALLENGE_TITLES) and len(res.body) < 60_000:
        return "challenge page"
    if res.status == 503 and len(res.body) < 20_000:
        return "http 503"
    return None


def _clean_meta(value: str) -> str:
    if "\\" in value:
        try:
            value = json.loads(f'"{value}"')
        except ValueError:
            pass
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return normalise_text(value)[:400]


def extract_meta(raw_html: str, patterns: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for name, pattern in patterns.items():
        m = re.search(pattern, raw_html, re.S)
        if m:
            val = _clean_meta(m.group(1) if m.groups() else m.group(0))
            if val:
                out[name] = val
    return out


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_page(page: Page, res: FetchResult) -> Extraction:
    """Turn a fetched response into blocks, metadata and a hash, or raise PageError."""
    reason = detect_challenge(res)
    if reason:
        raise PageError("blocked", reason)
    if res.status >= 400 or res.status == 0:
        raise PageError(f"http {res.status}" if res.status else "fetch", "")
    hints = page.hints
    meta = extract_meta(res.body, hints.get("meta") or {})
    if hints.get("http_last_modified") and res.headers.get("last-modified"):
        meta["http_last_modified"] = res.headers["last-modified"]
    fp = hints.get("fingerprint") or {"mode": "text"}
    if fp["mode"] == "meta":
        missing = [k for k in fp["keys"] if k not in meta]
        if missing:
            raise PageError("blocked", f"empty or script-rendered page: {', '.join(missing)} not found")
        return Extraction([], meta, "meta", _sha("\n".join(f"{k}={meta[k]}" for k in fp["keys"])))

    select = parse_selector(hints["select"]) if hints.get("select") else None
    parser = _Extractor(select, [parse_selector(s) for s in hints.get("exclude") or []])
    parser.feed(res.body)
    raw_blocks = parser.result()
    if select is not None and not parser.matched:
        raise PageError("blocked", f"empty or script-rendered page: selector {hints['select']!r} matched nothing")
    text = "\n".join(b for b in (normalise_text(b) for b in raw_blocks) if b)
    if hints.get("start"):
        i = text.find(normalise_text(hints["start"]))
        if i < 0:
            raise PageError("extraction", f"start anchor {hints['start']!r} not found; page layout may have changed")
        text = text[i:]
    if hints.get("end"):
        j = text.find(normalise_text(hints["end"]), 1)
        if j >= 0:
            text = text[:j]
    strips = [re.compile(p) for p in hints.get("strip") or []]
    blocks: list[str] = []
    for line in text.split("\n"):
        for rx in strips:
            line = rx.sub("", line)
        line = normalise_text(line)
        if line:
            blocks.append(line)
    total = sum(len(b) for b in blocks)
    if total < int(hints.get("min_chars", DEFAULT_MIN_CHARS)):
        raise PageError("blocked", f"empty or script-rendered page: {total} characters extracted")
    joined = "\n".join(blocks)
    for needle in hints.get("expect") or []:
        if normalise_text(needle) not in joined:
            raise PageError("blocked", f"empty or script-rendered page: expected text {needle!r} missing")
    return Extraction(blocks, meta, "text", _sha(joined))


def _block_hash(block: str) -> str:
    return hashlib.sha256(block.encode("utf-8")).hexdigest()[:8]


MAX_STORED_BLOCKS = 3000


def build_fingerprint(page: Page, ex: Extraction, checked_at: str, previous: dict | None) -> dict:
    fp: dict = {"url": page.url, "mode": ex.mode, "sha256": ex.sha256}
    if ex.mode == "text":
        fp["chars"] = sum(len(b) for b in ex.blocks)
        fp["blocks"] = " ".join(_block_hash(b) for b in ex.blocks[:MAX_STORED_BLOCKS])
    fp["meta"] = ex.meta
    fp["checked_at"] = checked_at
    same = previous and previous.get("sha256") == ex.sha256
    fp["changed_at"] = previous.get("changed_at", previous.get("checked_at", checked_at)) if same else checked_at
    return fp


# ------------------------------------------------------------------ comparison and reporting

@dataclass
class Result:
    page: Page
    status: str  # unchanged | changed | new | error
    detail: str = ""
    notes: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    removed_count: int = 0
    fingerprint: dict | None = None


def _short(value: str, width: int = 100) -> str:
    return value if len(value) <= width else value[: width - 3] + "..."


def _meta_diff(old: dict, new: dict) -> list[str]:
    out = []
    for k in sorted(set(old) | set(new)):
        if old.get(k) != new.get(k):
            out.append(f"{k}: {_short(old.get(k, '-'))} -> {_short(new.get(k, '-'))}")
    return out


def compare(page: Page, ex: Extraction, old: dict | None, checked_at: str) -> Result:
    new_fp = build_fingerprint(page, ex, checked_at, old)
    if not old:
        return Result(page, "new", "no stored fingerprint", fingerprint=new_fp)
    meta_notes = _meta_diff(old.get("meta") or {}, ex.meta)
    if old.get("sha256") == ex.sha256 and old.get("mode", "text") == ex.mode:
        notes = [f"metadata moved with identical text: {'; '.join(meta_notes)}"] if meta_notes else []
        return Result(page, "unchanged", notes=notes, fingerprint=new_fp)
    res = Result(page, "changed", fingerprint=new_fp)
    if meta_notes:
        res.detail = "; ".join(meta_notes)
    if ex.mode == "text" and old.get("blocks") is not None:
        old_counts = Counter(str(old["blocks"]).split())
        added, new_counts = [], Counter()
        for b in ex.blocks:
            h = _block_hash(b)
            new_counts[h] += 1
            if new_counts[h] > old_counts.get(h, 0):
                added.append(b)
        res.added = added
        res.removed_count = sum(max(c - new_counts.get(h, 0), 0) for h, c in old_counts.items())
        counts = f"{len(added)} block(s) added, {res.removed_count} removed"
        res.detail = f"{res.detail}; {counts}" if res.detail else counts
    return res


def check_page(page: Page, fetcher: Callable[[Page], FetchResult], old: dict | None, checked_at: str) -> Result:
    res = fetcher(page)
    if res.error:
        kind, _, detail = res.error.partition(": ")
        return Result(page, "error", f"{kind} ({detail})" if detail else kind)
    try:
        ex = extract_page(page, res)
    except PageError as exc:
        return Result(page, "error", str(exc))
    return compare(page, ex, old, checked_at)


# ------------------------------------------------------------------ store

def load_fingerprints(path: Path = FINGERPRINTS_PATH) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "pages": {}}
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("pages"), dict):
        raise ConfigError(f"{path}: expected an object with a `pages` object")
    return data


def save_fingerprints(store: dict, path: Path = FINGERPRINTS_PATH) -> None:
    store["schema"] = SCHEMA
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(store, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    tmp.replace(path)


# ------------------------------------------------------------------ orchestration

@dataclass
class Report:
    results: list[Result]
    orphans: list[str]
    written: bool = False

    def count(self, status: str) -> int:
        return sum(1 for r in self.results if r.status == status)

    @property
    def blocked(self) -> int:
        return sum(1 for r in self.results if r.status == "error" and r.detail.startswith("blocked"))

    def exit_code(self, strict: bool = False) -> int:
        if self.count("changed") or self.count("new"):
            return 1
        if strict and self.count("error"):
            return 3
        return 0


def run_check(pages: list[Page], fetcher: Callable[[Page], FetchResult], store: dict, checked_at: str,
              update: bool = False, on_result: Callable[[Result], None] | None = None,
              all_ids: set[str] | None = None, max_seconds: float | None = None,
              clock: Callable[[], float] = time.monotonic) -> Report:
    """Check each page in turn. Once `max_seconds` of wall-clock time has passed, remaining pages are not fetched and
    are reported as `error: time limit`, so the run always ends (a page already in flight is bounded by its own timeout)."""
    results: list[Result] = []
    started = clock()
    for page in pages:
        if max_seconds and clock() - started > max_seconds:
            r = Result(page, "error", f"time limit (overall cap of {max_seconds:g} s reached, page not fetched)")
        else:
            r = check_page(page, fetcher, store["pages"].get(page.id), checked_at)
        results.append(r)
        if on_result:
            on_result(r)
        if update and r.fingerprint is not None:
            store["pages"][page.id] = r.fingerprint
    known = all_ids if all_ids is not None else {p.id for p in pages}
    return Report(results, sorted(set(store["pages"]) - known), written=update)


def format_result(r: Result, verbose: bool = False, max_added: int = 6) -> str:
    label = {"unchanged": "unchanged", "changed": "CHANGED", "new": "new", "error": "error"}[r.status]
    if r.status == "error":
        line = f"error: {r.detail}"
        lines = [f"{line:<28} {r.page.id}"]
    else:
        lines = [f"{label:<28} {r.page.id}" + (f"  {r.detail}" if r.detail else "")]
    for note in r.notes:
        lines.append(f"    note: {note}")
    if r.status == "changed":
        lines.append(f"    why watched: {r.page.why}")
        lines.append(f"    url: {r.page.url}")
        shown = r.added if verbose else r.added[:max_added]
        for b in shown:
            lines.append("    + " + (b if verbose or len(b) <= 220 else b[:217] + "..."))
        if len(shown) < len(r.added):
            lines.append(f"    + ... {len(r.added) - len(shown)} more added block(s) (use --verbose)")
        if r.removed_count:
            lines.append(f"    - {r.removed_count} block(s) no longer present (old text is not stored)")
    return "\n".join(lines)


def format_summary(rep: Report, updated: bool) -> str:
    parts = [f"{len(rep.results)} pages: {rep.count('unchanged')} unchanged, {rep.count('changed')} changed, "
             f"{rep.count('new')} new, {rep.count('error')} error ({rep.blocked} blocked)"]
    if rep.count("new") and not updated:
        parts.append("new pages have no baseline yet: run with --update to record one")
    if updated:
        parts.append("fingerprints updated for changed, new and unchanged pages; error pages left as they were")
    if rep.orphans:
        parts.append(f"fingerprints for ids no longer in pages.yaml: {', '.join(rep.orphans)}")
    if rep.count("error"):
        parts.append(f"WARNING: {rep.count('error')} of {len(rep.results)} pages were not checked (blocked, timed out or "
                     "missing offline copy). The exit code ignores errors unless --strict is given: check those pages "
                     "by hand or from saved browser copies (--offline).")
    return "\n".join(parts)


# ------------------------------------------------------------------ CLI

def _saving(fetcher: Callable[[Page], FetchResult], directory: Path) -> Callable[[Page], FetchResult]:
    """Wrap a fetcher so each response body is also written to DIR/<id>.html for offline re-runs."""
    directory.mkdir(parents=True, exist_ok=True)

    def wrapped(page: Page) -> FetchResult:
        res = fetcher(page)
        if not res.error:
            (directory / f"{page.id}.html").write_text(res.body)
            (directory / f"{page.id}.status").write_text(f"{res.status}\n")
        return res

    return wrapped


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="law_watch.py", description="Fingerprint primary-source pages and report what changed.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    chk = sub.add_parser("check", help="fetch each watched page and compare with its stored fingerprint")
    chk.add_argument("--only", action="append", metavar="ID", help="check only page ids matching this id or glob such as 'legis-*' (repeatable)")
    chk.add_argument("--update", action="store_true", help="write fingerprints for changed, new and unchanged pages")
    chk.add_argument("--offline", metavar="DIR", help="read DIR/<id>.html instead of fetching (tests, saved pages)")
    chk.add_argument("--strict", action="store_true", help="exit 3 when any page errored (blocked pages included)")
    chk.add_argument("--save", metavar="DIR", help="also write each fetched page to DIR/<id>.html (and .status), usable later with --offline")
    chk.add_argument("--verbose", action="store_true", help="print every added text block for changed pages")
    chk.add_argument("--delay", type=float, default=DEFAULT_DELAY, help=f"seconds between requests to one host (default {DEFAULT_DELAY:g})")
    chk.add_argument("--max-blocked", type=int, default=DEFAULT_MAX_BLOCKED, metavar="N",
                     help=f"stop requesting a host after N blocked responses in a row (default {DEFAULT_MAX_BLOCKED}; 0 = never stop)")
    chk.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"per-request wall-clock limit in seconds (default {DEFAULT_TIMEOUT:g})")
    chk.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS, metavar="S",
                     help=f"overall cap for the whole run; pages not reached are reported as errors (default {DEFAULT_MAX_SECONDS:g}; 0 = no cap)")
    lst = sub.add_parser("list", help="print the watch list and which pages have no stored fingerprint yet")
    for p in (chk, lst):
        p.add_argument("--pages", type=Path, default=PAGES_PATH, help=argparse.SUPPRESS)
        p.add_argument("--fingerprints", type=Path, default=FINGERPRINTS_PATH, help=argparse.SUPPRESS)
    chk.add_argument("--checked-at", default=None, help=argparse.SUPPRESS)
    return ap


def main(argv: list[str] | None = None, *, fetcher: Callable[[Page], FetchResult] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        pages = load_pages(args.pages)
        if args.cmd == "list":
            known = load_fingerprints(args.fingerprints)["pages"]
            for p in pages:
                print(f"{p.id:<44} {'' if p.id in known else '[no fingerprint] '}{p.url}")
            missing = sum(1 for p in pages if p.id not in known)
            print(f"{len(pages)} pages, {missing} without a fingerprint (check reports them as new, or as errors if the site blocks scripted fetches)")
            return 0
        all_ids = {p.id for p in pages}
        if args.only:
            unknown = [pat for pat in args.only if not any(fnmatch.fnmatchcase(p.id, pat) for p in pages)]
            if unknown:
                raise ConfigError(f"no page id matches: {', '.join(unknown)}")
            pages = [p for p in pages if any(fnmatch.fnmatchcase(p.id, pat) for pat in args.only)]
        store = load_fingerprints(args.fingerprints)
    except ConfigError as exc:
        print(f"law_watch: {exc}", file=sys.stderr)
        return 2
    if fetcher is None:
        fetcher = OfflineFetcher(Path(args.offline)) if args.offline else NetworkFetcher(args.delay, args.timeout, max_blocked=args.max_blocked)
    if args.save:
        fetcher = _saving(fetcher, Path(args.save))
    checked_at = args.checked_at or dt.date.today().isoformat()
    rep = run_check(pages, fetcher, store, checked_at, update=args.update,
                    on_result=lambda r: print(format_result(r, args.verbose), flush=True), all_ids=all_ids,
                    max_seconds=args.max_seconds)
    if args.update:
        save_fingerprints(store, args.fingerprints)
    print(format_summary(rep, args.update))
    return rep.exit_code(args.strict)


if __name__ == "__main__":
    sys.exit(main())
