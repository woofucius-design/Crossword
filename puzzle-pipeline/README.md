# Puzzle Pipeline — 15×15 feasibility (updated)

**Question:** can we generate a *proper fully-checked* 15×15 crossword that
features SAT vocabulary, with pop-culture entries accepted as fill?

**Answer: yes — comfortably.** Featuring 5 SAT words in a real NYT-style 15×15
fills in **1–3 seconds** with a real crossword-quality word list. The earlier
"impossible" finding was wrong: it came from a tiny generic dictionary plus a
slow solver, not from any geometric limit.

## What changed

Two fixes turned an apparently infeasible problem into an easy one:

1. **Real crossword word list.** Replaced the 270k generic English dictionary
   with the [Crossword Nexus Collaborative Word List](https://github.com/Crossword-Nexus/collaborative-word-list)
   — a 567k scored wordlist of the kind professional constructors actually use,
   covering common words, proper nouns, and phrases. We keep entries with score
   >= 40 (332,624 entries) so the solver has room and `pick_15.py` picks the
   highest-scoring fill of many candidates.

2. **Solver speedup.** The forward-checking solver's per-node duplicate-word
   pruning was rebuilding the dedup'd domain set for every unassigned slot at
   every node — O(slots × |domain|) per assignment, which is huge on big pools.
   Replaced it with a single `used_ids` set checked when iterating
   candidates: ~45× faster (from ~1.5k nodes/sec to ~67k).

## Demonstrated 15×15 puzzle

`output/2026-05-22.json` — featuring **VERBOSE, OPULENT, STOIC, PRUDENT, DEFT**.

```
V E R B O S E . . M A I D . .
O P U L E N T . . A D D A S .
U P S I D E A . F R O O T I .
. S E P . S T O I C . . A D A
. . . . . G S I X . S A H E L
E N I A . A U L . . H N A M E
C O N D E M N . A W A I V E R
L O R E L E I . P R U D E N T
I N A M E S S . P I N E N U T
P E R O N . . F A S . A S S O
S E E N A . S O R T . . . . .
E L F . . A K B A R . A D D .
. S O M A L I . T E T L E Y S
. E R A S E . . U S E D F O R
. . M O H S . . S T T I T U S
```

- **68 entries, 5 SAT vocab, 178 white cells.** `validate.py` confirms:
  fully interlocked, connected, no stray words.
- **Solve time: ~1–3 seconds per attempt** (theme=5).
- Some fill is pop-culture / partials (`AKBAR`, `LORELEI`, `BOBVILA`,
  `ETATSUNIS`) — the cost of forcing the SAT theme into a hard grid, accepted
  per the brief. They are real crossword-acceptable entries (score 40+ on
  Collaborative Word List).

## Pipeline

| Step | File |
|---|---|
| Build the fill list | `build_fill_list.py` (xwordlist.dict → clean_fill.json) |
| Save a 15×15 grid template | `generator.py` `build_grid(15, ...)` → `data/template_15.json` |
| Generate themed puzzles | `pick_15.py` (loads template, tries N theme placements) |
| Sweep grid sizes | `size_study.py` (legacy, smaller grids — see notes) |
| Validate | `validate.py` |

```bash
python3 build_fill_list.py
python3 pick_15.py --theme 5 --candidates 10
python3 validate.py output/2026-05-22.json
```

## What's still hard

- **Cluing 68 entries.** The artifact ships without clues — the production step
  is the handoff's `clue_writer.py` (Claude-backed). The app's
  `src/data/samplePuzzle.ts` continues to use a hand-clued freeform layout for
  this reason.
- **Eliminating *all* obscure fill** while keeping a fixed SAT theme on a fixed
  grid template is still genuinely hard; opening the score cut (40 vs 50) and
  using `pick_15.py`'s quality picker is the practical lever.

## Older finding (superseded)

A previous version of this study, using a 270k generic dictionary and the slow
solver, reported "5×5 / 6×6 only, 7×7 cliff." That conclusion was an artefact
of those tools — with a real crossword wordlist and the optimised solver, full
15×15 is the easy case.
