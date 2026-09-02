import type { Puzzle, PuzzleWord } from '@/types/models';
import { localISODate } from './dates';

interface Corpus {
  anchor: string;
  lastDate: string;
  count: number;
  puzzles: Puzzle[];
}

/**
 * The whole corpus ships inside the binary — see
 * puzzle-pipeline/publish_puzzles.py. No backend, no per-request cost, and
 * every puzzle works offline.
 *
 * Required lazily, not at module scope: it is a few MB of JSON, and paying
 * that parse during app startup would delay the first paint for a file the
 * home screen doesn't need until someone opens a puzzle. `require` caches,
 * so the cost is paid once.
 */
let cache: { corpus: Corpus; byDate: Map<string, Puzzle> } | null = null;

function load() {
  if (!cache) {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    const corpus = require('./corpus.json') as Corpus;
    cache = {
      corpus,
      byDate: new Map(corpus.puzzles.map((p) => [p.date, p])),
    };
  }
  return cache;
}

/** First and last dates the corpus covers. */
export function puzzleDateRange(): { first: string; last: string } {
  const { corpus } = load();
  return { first: corpus.anchor, last: corpus.lastDate };
}

export function hasPuzzleFor(date: string): boolean {
  return load().byDate.has(date);
}

/**
 * The date whose puzzle counts as "today's". Normally just today, but the
 * corpus is finite: once the calendar runs past the last published puzzle
 * this holds at the newest one rather than showing an empty screen. Shipping
 * more puzzles is a content update, not a code change.
 */
export function currentPuzzleDate(today: string = localISODate()): string {
  const { first, last } = puzzleDateRange();
  if (today < first) return first;
  if (today > last) return last;
  // Every date in range has a puzzle: publish assigns them consecutively.
  return today;
}

/** Puzzle for a date, falling back to the nearest published one. */
export function getPuzzle(date: string): Puzzle {
  const { byDate } = load();
  return byDate.get(date) ?? byDate.get(currentPuzzleDate(date))!;
}

export function wordCells(word: PuzzleWord): { row: number; col: number }[] {
  return Array.from({ length: word.length }, (_, i) =>
    word.direction === 'across'
      ? { row: word.row, col: word.col + i }
      : { row: word.row + i, col: word.col },
  );
}

export function wordAt(
  puzzle: Puzzle,
  row: number,
  col: number,
  direction: 'across' | 'down',
): PuzzleWord | null {
  return (
    puzzle.words.find(
      (w) =>
        w.direction === direction &&
        wordCells(w).some((c) => c.row === row && c.col === col),
    ) ?? null
  );
}

export function isWordComplete(
  word: PuzzleWord,
  letters: Record<string, string>,
): boolean {
  return wordCells(word).every(
    (c, i) => letters[`${c.row},${c.col}`] === word.answer[i],
  );
}
