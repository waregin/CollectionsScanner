# Trove Import Mapping

How a captured `queue.jsonl` row lands in the `trove-os` PostgreSQL schema.
Source: `waregin/trove-os/trove_schema.sql` (read 2026-06-18; PLpgSQL repo).

> This repo's GitHub tools were scoped to `collectionsscanner` only, so the schema below was read from
> the **public** trove-os repo over the web. Treat it as observed-at-a-point-in-time; re-confirm against
> `trove_schema.sql` when building the importer.

---

## Relevant schema (observed)

**`items`** (core inventory)
- `id` UUID PK, `user_id` UUID FK
- `collection_type` TEXT — selects the extension table
- `title`, `subtitle`, `series_title`, `series_position`
- `ownership_status` ENUM (`owned`,`wanted`,`lent_out`,`ordered`,`lost`,`given_away`,`sold`,`digital`)
- `storage_location_id` UUID FK → `storage_locations`
- `location_notes` TEXT, `notes` TEXT, `tags` TEXT[]
- `approximate_value` NUMERIC, `currency` CHAR(3), `primary_image_url`, timestamps

**`storage_locations`** — `id` UUID PK, `user_id` FK, `name` TEXT, `parent_id` self-FK (hierarchical), `notes`

**Extension tables (keyed `item_id` PK/FK → items):**
- `item_print_books` — `author` TEXT, `isbn` TEXT, `ddc` **NUMERIC**, `publisher`, `pub_year` SMALLINT, `edition`, `is_signed`, `is_special_edition`, `read_status`, `date_read`
- `item_ebooks` — `author_publisher`, `file_path`, `file_format`, `isbn`, `read_status`
- `item_films` — `year` SMALLINT, `format`, `file_path`, `watched_status`
- `item_games` — `platform`, `storefront`, `play_status`
- `item_lego` — `set_number` TEXT, `theme`, `piece_count` INTEGER, `is_built`, `is_displayed`
- `item_plushies` — `brand`, `species_type`, `size_value`, `size_system`
- `item_nicky_nacks` — (no extra columns)
- `item_home_inventory` — `manufacturer`, `model_number`, `serial_number`, `purchase_date`, `purchase_price`, `warranty_expiry`, `receipt_url`

**`external_id_cache`** — `id_type` (`isbn`/`upc`/`igdb`/`lego_set`), `external_id`, `source`
(`open_library`/`igdb`/`upc_item_db`), `payload` JSONB, UNIQUE(id_type, external_id, source).
This is Trove's server-side barcode resolver/cache — the capture client does not need to resolve.

**No staging/import table exists** — the importer is to be built.

## Column mapping (export row → Trove)

The importer inserts an `items` row, one extension row, and resolves the storage location.

| Export column | Trove target |
|---|---|
| `collection` | `items.collection_type` (use Trove values directly — see below) |
| `box` | resolve to `storage_locations.name` (upsert/create) → `items.storage_location_id`; also fill `items.location_notes` |
| `title` | `items.title` |
| `code` where `code_type=isbn` | `item_print_books.isbn` (TEXT) |
| `author` | `item_print_books.author` |
| `ddc` | `item_print_books.ddc` — **NUMERIC**, keep numeric or null (never a string) |
| `code` where `code_type=upc`/`lego_set`/`igdb` | resolution key for `external_id_cache`; **keep raw code in export** — non-book extension tables have no generic code column, so the raw code is the only reconciliation handle |
| `scanned_at` | informational → a tag, or `items.created_at` |
| (constant) | `items.ownership_status = 'owned'` |

**Always include every queue row regardless of `status`.** A never-resolved row still carries `code` + `box`,
which is the irreplaceable data captured during the move; Trove can resolve or hand-fix later.

## `collection_type` values

Have extension tables today: `print_books`, `ebooks`, `films`, `games`, `lego`, `plushies`,
`nicky_nacks`, `home_inventory`.

**New types to add (decided 2026-06-18):** `board_games` and `puzzles` each become their **own**
`collection_type` (not folded into `nicky_nacks`). The trove-os work should:
- add `board_games` and `puzzles` as valid `collection_type` values, and
- add `item_board_games` / `item_puzzles` extension tables **if** they need type-specific fields
  (e.g. board games: player count, designer; puzzles: piece count, brand). If they have no extra fields yet,
  they can exist as collection_type values with no extension row (like `nicky_nacks`) and gain a table later.

## Open decision: box → location

**Recommended default:** export carries the box **name**; the importer upserts a `storage_locations` row
(creating it if absent, optionally under a parent like a room) and sets `items.storage_location_id`. This keeps
the capture client UUID-free and offline.

**Alternative:** pre-seed `storage_locations` in Trove and have the export reference them by id — more setup,
less forgiving during packing.

**Status: user undecided (2026-06-18).** Confirm in the trove-os session before building the importer.
