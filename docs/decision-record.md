# Decision Record: CollectionsScanner vs. trove-os

**Date:** 2026-06-18
**Decision:** Keep CollectionsScanner alive as a **thin, offline-tolerant capture client**, feeding a queue that `trove-os` imports later. Build the importer in `trove-os`.

This document is the rationale. See also:
- [`capture-client-spec.md`](./capture-client-spec.md) — what the capture client must do.
- [`trove-import-mapping.md`](./trove-import-mapping.md) — how captured data lands in the Trove schema.
- GitHub issues in this repo — the task list (#1 is labeled `next`).

---

## 1. What this repo actually is (inventory)

The entire repo is **`main.py`, ~40 lines** (plus README/REQUIREMENTS). It is a working
proof-of-concept, not a tool.

**What it does**
- Reads lines from stdin in a loop until you type `DONE` — keyboard-wedge friendly
  (the scanner types digits + Enter).
- For each ISBN: calls **Google Books** (title, author) and **Open Library** (Dewey/DDC).
- Buffers `title;author;isbn;DDC;house` rows in memory and prints them all at the end as
  semicolon-separated text to paste into a database.

**What it does NOT do — and these are exactly the move-critical gaps**
- **No offline tolerance.** Every scan makes two synchronous HTTP calls. No internet = no capture.
- **Not crash-safe.** Output lives in an in-memory list and only prints at `DONE`. A crash,
  Ctrl-C, or dead network mid-session loses the whole box.
- **Fragile happy-path only.** `volume_info.get("authors")[0]` raises `IndexError` on any book
  with no author returned; an unknown/typo'd ISBN → empty results → likely crash. One bad scan
  kills the run.
- **Books only.** No UPC path, no collection-type switching, despite README aspirations
  (FILM, VIDEO_GAMES, BOARD_GAMES, …).
- **No box/location batching.** Location is hardcoded `;house`.
- **No persistent storage or Trove-shaped export** — just stdout text.

**Completeness: ~15%.** It proves ISBN lookup works and that keyboard-wedge `input()` capture is
trivial. Everything that makes it survivable during a move is absent. The reusable nugget is the
ISBN-lookup logic (Google Books + Open Library), which should be **ported** (with bug fixes) rather
than depended on as-is.

## 2. Options considered

1. **Fold in** — CollectionsScanner becomes Trove's scanning module; archive this repo.
2. **Capture client** — survives as a thin offline capture tool (scan → box label → queue →
   import to Trove later).
3. **Archive** — if Trove's planned scanner support covers everything.

## 3. Recommendation: capture client (option 2), built in trove-os

Optimized for **move-useful over elegant**, given a one-time packing window of as little as 30 days.

- **Trove's scanner/import support is planned, not built; the move is now.** Betting capture on an
  unbuilt import path against a hard deadline is the high-risk option. **Fold-in fails the timeline.**
- **Archive throws away the one working thing** (ISBN lookup) and forfeits the packing window. Rejected.
- **Capture client is decoupled and cheap.** Its whole value — offline-first, crash-safe, box-batched
  capture that emits a queue Trove imports *later* — is exactly the ~85% this script lacks, and it is a
  few hundred lines of stdlib Python. Trove need not be ready during the move; it just consumes the queue
  afterward.
- It **de-risks Trove**: the queue file becomes a clean, replayable import fixture, and this lookup logic
  is the prototype for Trove's eventual scanner module. Capture-client *feeds* a future fold-in rather than
  competing with it.

**The one reframe that matters:** capture must do **zero network at scan time** — scan → append raw
code + box to disk instantly → resolve titles later (or let Trove resolve them). That single change turns
a brittle demo into something trustworthy over a weekend of packing.

## 4. Why build it in trove-os (user direction, 2026-06-18)

`trove-os` is a brand-new repo with the schema already designed. Rather than evolve this repo, **build the
capture client and its importer in `trove-os`**, copying/porting the small amount of reusable code from here.
This document set is the source of truth for that work. CollectionsScanner remains the historical reference
and the home of these design notes and issues.

## 5. Schema reality check (from `waregin/trove-os/trove_schema.sql`)

Reading the actual schema made the MVP **leaner**:

- `items.collection_type` (TEXT) selects a per-type extension table
  (`item_print_books`, `item_games`, `item_lego`, `item_films`, `item_plushies`, `item_nicky_nacks`,
  `item_home_inventory`, `item_ebooks`).
- `storage_locations` is per-user, named, hierarchical (self-FK `parent_id`). A **box = a
  `storage_locations.name`**; items reference it by `storage_location_id` (UUID) + free-text `location_notes`.
- `external_id_cache` (`id_type` ∈ isbn/upc/igdb/lego_set, `source` ∈ open_library/igdb/upc_item_db,
  `payload` JSONB) means **Trove already owns barcode resolution server-side.**
- **No staging/import table exists yet** — confirms the import path is unbuilt and the decoupled
  capture-client approach is correct.

**Consequence:** the capture client does not *need* to resolve anything. Minimal move-ready path is
**capture → export → run on Zorin**. Optional title lookup at capture time is only for in-hand verification.

## 6. Open decisions handed to the trove-os session

1. **Box → location resolution.** Recommended default: export carries the box **name**; the Trove importer
   upserts a `storage_locations` row (creating it if absent) and resolves `storage_location_id`. Alternative:
   pre-seed locations in Trove and reference by id. **User undecided — confirm in the trove-os session.**
2. **New collection types.** Decided (2026-06-18): **`board_games` and `puzzles` each become a new
   `collection_type`** in Trove (not folded into `nicky_nacks`). The schema needs the new `collection_type`
   values and, if they carry type-specific fields, new `item_board_games` / `item_puzzles` extension tables
   (otherwise they can exist as collection_type values with no extension row, like `item_nicky_nacks`).
