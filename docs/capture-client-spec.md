# Capture Client — Minimal Move-Ready Spec

Target: a dirt-simple, **offline-first, crash-safe** tool you can run on Zorin while packing.
Scan everything in a box → it lands on disk instantly → reconcile into Trove later.

> Build this in `trove-os`. Port the ISBN-lookup logic from this repo's `main.py` (with the bug
> fixes noted below). Optimize for **move-useful over elegant**.

Minimal path that is usable during packing: **capture (#1) → export (#3) → run on Zorin (#4)**.
Title lookup (#2) and UPC/type ergonomics (#5) are optional / post-move.

---

## Data model — `queue.jsonl`

One JSON object per line, appended and flushed on every scan.

```json
{"code":"9780553213113","code_type":"isbn","collection":"print_books","box":"kitchen-12","scanned_at":"2026-06-18T17:50:00Z","status":"raw","title":null,"author":null,"ddc":null}
```

| field | meaning |
|---|---|
| `code` | raw scanned string (ISBN, UPC, LEGO set #, anything) |
| `code_type` | `isbn` \| `upc` \| `lego_set` \| `unknown` (cheap heuristic; see below) |
| `collection` | a Trove `collection_type` value (see list) — set by `TYPE` command, default `print_books` |
| `box` | current box/location label, set by `BOX` command → becomes a Trove `storage_locations.name` |
| `scanned_at` | ISO-8601 UTC timestamp |
| `status` | `raw` until (optionally) enriched → `resolved` / `failed` |
| `title`/`author`/`ddc` | null at capture; filled only by the optional resolve pass (or left for Trove) |

**`code_type` heuristic:** 13 digits starting `978`/`979`, or 10 digits → `isbn`; else `upc`/`unknown`.
Resolution can refine later. Don't block capture on getting this perfect.

**`collection` values** (must match Trove `collection_type`, so export needs no remapping):
`print_books` (default), `ebooks`, `films`, `games`, `lego`, `plushies`, `nicky_nacks`,
`home_inventory`, `board_games`, `puzzles`.
> `board_games` and `puzzles` are **new** Trove collection types (decided 2026-06-18). Trove must add
> them before import; see [`trove-import-mapping.md`](./trove-import-mapping.md).

## Capture loop (issue #1 — `next`)

Behavior:
- Read stdin lines (keyboard-wedge scanner types code + Enter — works with plain `input()`).
- Each scanned code → **append one record to `queue.jsonl`, flush immediately**. No network, no blocking.
- Commands (typed by hand, or scanned as control barcodes via barcode.tec-it.com):
  - `BOX <label>` — set current box for subsequent scans. Persist the active box so a restart resumes it.
  - `TYPE <collection>` — set current collection (values above).
  - `DONE` — exit cleanly.
- **Never crash on input.** Unknown/garbage lines are captured as records too — over-capture beats dropping.

Acceptance criteria:
- Airplane mode / cable pulled → scanning still works; every code lands in `queue.jsonl`.
- Kill mid-session (Ctrl-C / `kill`) → all prior scans already on disk; restart resumes the active box.
- 50 rapid scans → 50 lines, correct box tags, no dropped/merged lines.
- Blank line / non-numeric scan does not crash the loop.

## Optional resolve-later pass (issue #2 — optional / post-move)

Trove resolves codes server-side via `external_id_cache`, so this is **not required**. The only reason to
keep it: eyeball that a title is right while the book is still in your hand.

- Separate command over `queue.jsonl`; for `status: "raw"`, `code_type: "isbn"`:
  Google Books → title/author; Open Library → ddc. Success → `resolved`; any failure → `failed`.
- **Never crash the batch.** Idempotent: skip `resolved`, retry `failed`/`raw`. Atomic write-back
  (temp file + rename).

### Reusable logic from this repo's `main.py` (port with fixes)

- Google Books: `GET https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}` → `items[0].volumeInfo`
  (`title`, `authors`).
- Open Library: `GET https://openlibrary.org/api/volumes/brief/isbn/{isbn}.json` →
  `records[*].data.classifications.dewey_decimal_class`.

**Known bugs to fix when porting:**
- `volumeInfo["authors"][0]` crashes when `authors` is missing/empty — guard it.
- No error handling on the HTTP calls — wrap, set `failed` on any exception/timeout.
- `ddc` may be a list and is **NUMERIC in Trove** — take first element and coerce to a number (or null).

## Export (issue #3 — move-critical)

Transform `queue.jsonl` → `export.csv` (+ optional JSONL) for the Trove importer. Must work even with no
resolved rows. Full column mapping in [`trove-import-mapping.md`](./trove-import-mapping.md). Always keep the
raw `code` and `box` on every row — that is the irreplaceable move data.

## Run on Zorin (issue #4 — move-critical)

- `requirements.txt` = `requests` (or confirm stdlib-only for capture; lookup needs `requests`).
- README quickstart: start a session, `BOX`/`TYPE`/`DONE` commands, where `queue.jsonl` lands, how to export.
- **Scanner sanity check:** confirm the keyboard-wedge scanner emits code + Enter into the terminal; note any
  scanner suffix config (Enter/CR). A 2-minute documented test scan avoids a packing-day surprise.
- Optional: print control-barcode strings for `BOX …` / `TYPE …` / `DONE` for hands-free commands.
