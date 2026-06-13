# CollectionsScanner — Requirements & Context

> **Decision needed:** this repo likely overlaps heavily with **trove-os** (unified collections + home inventory tool; PostgreSQL schema already designed, barcode scanner integration via ISBN/UPC lookup is in Trove's plan).

## Purpose (historical)
Scan barcodes (Reggie owns a hardware barcode scanner) to capture collection items — books, games, etc.

## The overlap question
Trove's architecture already includes barcode scanning as an input method. Plausible outcomes:
1. **Fold in:** CollectionsScanner becomes Trove's scanning input module; this repo is archived with a pointer
2. **Client/server:** CollectionsScanner survives as a thin capture client (scan → queue → Trove API), useful for offline/bulk scanning sessions during the move
3. **Archive entirely:** if Trove's planned scanner support covers everything

**Urgency update:** the sale plan means as little as 30 days to vacate once a buyer signs, and anything unmoved is lost — capture tooling has a shelf life. Option 2 has real appeal given the move: a dirt-simple "scan everything in this box into a CSV/queue now, reconcile into Trove later" tool would directly support packing and inventorying.

## Current state (Claude Code: verify)
- Unknown completeness; inventory what works (scanner input handling? ISBN/UPC lookup? storage?)

## Requirements (if option 2 chosen)
- **Functional:** Accept scanner input (keyboard-wedge style), batch by box/location label, ISBN/UPC lookup with offline fallback (store raw codes, resolve later), export queue importable by Trove
- **Non-functional:** Must work TODAY on Zorin with minimal setup — move-useful beats elegant

## First session objectives
1. Analyze repo; compare capabilities against Trove's schema/plans (paste Trove context in if available)
2. Recommend fold-in vs. capture-client vs. archive, with rationale
3. If capture-client: define the minimal move-ready version and open issues; label one `next`
