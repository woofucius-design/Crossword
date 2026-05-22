# Puzzle Pipeline — feasibility study

**Question:** can we generate a *proper fully-checked* crossword — every white
cell in both an across and a down word, so every row and column is packed with
words — that **features SAT vocabulary** and **avoids pop-culture words**? And
what grid size makes that easiest?

**Short answer:** yes, at **small sizes**. A fully-checked grid is reliably
generatable at **5×5 and 6×6**; **7×7 is a sharp difficulty cliff** and 9×9+ is
impractical with this solver. Featuring SAT words works at 5×5 (2 per puzzle)
and 6×6 (3 per puzzle). The unavoidable cost of *fully-checked* interlock is
that some fill words are obscure — tight grids leave the solver no choice.

## The dictionary

`build_fill_list.py` builds the fill list from the full English dictionary
(`data/dictionary.txt`, 274k words from the npm `word-list` package) — **269,746
words**, all lowercase common vocabulary. Capitalised proper nouns are absent,
so brands / celebrities / titles essentially cannot appear. (Caveat: a handful
of lowercased given names and foreign particles — e.g. `denis`, `los` — do leak
through; perfect proper-noun exclusion needs a curated list.) Words are
frequency-ordered (`wordfreq`) so the solver prefers familiar words.

## How it works

| Step | File |
|---|---|
| Build the fill list | `build_fill_list.py` → `data/clean_fill.json` |
| Generate a puzzle | `generator.py` (symmetric grid + constraint solver) |
| Sweep grid sizes | `size_study.py` |
| Pick the cleanest puzzle | `pick_puzzle.py` |
| Validate | `validate.py` |

`generator.py` builds a 180°-symmetric, fully-checked, connected black-square
pattern, then fills it with a constraint solver: maintained domains + forward
checking + MRV ordering + randomised restarts. Theme slots are restricted to
SAT words so the puzzle features vocabulary.

## Size study results

`python3 size_study.py` — fully-checked grids, 270k-word dictionary:

| grid | fills? | solve time | common fill | features SAT words |
|------|--------|-----------|-------------|--------------------|
| 5×5  | **100%** | 6 ms    | 75%         | 2 / puzzle, ~95% of grids |
| 6×6  | **100%** | 15 ms   | 63%         | 3 / puzzle, ~27% of grids |
| 7×7  | 33%      | 740 ms  | 21%         | 0 — not viable |
| 9×9  | ~0%      | —       | —           | 0 — not viable |
| 11×11+ | ~0%    | —       | —           | 0 — not viable |

The cliff between 6×6 and 7×7 is real: a fully-checked 7×7 is essentially a
7×7 *word square*, a famously hard object. Above that, fully-checked grids
overwhelm a from-scratch Python solver (production constructors use curated,
scored word lists and optimised fillers).

## Recommendation

**Use a 6×6 fully-checked grid** as the daily puzzle:

- generates reliably (every valid grid fills; ~1 in 4 also takes 3 forced SAT
  words, so the generator just tries a few),
- a genuine proper crossword — every row and column is words,
- features 3 SAT vocabulary words per day.

Drop to **5×5** if you want the cleanest possible fill (75% vs 63% common
words) and accept 2 SAT words per day — this is exactly why the NYT Mini is
5×5.

### The trade-off to know about

*Fully-checked* and *vocabulary-dense* pull against each other:

- A fully-checked grid forces some obscure fill at **every** size — even the
  best of 80 generated 5×5s still needed a word like `TEPA`.
- It also caps SAT words low (2–3) — SAT vocabulary is arbitrary and does not
  interlock on demand.

If featuring **6+ SAT words with all-common fill** matters more than full
checking, a **freeform interlocking layout** (loose crossings, the style of the
original design handoff) is the better tool — that is what currently ships in
`src/data/samplePuzzle.ts`.

## Sample output

`output/2026-05-22.json` — a validated fully-checked 5×5 (SAT: STOIC, TERSE):

```
. . S R I
S T O I C
T E R S E
O P T E D
P A S . .
```

A representative fully-checked 6×6 (SAT: LUCID, SERENE, STOIC):

```
. R E P . .
L U C I D .
O N A G E R
S E R E N E
. S T O I C
. . E N S .
```

Reproduce: `python3 build_fill_list.py && python3 size_study.py` and
`python3 pick_puzzle.py --size 6 --theme 3`.
