import type { CollectedWord, MasteryTier } from '@/types/models';
import { colors } from '@/theme/tokens';

export function daysSince(iso: string | null): number {
  if (!iso) return 999;
  const then = new Date(iso).getTime();
  const now = Date.now();
  return Math.max(0, Math.floor((now - then) / 86_400_000));
}

const tierBonus: Record<MasteryTier, number> = {
  new: 0,
  learning: 10,
  familiar: 20,
  strong: 5,
  mastered: -10,
};

/** Higher score => more urgent to review. Drives the AI Focus Queue sort order. */
export function urgencyScore(w: CollectedWord): number {
  const retDecay = (100 - w.retention) * 1.5;
  const dayPenalty = daysSince(w.lastReviewAt) * 8;
  return retDecay + dayPenalty + tierBonus[w.mastery];
}

export interface FocusReason {
  label: string;
  color: string;
}

export function focusReason(w: CollectedWord): FocusReason {
  if (w.retention < 45) return { label: 'About to forget', color: colors.red };
  if (w.retention < 60) return { label: 'Slipping fast', color: '#F97316' };
  if (daysSince(w.lastReviewAt) >= 5) return { label: 'Long overdue', color: '#EAB308' };
  if (w.mastery === 'learning' && daysSince(w.lastReviewAt) >= 2) {
    return { label: 'Reinforce now', color: '#60A5FA' };
  }
  return { label: 'Good time to review', color: colors.mint };
}

/** A word is "due" when its retention has decayed below the comfortable threshold. */
export function isDue(w: CollectedWord): boolean {
  return w.retention < 70 || daysSince(w.lastReviewAt) >= 4;
}

export function isSlipping(w: CollectedWord): boolean {
  return w.retention < 70;
}

/** Advance mastery one tier when a review goes well. */
const tierOrder: MasteryTier[] = ['new', 'learning', 'familiar', 'strong', 'mastered'];

export function nextTier(current: MasteryTier): MasteryTier {
  const i = tierOrder.indexOf(current);
  return tierOrder[Math.min(i + 1, tierOrder.length - 1)];
}
