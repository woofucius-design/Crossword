import type { RecapWord } from '@/components/crossword/CompletionSheet';

export const APP_SHARE_URL = 'https://lexicon.app';

function fmtClock(total: number): string {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

/**
 * The shareable result.
 *
 * Two rules, both learned from how daily puzzle games actually spread:
 *
 * 1. No spoilers. Never the answers, never the clues — a result someone
 *    can't post until their friends have played doesn't get posted.
 * 2. It has to say something about *you*. Everyone gets the same grid on a
 *    given day, so the grid shape carries no information; the squares encode
 *    which words were new to the sharer, which differs per player and is the
 *    part worth bragging about.
 */
export function buildShareText(opts: {
  puzzleNumber: number;
  durationSeconds: number;
  words: RecapWord[];
  streak: number;
}): string {
  const { puzzleNumber, durationSeconds, words, streak } = opts;
  const newCount = words.filter((w) => w.isNew).length;

  // Gold = new to this player, green = already collected.
  const squares = words.map((w) => (w.isNew ? '🟨' : '🟩')).join('');

  const lines = [`LEXICON #${puzzleNumber} — ${fmtClock(durationSeconds)}`];
  if (squares) {
    lines.push(squares);
    lines.push(
      newCount > 0
        ? `${words.length} SAT words · ${newCount} new`
        : `${words.length} SAT words`,
    );
  }
  if (streak > 1) lines.push(`🔥 ${streak}-day streak`);
  lines.push(APP_SHARE_URL);

  return lines.join('\n');
}
