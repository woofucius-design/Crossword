# Puzzle Pipeline — feasibility verification

**Question:** can a complete LEXICON crossword be built where every answer is
either an SAT vocabulary word or a clean common word — with **no pop-culture
words** (no proper nouns, brand names, titles) and no obscure crosswordese?

**Answer: yes.** This pipeline generates and validates such a puzzle end to end.
The generated Daily Mini #48 ships in the app at `src/data/samplePuzzle.ts`,
replacing the original hand-coded sample that relied on `ODEA` (plural of
*odeon* — exactly the kind of crosswordese to avoid).

## Why pop-culture words are impossible here

The fill word list is built as the **intersection of two sources**:

1. A standard English dictionary (`data/dictionary.txt`, 274k entries from the
   npm `word-list` package) — entirely lowercase common words, so proper nouns,
   brands, celebrities, and titles are **absent by construction**.
2. A frequency floor (`wordfreq`, Zipf ≥ 3.0) — drops obscure crosswordese.

The intersection is 20,701 words. A puzzle filled from it *cannot* contain a
pop-culture word, because no proper noun ever enters the candidate pool.

## Pipeline

| Step | File | Output |
|---|---|---|
| Build the clean fill list | `build_fill_list.py` | `data/clean_fill.json` |
| Generate the puzzle | `generator.py` | `output/<date>.json` |
| Validate it | `validate.py` | pass / fail report |

```bash
python3 build_fill_list.py          # dictionary ∩ frequency  -> 20,701 words
python3 generator.py --seed 19      # freeform interlocking layout
python3 validate.py output/2026-05-22.json
```

`generator.py` builds a freeform interlocking layout (the style of the design
handoff's own puzzle — not a fully-checked American grid): it seats 6 SAT theme
answers and ~8 fill words so every entry crosses another and the whole puzzle
is one connected component inside a 10×10 box.

`validate.py` confirms the result is a real crossword: answers match the grid,
crossings agree, numbering is correct, the white cells are connected, every
word interlocks, and **no unintended words** appear.

## Verified result — Daily Mini #48

```
. . . . N U A N C E
O . . . . . S . . .
B . . A U S T E R E
S . . . S . U . U .
T . . D E F T . S .
I . F . L . E C H O
N O I S E . . R . .
A . R . S T O I C .
T I M E S . . E . .
E . S . . R O S E S
```

- **SAT vocab (6):** NUANCE, ASTUTE, OBSTINATE, AUSTERE, DEFT, STOIC
- **Fill (8):** USELESS, RUSH, FIRMS, ECHO, CRIES, NOISE, TIMES, ROSES
- 14 interlocked entries · validator: **VALID**
- Every fill word is a common ≥4-letter dictionary word — zero proper nouns,
  zero crosswordese.

Seeds 7, 11, 19, 23, and 42 all produce valid puzzles, so the result is not a
lucky one-off — clean construction is consistently achievable.

## Notes / production path

- Fill clues come from `data/fill_clues.json`. In production this is the
  handoff's `clue_writer.py` step (Claude-generated clues); a curated local
  dictionary is used here so the offline run is fully self-contained.
- A fully-checked (every-cell-crossed) 10×10 was tried first. It is at the edge
  of feasibility with a 20k-word list — which is why real American crosswords
  are 15×15. The freeform interlocking layout matches the design handoff and
  fills cleanly and reliably.
