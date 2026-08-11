/**
 * Puzzle dates are calendar days in the user's own timezone, never UTC.
 *
 * `toISOString().slice(0, 10)` is the tempting one-liner and it is wrong
 * west of UTC: at 8pm in New York it already reports tomorrow. That matters
 * here because the date string is the identity of a puzzle and the key that
 * completions and streaks are recorded under — a mismatch between two
 * screens means one records a solve under tomorrow's date, which then
 * swallows the real solve the next day as a duplicate and stalls the streak.
 */
export function localISODate(d: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** `n` days before `from`, as a local calendar date string. */
export function daysAgoISO(n: number, from: Date = new Date()): string {
  const d = new Date(from);
  d.setDate(d.getDate() - n);
  return localISODate(d);
}
