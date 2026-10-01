"""Tests for scripts/law_watch.py (GOAL gate 8). No network: pages are synthetic HTML modelled on the markup of the
sites on the watch list (structure only, invented text and numbers), passed through the offline fetcher or an injected
fetcher. The fetch layer is tested with a fake `_urlopen`.

Rates and figures here are made up; nothing in this file is a tax figure.
"""

import gzip
import io
import json
import sys
import urllib.error
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import law_watch as lw  # noqa: E402

REAL_PAGES = ROOT / "data" / "law_watch" / "pages.yaml"
REAL_FINGERPRINTS = ROOT / "data" / "law_watch" / "fingerprints.json"


# ------------------------------------------------------------------ synthetic pages

def ato_html(rows=(("0 - 10", "Nil"), ("10 - 20", "5c for each $1 over 10")), *, banner="", nav="Menu Search Log in",
             footer="Our commitment to you", last_updated="1 January 2030", sep="\n", intro="Rates for the demo year."):
    """Next.js-style ATO page: hashed class names, section#content with breadcrumb and feedback widgets around the body."""
    table = "".join(f"<tr><td>{a}</td><td>{b}</td></tr>{sep}" for a, b in rows)
    filler = "Demo paragraph that pads the extracted text past the minimum length. " * 6
    return f"""<!doctype html><html><head><title>Demo rates | Australian Taxation Office</title>
<script>window.__NEXT_DATA__ = {{"props": "<p>Do not fingerprint me 999</p>"}};</script><style>.a{{color:red}}</style></head>
<body><div id="__next">{banner}<div id="main-nav">{nav}</div>
<section id="content"><section id="breadcrumb-nav"><a href="/">Home</a> Rates</section>
<section class="Layout_title__Zklb" id="content-header"><h1>Demo rates</h1>
<p class="Date_date__mL2KV"><strong>Last updated </strong>{last_updated}</p></section>
<section id="content-nav">On this page</section>
<section class="Layout_content__WN_oi" id="content-body1f35"><h2>About</h2><p>{intro}</p><p>{filler}</p>
<table><tbody>{table}</tbody></table></section>
<section id="page-qc">Was this page helpful? Yes No</section></section>
<section id="footer"><footer>{footer}</footer></section></div></body></html>"""


CHALLENGE_HTML = ("<!DOCTYPE html><html><head><title>Just a moment...</title></head><body><div id='main' role='main'>"
                  "Enable JavaScript and cookies to continue</div></body></html>")
JS_SHELL_HTML = "<html><head><title>Rates</title></head><body><div id='root'></div><script src='/app.js'></script></body></html>"


def legis_html(comp="C2030C00001", num="C10", start="1 July 2030", noise="a"):
    return (f'<html><body><app-root _ngcontent-{noise}="" class="x"><span _ngcontent-{noise}="" class="item-id small fw-bold">'
            f'{comp} {num}</span><frl-effective-dates><span class="date-effective-start">{start}</span></frl-effective-dates>'
            f'<script>{{"isLatest":true,"name":"Demo Act 2000","status":"InForce","registerId":"{comp}","compilationNumber":"10",'
            f'"publishComments":"Demo comment."}}</script></app-root></body></html>')


def fwo_html(rows=("1 Jan New Year's Day",), updated="2030-01-01", banner=""):
    items = "".join(f"<li>{r}</li>" for r in rows)
    pad = "Padding text so that the page is long enough to be a real page. " * 6
    return (f"<html><body>{banner}<nav>Home Menu</nav><article class='main rightWider' role='main'><a id='main-content'></a>"
            f"<h1>2030 public holidays</h1><p>{pad}</p><ul>{items}</ul></article>"
            f"<footer><p>Printed from example.gov.au<br/>Content last updated: {updated}<br/>Copyright</p></footer></body></html>")


@pytest.fixture()
def env(tmp_path):
    """A tmp pages.yaml built from the REAL profiles plus three demo pages, an offline dir, and a fingerprints path."""
    profiles = yaml.safe_load(REAL_PAGES.read_text())["profiles"]
    pages = {
        "schema": 1,
        "profiles": profiles,
        "pages": [
            {"id": "demo-ato", "url": "https://www.ato.gov.au/demo", "profile": "ato", "why": "demo ATO page", "skills": ["demo"]},
            {"id": "demo-legis", "url": "https://www.legislation.gov.au/C2030A00001/latest/text", "profile": "legislation-gov-au", "why": "demo Act"},
            {"id": "demo-fwo", "url": "https://www.fairwork.gov.au/demo", "profile": "fwo", "why": "demo holidays"},
        ],
    }
    pages_path = tmp_path / "pages.yaml"
    pages_path.write_text(yaml.safe_dump(pages))
    off = tmp_path / "off"
    off.mkdir()
    return type("Env", (), {"pages": pages_path, "off": off, "fp": tmp_path / "fp.json", "tmp": tmp_path})()


def put(env, page_id, html, status=None):
    (env.off / f"{page_id}.html").write_text(html)
    if status is not None:
        (env.off / f"{page_id}.status").write_text(str(status))


def seed_all(env):
    put(env, "demo-ato", ato_html())
    put(env, "demo-legis", legis_html())
    put(env, "demo-fwo", fwo_html())


def run(env, *extra, capsys=None):
    argv = ["check", "--pages", str(env.pages), "--fingerprints", str(env.fp), "--offline", str(env.off),
            "--checked-at", "2030-02-01", *extra]
    code = lw.main(argv)
    return code, (capsys.readouterr().out if capsys else "")


def stored(env):
    return json.loads(env.fp.read_text())["pages"]


# ------------------------------------------------------------------ the five behaviours asked for

def test_unchanged_after_baseline(env, capsys):
    seed_all(env)
    code, out = run(env, "--update", capsys=capsys)
    assert code == 1 and sum(1 for ln in out.splitlines() if ln.startswith("new ")) == 3  # no baseline yet: new, non-zero
    code, out = run(env, capsys=capsys)
    assert code == 0
    assert "3 pages: 3 unchanged, 0 changed, 0 new, 0 error (0 blocked)" in out


def test_changed_text_is_reported_with_added_block_and_exits_nonzero(env, capsys):
    seed_all(env)
    run(env, "--update", capsys=capsys)
    put(env, "demo-ato", ato_html(rows=(("0 - 10", "Nil"), ("10 - 20", "7c for each $1 over 10"))))
    code, out = run(env, capsys=capsys)
    assert code == 1
    assert "CHANGED" in out and "demo-ato" in out
    assert "1 block(s) added, 1 removed" in out
    assert "+ 7c for each $1 over 10" in out
    assert "why watched: demo ATO page" in out
    assert "2 unchanged, 1 changed" in out


def test_changed_legislation_compilation_id(env, capsys):
    seed_all(env)
    run(env, "--update", capsys=capsys)
    put(env, "demo-legis", legis_html(comp="C2030C00002", num="C11", start="1 August 2030"))
    code, out = run(env, "--only", "demo-legis", capsys=capsys)
    assert code == 1
    assert "compilation_id: C2030C00001 -> C2030C00002" in out
    assert "effective_start: 1 July 2030 -> 1 August 2030" in out


def test_legislation_page_noise_does_not_change_it(env, capsys):
    seed_all(env)
    run(env, "--update", capsys=capsys)
    put(env, "demo-legis", legis_html(noise="zzz"))  # different Angular attribute names, same compilation
    code, out = run(env, "--only", "demo-legis", capsys=capsys)
    assert code == 0 and "1 unchanged" in out


@pytest.mark.parametrize("html,status,reason", [
    (CHALLENGE_HTML, 200, "challenge page"),
    (CHALLENGE_HTML, 403, "http 403"),
    ("<html><body>Access denied</body></html>", 429, "http 429"),
    (JS_SHELL_HTML, 200, "empty or script-rendered page"),
])
def test_blocked_pages_are_errors_never_changes(env, capsys, html, status, reason):
    seed_all(env)
    run(env, "--update", capsys=capsys)
    before = stored(env)["demo-ato"]
    put(env, "demo-ato", html, status=status)
    code, out = run(env, "--update", capsys=capsys)
    assert code == 0  # a blocked page is not a change
    assert f"error: blocked ({reason}" in out
    assert "1 error (1 blocked)" in out and "0 changed" in out
    assert stored(env)["demo-ato"] == before  # --update leaves the old fingerprint alone
    code, _ = run(env, "--strict", capsys=capsys)
    assert code == 3


def test_blocked_on_first_run_records_nothing(env, capsys):
    put(env, "demo-ato", CHALLENGE_HTML, status=403)
    put(env, "demo-legis", legis_html())
    put(env, "demo-fwo", fwo_html())
    run(env, "--update", capsys=capsys)
    assert "demo-ato" not in stored(env)


def test_normalisation_ignores_boilerplate_and_whitespace(env, capsys):
    put(env, "demo-ato", ato_html())
    put(env, "demo-legis", legis_html())
    put(env, "demo-fwo", fwo_html())
    run(env, "--update", capsys=capsys)
    first = stored(env)
    # Same content, different chrome: banner, menu, footer, template whitespace, entities, curly dashes, updated date.
    noisy = ato_html(banner="<div id='banners'>Cookie notice, new banner 12345</div>", nav="Totally different menu",
                     footer="Different footer text", sep="\n\n      \n", last_updated="9 September 2031")
    noisy = noisy.replace("0 - 10", "0&nbsp;&ndash; 10").replace("10 - 20", "10 –   20")
    put(env, "demo-ato", noisy)
    put(env, "demo-fwo", fwo_html(banner="<div>Survey banner</div>", updated="2031-09-09"))
    code, out = run(env, capsys=capsys)
    assert code == 0, out
    assert "3 unchanged" in out
    assert "metadata moved with identical text: last_updated: 1 January 2030 -> 9 September 2031" in out
    _, _ = run(env, "--update", capsys=capsys)
    after = stored(env)
    assert after["demo-ato"]["sha256"] == first["demo-ato"]["sha256"]
    assert after["demo-ato"]["meta"]["last_updated"] == "9 September 2031"  # metadata still refreshed
    assert after["demo-ato"]["changed_at"] == "2030-02-01"  # text never changed


def test_script_and_style_content_is_not_fingerprinted():
    page = _page("ato")
    a = lw.extract_page(page, lw.FetchResult(200, ato_html()))
    b = lw.extract_page(page, lw.FetchResult(200, ato_html().replace("Do not fingerprint me 999", "changed script 111")))
    assert a.sha256 == b.sha256
    assert not any("fingerprint me" in blk for blk in a.blocks)


def test_update_writes_fingerprints(env, capsys):
    seed_all(env)
    assert not env.fp.exists()
    run(env, "--update", capsys=capsys)
    data = json.loads(env.fp.read_text())
    assert data["schema"] == 1
    ato = data["pages"]["demo-ato"]
    assert ato["mode"] == "text" and len(ato["sha256"]) == 64 and ato["chars"] > 200
    assert ato["checked_at"] == "2030-02-01" and ato["changed_at"] == "2030-02-01"
    assert ato["meta"] == {"last_updated": "1 January 2030"} and ato["url"] == "https://www.ato.gov.au/demo"
    assert len(ato["blocks"].split()) == 8  # blocks stored as short hashes only, not the text
    assert "Demo paragraph" not in env.fp.read_text()
    legis = data["pages"]["demo-legis"]
    assert legis["mode"] == "meta" and "blocks" not in legis and legis["meta"]["compilation_id"] == "C2030C00001"
    assert data["pages"]["demo-fwo"]["meta"]["last_updated"] == "2030-01-01"


def test_check_without_update_never_writes(env, capsys):
    seed_all(env)
    run(env, capsys=capsys)
    assert not env.fp.exists()


def test_update_refreshes_checked_at_and_tracks_changed_at(env, capsys):
    seed_all(env)
    run(env, "--update", capsys=capsys)
    code = lw.main(["check", "--pages", str(env.pages), "--fingerprints", str(env.fp), "--offline", str(env.off),
                    "--checked-at", "2030-03-01", "--update"])
    assert code == 0
    p = stored(env)["demo-ato"]
    assert p["checked_at"] == "2030-03-01" and p["changed_at"] == "2030-02-01"
    put(env, "demo-ato", ato_html(rows=(("0 - 10", "Nil"), ("10 - 20", "9c"))))
    lw.main(["check", "--pages", str(env.pages), "--fingerprints", str(env.fp), "--offline", str(env.off),
             "--checked-at", "2030-04-01", "--update"])
    assert stored(env)["demo-ato"]["changed_at"] == "2030-04-01"


def test_only_limits_pages_and_rejects_unknown_id(env, capsys):
    seed_all(env)
    code, out = run(env, "--only", "demo-fwo", "--update", capsys=capsys)
    assert "1 pages" in out and list(stored(env)) == ["demo-fwo"]
    code, _ = run(env, "--only", "nope", capsys=capsys)
    assert code == 2


def test_missing_offline_fixture_is_an_error_not_a_change(env, capsys):
    put(env, "demo-ato", ato_html())
    code, out = run(env, "--only", "demo-legis", capsys=capsys)
    assert code == 0 and "error: no offline fixture" in out


def test_orphan_fingerprints_are_reported(env, capsys):
    seed_all(env)
    run(env, "--update", capsys=capsys)
    data = json.loads(env.fp.read_text())
    data["pages"]["retired-page"] = {"sha256": "x"}
    env.fp.write_text(json.dumps(data))
    _, out = run(env, capsys=capsys)
    assert "no longer in pages.yaml: retired-page" in out
    _, out = run(env, "--only", "demo-fwo", capsys=capsys)
    assert "no longer in pages.yaml: retired-page" in out and "demo-ato" not in out.split("no longer in pages.yaml")[1]


# ------------------------------------------------------------------ extraction details

def _page(profile, **extract):
    profiles = yaml.safe_load(REAL_PAGES.read_text())["profiles"]
    hints = dict(profiles[profile])
    hints.update(extract)
    return lw.Page("t", "https://example.gov.au/t", "test", profile, [], hints)


def test_table_cells_and_list_items_stay_separate_blocks():
    page = _page("generic", min_chars=1)
    html_ = "<body><table><tr><td>18,201</td><td>15c</td></tr></table><ul><li>one<li>two</ul><p>a<br>b</p></body>"
    ex = lw.extract_page(page, lw.FetchResult(200, html_))
    assert ex.blocks == ["18,201", "15c", "one", "two", "a", "b"]


def test_inline_markup_joins_into_one_block():
    page = _page("generic", min_chars=1)
    ex = lw.extract_page(page, lw.FetchResult(200, "<p>The <a href='/x'>Div&nbsp;7A</a> rate is <strong>8.37%</strong>.</p>"))
    assert ex.blocks == ["The Div 7A rate is 8.37%."]


def test_exclude_start_end_and_strip_hints():
    body = ("<body><div id='m'><div class='ad'>Advert text</div><p>Intro line</p><p>START HERE</p><p>Real content</p>"
            "<p>Ref 12345 ref</p><p>END HERE</p><p>After end</p></div><p>outside</p></body>")
    page = _page("generic", select="div#m", exclude=[".ad"], start="START HERE", end="END HERE",
                 strip=[r"\d{5}"], min_chars=1)
    ex = lw.extract_page(page, lw.FetchResult(200, body))
    assert ex.blocks == ["START HERE", "Real content", "Ref ref"]


def test_missing_start_anchor_is_an_extraction_error():
    page = _page("generic", start="NOT THERE", min_chars=1)
    with pytest.raises(lw.PageError) as exc:
        lw.extract_page(page, lw.FetchResult(200, "<p>hello</p>"))
    assert exc.value.kind == "extraction"


def test_selector_matching_nothing_is_reported_blocked():
    page = _page("ato")
    with pytest.raises(lw.PageError) as exc:
        lw.extract_page(page, lw.FetchResult(200, "<html><body><p>" + "text " * 100 + "</p></body></html>"))
    assert exc.value.kind == "blocked" and "matched nothing" in exc.value.detail


def test_expect_strings_guard_script_rendered_pages():
    page = _page("generic", expect=["Land tax"], min_chars=5)
    with pytest.raises(lw.PageError):
        lw.extract_page(page, lw.FetchResult(200, "<p>Loading, please wait...</p>"))
    assert lw.extract_page(page, lw.FetchResult(200, "<p>Land tax rates</p>")).blocks == ["Land tax rates"]


def test_prefix_and_contains_attribute_selectors():
    page = _page("generic", select="section[id^=content-body]", min_chars=1)
    html_ = "<section id='content-nav'>nav</section><section id='content-body-1f'>body <b>text</b></section><p>tail</p>"
    assert lw.extract_page(page, lw.FetchResult(200, html_)).blocks == ["body text"]


@pytest.mark.parametrize("bad", ["", "div p", "a > b", "a, b", "div[", "#"])
def test_bad_selectors_rejected(bad):
    with pytest.raises(lw.ConfigError):
        lw.parse_selector(bad)


def test_challenge_detection_is_narrow():
    ok = lw.FetchResult(200, "<html><body><p>Our form has a CAPTCHA field to stop spam.</p></body></html>")
    assert lw.detect_challenge(ok) is None
    assert lw.detect_challenge(lw.FetchResult(200, CHALLENGE_HTML)) == "challenge page"
    assert lw.detect_challenge(lw.FetchResult(403, "")) == "http 403"
    assert lw.detect_challenge(lw.FetchResult(404, "Not found")) is None


def test_http_404_is_an_error_but_not_blocked(env, capsys):
    put(env, "demo-ato", "<html><body>Page not found " + "x" * 300 + "</body></html>", status=404)
    code, out = run(env, "--only", "demo-ato", capsys=capsys)
    assert code == 0 and "error: http 404" in out and "0 blocked" in out


# ------------------------------------------------------------------ fetch layer (no network)

class FakeResp:
    def __init__(self, body: bytes, status=200, headers=None):
        self._body, self.status, self._pos = body, status, 0
        self.headers = headers or {"Content-Type": "text/html; charset=utf-8"}

    def read(self, n=-1):
        end = len(self._body) if n is None or n < 0 else self._pos + n
        chunk, self._pos = self._body[self._pos:end], min(end, len(self._body))
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_fetch_url_decodes_gzip_and_sends_identifying_agent(monkeypatch):
    seen = {}

    def fake(req, timeout):
        seen["ua"], seen["timeout"] = req.get_header("User-agent"), timeout
        return FakeResp(gzip.compress("<p>café</p>".encode()), headers={"Content-Type": "text/html", "Content-Encoding": "gzip"})

    monkeypatch.setattr(lw, "_urlopen", fake)
    res = lw.fetch_url("https://example.gov.au/x", timeout=7)
    assert res.status == 200 and res.body == "<p>café</p>"
    assert seen["ua"].startswith("au-accounting-law-watch/") and seen["timeout"] == 7


def test_fetch_url_maps_http_error_and_network_error(monkeypatch):
    def forbidden(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {"Server": "cloudflare"}, io.BytesIO(b"<title>Just a moment...</title>"))

    monkeypatch.setattr(lw, "_urlopen", forbidden)
    res = lw.fetch_url("https://example.gov.au/x")
    assert res.status == 403 and "just a moment" in res.body.lower() and res.headers["server"] == "cloudflare"

    def down(req, timeout):
        raise urllib.error.URLError("name resolution failed")

    monkeypatch.setattr(lw, "_urlopen", down)
    res = lw.fetch_url("https://example.gov.au/x")
    assert res.status == 0 and "URLError" in res.error


def test_network_fetcher_is_polite_and_honours_robots():
    calls, sleeps, now = [], [], [0.0]

    def fake_fetch(url, timeout):
        calls.append(url)
        if url.endswith("/robots.txt"):
            return lw.FetchResult(200, "User-agent: *\nDisallow: /private/\n")
        return lw.FetchResult(200, "<p>ok</p>")

    def sleep(s):
        sleeps.append(round(s, 3))
        now[0] += s

    f = lw.NetworkFetcher(delay=3.0, sleep=sleep, clock=lambda: now[0], fetch=fake_fetch)
    open_page = lw.Page("a", "https://example.gov.au/public", "x")
    other_page = lw.Page("b", "https://example.gov.au/other", "x")
    closed_page = lw.Page("c", "https://example.gov.au/private/x", "x")
    other_host = lw.Page("d", "https://other.gov.au/x", "x")
    assert f(open_page).status == 200
    assert f(other_page).status == 200
    assert f(closed_page).error.startswith("robots:")
    assert f(other_host).status == 200
    assert calls.count("https://example.gov.au/robots.txt") == 1  # cached per host
    assert "https://example.gov.au/private/x" not in calls  # never requested
    assert sleeps and all(s == pytest.approx(3.0, abs=0.01) for s in sleeps)  # same-host requests spaced by the delay
    assert calls[-2:] == ["https://other.gov.au/robots.txt", "https://other.gov.au/x"]


def test_network_fetcher_stops_asking_a_host_that_keeps_refusing():
    calls = []

    def fake_fetch(url, timeout):
        calls.append(url)
        return lw.FetchResult(403, "<title>Access Denied</title>") if not url.endswith("robots.txt") else lw.FetchResult(404, "")

    f = lw.NetworkFetcher(delay=0, sleep=lambda s: None, fetch=fake_fetch, max_blocked=3)
    results = [f(lw.Page(f"p{i}", f"https://www.example.gov.au/p{i}", "x")) for i in range(6)]
    assert [r.status for r in results] == [403, 403, 403, 0, 0, 0]
    assert results[3].error.startswith("blocked: www.example.gov.au refused or did not answer 3 requests in a row")
    assert len([c for c in calls if not c.endswith("robots.txt")]) == 3  # nothing further was sent
    # Unanswered requests count the same way (a silent drop is a block too).
    quiet = lw.NetworkFetcher(delay=0, sleep=lambda s: None, max_blocked=2,
                              fetch=lambda url, t: lw.FetchResult(error="TimeoutError: The read operation timed out"))
    assert [quiet(lw.Page(str(i), f"https://q.gov.au/{i}", "x")).error.split(":")[0] for i in range(3)] == ["TimeoutError", "TimeoutError", "blocked"]
    # A different host is unaffected, and a success resets the streak.
    other = lw.NetworkFetcher(delay=0, sleep=lambda s: None, max_blocked=2,
                              fetch=lambda url, t: lw.FetchResult(403 if url.endswith("/bad") else 200, "<p>x</p>"))
    seq = [other(lw.Page("a", "https://h.gov.au/bad", "x")).status, other(lw.Page("b", "https://h.gov.au/ok", "x")).status,
           other(lw.Page("c", "https://h.gov.au/bad", "x")).status, other(lw.Page("d", "https://h.gov.au/ok", "x")).status]
    assert seq == [403, 200, 403, 200]


def test_skipped_host_is_reported_as_blocked_error(env, capsys):
    def refusing(page):
        return lw.FetchResult(error="blocked: www.ato.gov.au refused or did not answer 3 requests in a row, so this one was not sent")

    code = lw.main(["check", "--pages", str(env.pages), "--fingerprints", str(env.fp), "--only", "demo-ato"], fetcher=refusing)
    out = capsys.readouterr().out
    assert code == 0 and "error: blocked (www.ato.gov.au refused or did not answer 3 requests in a row" in out and "1 error (1 blocked)" in out


def test_robots_challenge_page_means_no_restrictions():
    f = lw.NetworkFetcher(delay=0, sleep=lambda s: None,
                          fetch=lambda url, t: lw.FetchResult(403, "Just a moment...") if url.endswith("robots.txt") else lw.FetchResult(200, "<p>x</p>"))
    assert f(lw.Page("a", "https://example.gov.au/x", "x")).status == 200


def test_main_uses_injected_fetcher_and_reports_network_errors(env, capsys):
    def fetcher(page):
        return lw.FetchResult(error="TimeoutError: timed out") if page.id == "demo-ato" else lw.FetchResult(200, fwo_html() if page.id == "demo-fwo" else legis_html())

    code = lw.main(["check", "--pages", str(env.pages), "--fingerprints", str(env.fp), "--checked-at", "2030-02-01"], fetcher=fetcher)
    out = capsys.readouterr().out
    assert "error: TimeoutError (timed out)" in out and "2 new" in out and code == 1


def test_save_option_writes_pages_usable_offline(env, capsys):
    def fetcher(page):
        return lw.FetchResult(200, {"demo-ato": ato_html(), "demo-fwo": fwo_html(), "demo-legis": legis_html()}[page.id])

    saved = env.tmp / "saved"
    lw.main(["check", "--pages", str(env.pages), "--fingerprints", str(env.fp), "--save", str(saved), "--update"], fetcher=fetcher)
    capsys.readouterr()
    assert (saved / "demo-ato.html").read_text() == ato_html()
    assert lw.main(["check", "--pages", str(env.pages), "--fingerprints", str(env.fp), "--offline", str(saved)]) == 0


# ------------------------------------------------------------------ configuration

def test_real_watch_list_is_valid():
    pages = lw.load_pages(REAL_PAGES)
    ids = [p.id for p in pages]
    assert len(ids) == len(set(ids)) and len(pages) >= 50
    urls = [p.url for p in pages]
    assert len(urls) == len(set(urls)), "duplicate URLs on the watch list"
    for p in pages:
        assert p.url.startswith("https://") and p.why.strip()
        assert p.profile  # every page names a profile (load_pages already checks it exists)
    kinds = {p.id.split("-")[0] for p in pages}
    assert {"ato", "legis", "revenuesa", "asic", "fwo"} <= kinds


def test_real_watch_list_covers_the_required_sources():
    urls = {p.url for p in lw.load_pages(REAL_PAGES)}
    assert "https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents" in urls
    assert "https://www.legislation.gov.au/C2004A05138/latest/text" in urls  # ITAA 1997
    assert any("revenuesa.sa.gov.au" in u for u in urls)
    assert any("asic.gov.au" in u and "fees" in u for u in urls)
    assert any("fairwork.gov.au" in u and "public-holidays" in u for u in urls)


def test_stored_fingerprints_match_the_watch_list():
    data = json.loads(REAL_FINGERPRINTS.read_text())
    ids = {p.id for p in lw.load_pages(REAL_PAGES)}
    assert data["schema"] == 1
    assert set(data["pages"]) <= ids, "fingerprints for ids that are not on the watch list"
    for pid, fp in data["pages"].items():
        assert len(fp["sha256"]) == 64 and fp["checked_at"] and fp["mode"] in {"text", "meta"}, pid


def test_every_watched_page_names_what_depends_on_it():
    """Each `why` must say which figure keys (dotted names) or skills depend on the page, and every key it names exists."""
    import re
    rates = "".join(f.read_text() for f in (ROOT / "data" / "rates").rglob("*.yaml"))
    skills = {d.name for d in (ROOT / "skills").iterdir() if d.is_dir()}
    for p in lw.load_pages(REAL_PAGES):
        keys = re.findall(r"\b([a-z0-9_]+\.[a-z0-9_]+)\b", p.why)
        keys = [k for k in keys if not k.endswith((".yaml", ".md"))]
        assert keys or p.skills or "data/holidays" in p.why, f"{p.id}: why names no figure key or skill"
        assert set(p.skills) <= skills, f"{p.id}: unknown skill {set(p.skills) - skills}"
        for k in keys:
            assert k.split(".", 1)[1] in rates, f"{p.id}: figure key {k} is not in data/rates"
        if p.profile == "legislation-gov-au":
            assert p.skills, f"{p.id}: legislation page lists no dependent skills"


def test_config_errors(tmp_path):
    def load(doc):
        f = tmp_path / "p.yaml"
        f.write_text(yaml.safe_dump(doc))
        return lw.load_pages(f)

    base = {"id": "a", "url": "https://x.gov.au/a", "why": "w"}
    assert load({"pages": [base]})[0].id == "a"
    for bad in ({**base, "url": "http://x.gov.au/a"}, {**base, "why": ""}, {**base, "id": "Bad_Id"}, {**base, "profile": "nope"},
                {**base, "extra": 1}, {**base, "extract": {"selectr": "x"}}, {**base, "extract": {"strip": ["("]}},
                {**base, "extract": {"fingerprint": {"mode": "meta", "keys": ["missing"]}}}):
        with pytest.raises(lw.ConfigError):
            load({"pages": [bad]})
    with pytest.raises(lw.ConfigError):
        load({"pages": [base, base]})
    with pytest.raises(lw.ConfigError):
        load({"nope": []})


def test_list_command(capsys):
    assert lw.main(["list"]) == 0
    out = capsys.readouterr().out
    assert "ato-tax-rates-resident" in out and "pages," in out.strip().splitlines()[-1]


def test_list_marks_pages_without_a_fingerprint(env, capsys):
    seed_all(env)
    run(env, "--only", "demo-fwo", "--update")
    capsys.readouterr()
    assert lw.main(["list", "--pages", str(env.pages), "--fingerprints", str(env.fp)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert not any("[no fingerprint]" in ln for ln in lines if ln.startswith("demo-fwo"))
    assert all("[no fingerprint]" in ln for ln in lines if ln.startswith(("demo-ato", "demo-legis")))
    assert lines[-1].startswith("3 pages, 2 without a fingerprint")


def test_page_without_fingerprint_is_new_not_changed(env, capsys):
    seed_all(env)
    run(env, "--only", "demo-ato", "--update")
    capsys.readouterr()
    code, out = run(env, capsys=capsys)  # demo-ato has a baseline, the other two do not
    assert code == 1
    assert sum(1 for ln in out.splitlines() if ln.startswith("new ") and "demo-" in ln) == 2 and "CHANGED" not in out
    assert "1 unchanged, 0 changed, 2 new" in out


def test_fetch_url_gives_up_when_a_server_trickles_bytes(monkeypatch):
    class Slow(FakeResp):
        def read(self, n=-1):
            ticks[0] += 10.0  # each chunk takes 10 s of wall-clock time
            return b"x" * 10

    ticks = [0.0]
    monkeypatch.setattr(lw, "_urlopen", lambda req, timeout: Slow(b""))
    res = lw.fetch_url("https://example.gov.au/x", timeout=25, clock=lambda: ticks[0])
    assert res.status == 0 and "TimeoutError" in res.error and "timed out" in res.error


def test_fetch_url_rejects_oversized_responses(monkeypatch):
    monkeypatch.setattr(lw, "MAX_BYTES", 100)
    monkeypatch.setattr(lw, "_urlopen", lambda req, timeout: FakeResp(b"x" * 500))
    res = lw.fetch_url("https://example.gov.au/x")
    assert res.status == 0 and "over" in res.error


def test_overall_cap_stops_the_run_and_reports_unfetched_pages(env, capsys):
    seed_all(env)
    now = [0.0]

    def slow_fetcher(page):
        now[0] += 400.0  # every page "takes" 400 s
        return lw.FetchResult(200, (env.off / f"{page.id}.html").read_text())

    pages = lw.load_pages(env.pages)
    rep = lw.run_check(pages, slow_fetcher, {"schema": 1, "pages": {}}, "2030-02-01", max_seconds=500, clock=lambda: now[0])
    assert [r.status for r in rep.results] == ["new", "new", "error"]
    assert "time limit" in rep.results[2].detail and rep.exit_code() == 1
    assert rep.exit_code(strict=True) == 1  # changed/new still outranks strict errors
    unlimited = lw.run_check(pages, slow_fetcher, {"schema": 1, "pages": {}}, "2030-02-01", max_seconds=0, clock=lambda: now[0])
    assert [r.status for r in unlimited.results] == ["new"] * 3


def test_cli_exposes_timeout_and_overall_cap():
    args = lw.build_parser().parse_args(["check"])
    assert args.timeout == lw.DEFAULT_TIMEOUT and args.max_seconds == lw.DEFAULT_MAX_SECONDS > 0
    args = lw.build_parser().parse_args(["check", "--timeout", "5", "--max-seconds", "60"])
    assert args.timeout == 5 and args.max_seconds == 60


def test_module_never_touches_the_network_in_tests(monkeypatch):
    """Guard: if any test above forgot to inject a fetcher, the real opener would be called; make that loud."""
    def boom(*a, **k):
        raise AssertionError("network access attempted")

    monkeypatch.setattr(lw, "_urlopen", boom)
    with pytest.raises(AssertionError):
        lw.fetch_url("https://example.gov.au/")
