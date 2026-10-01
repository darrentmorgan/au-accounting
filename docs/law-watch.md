# Law-change watch

`scripts/law_watch.py` checks a listed set of primary-source pages against stored fingerprints and reports what changed. It is an alert for a person, not a source of figures: when a page moves, someone reads it, updates `data/rates/` through the normal verification path (CONVENTIONS section 2), and only then refreshes the fingerprint. Nothing here is scheduled; running it on a timer needs the project owner's approval.

## Files

| File | What it holds |
|---|---|
| `data/law_watch/pages.yaml` | The watch list: `id`, `url`, `why` (figure keys and skills that depend on the page, and any null or SUSPECT figure a change might publish), `profile`, optional `extract` overrides. The header comment lists what is in and out of scope and every extraction hint. |
| `data/law_watch/fingerprints.json` | Per page: SHA-256 of the normalised extracted text (or of the compilation id and effective date for legislation.gov.au), a short hash per text block, the metadata seen (`last_updated`, `compilation_id`), `checked_at` and `changed_at`. No page text is stored. |
| `tests/unit/test_law_watch.py` | Fixture-only tests, no network. |

## Usage

```
uv run scripts/law_watch.py list                         # marks pages with no stored fingerprint
uv run scripts/law_watch.py check                        # every page, one polite request each, prints changed / unchanged / error
uv run scripts/law_watch.py check --only 'legis-*'       # ids or globs, repeatable
uv run scripts/law_watch.py check --update               # also write new fingerprints (changed, new and unchanged pages)
uv run scripts/law_watch.py check --offline saved/       # read saved/<id>.html instead of fetching
uv run scripts/law_watch.py check --save saved/          # also keep each fetched page as saved/<id>.html
uv run scripts/law_watch.py check --timeout 20 --max-seconds 600   # per-request and whole-run limits
```

Exit code: 0 nothing changed; 1 at least one page changed or has no fingerprint yet; 2 bad arguments or configuration; 3 with `--strict`, when any page errored. The exit code says what was found, not what was written, so `--update` still exits 1 when it records a change.

A changed page prints the metadata that moved (for example `compilation_id: C2026C00400 -> C2026C00500`), how many text blocks were added and removed, the added text, why the page is watched, and its URL. Old text is not kept, so removed blocks are only counted.

## What counts as a change

Only the relevant part of each page is fingerprinted, so site chrome and changing boilerplate do not raise false alarms. Per-profile hints select a region (`section#content` on ato.gov.au, `article.main` on fairwork.gov.au), drop breadcrumbs and feedback widgets, and strip "Last updated" lines from the hash while still recording them as metadata. Text is normalised before hashing (Unicode NFKC, curly quotes and dashes unified, scripts and styles ignored, whitespace collapsed). A page whose text is identical but whose "last updated" date moved is reported as unchanged with a note. legislation.gov.au pages are fingerprinted by compilation id and effective date, because the register page is large and rendered by script; a new compilation is the signal, and its publish comment is stored as metadata.

## Blocked pages

Some sites refuse scripted requests: ato.gov.au answers with an Akamai "Access Denied" page, revenuesa.sa.gov.au and legislation.sa.gov.au with a Cloudflare challenge, and some pages render their figures by script and arrive empty. The tool reports these as `error: blocked (...)`, never as a change, and never tries to get around them. It sends one request per page with an identifying User-Agent, honours robots.txt, waits between requests to a host (`--delay`, default 3 s), never retries, gives each request a wall-clock limit (`--timeout`, default 30 s, including a server that trickles bytes), caps the whole run (`--max-seconds`, default 900; pages not reached are reported as `error: time limit`), and stops asking a host that has refused three requests in a row (`--max-blocked`), reporting the rest as blocked without sending them.

When the list was built (2026-09-29) the script could fetch and fingerprint the 15 legislation.gov.au compilations, the ASIC fees sheet, the WA public-holiday review page and the ABS CPI release page. It was refused (HTTP 403) by ato.gov.au, revenuesa.sa.gov.au, legislation.sa.gov.au, safework.sa.gov.au, business.vic.gov.au and fwc.gov.au, and got no answer from fairwork.gov.au and softwaredevelopers.ato.gov.au. Those pages (78 of the 96 on the list) have no stored fingerprint yet: a page that can be fetched or supplied with `--offline` is reported as `new`, not `changed`, until a baseline is recorded with `--update`; one that is still blocked is reported as `error: blocked`. Baseline them from saved copies as described next.

For pages the script cannot fetch, a person loads the page in a browser, saves the HTML as `<id>.html` in a folder (for example `saved/`), and runs `check --offline saved/` (add `--update` to record it). Only the region named by the page's hints is read, so a normal "save page" file works. `--save DIR` keeps the pages the script did fetch in the same layout.

## When something changes

1. Open the URL and read the change against the keys in `why`. Figures and dates are edited in `data/rates/<year>.yaml` or the domain overlay, with `source` and `as_at`, and by the verification rules in CONVENTIONS section 2 (status VERIFIED only when read on the primary page; a null figure gets `checked_at`).
2. If a rule rather than a figure changed, follow the skill's `references/sources.md` and raise it for review.
3. Run `check --only <id> --update` to accept the new baseline, then `scripts/check_all.sh`.

## Adding or changing a page

Add an entry to `pages.yaml` with a profile, then run `check --only <id> --save saved/` to see whether the page can be fetched and what is extracted. If the fingerprint is noisy, add `extract` hints (`select`, `exclude`, `start`, `end`, `strip`, `min_chars`, `expect`). `expect` and `min_chars` turn an empty script-rendered shell into `error: blocked` instead of a silent fingerprint of nothing. Keep the list to primary sources.
