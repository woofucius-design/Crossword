import type { Puzzle, PuzzleWord } from '@/types/models';
import { samplePuzzle } from './samplePuzzle';

/**
 * Puzzle access layer. Production fetches a static JSON file per day from
 * Supabase Storage and caches it in AsyncStorage; for now every date resolves
 * to the bundled sample puzzle.
 */
export function getPuzzle(_date: string): Puzzle {
  return samplePuzzle;
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
