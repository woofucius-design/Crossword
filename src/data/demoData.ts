import type { CollectedWord, UserProfile } from '@/types/models';

/**
 * The profile a player has before they tell us anything about themselves.
 *
 * Onboarding is optional and deferred — a first-time player goes straight to
 * a puzzle — so every screen has to render against this. Streak 0 and an
 * empty collection are the honest starting values; they fill in by playing.
 */
export function guestProfile(): UserProfile {
  return {
    id: 'local',
    username: 'Player',
    avatar: 'owl',
    goal: '1400+',
    testDate: 'unsure',
    level: 'Beginner',
    streak: 0,
    classId: undefined,
    createdAt: new Date().toISOString(),
  };
}

/**
 * Development seed for populated Collection / Review / Home screens. NOT the
 * default state — see defaultState() in AppStore.
 */
export const demoUser: UserProfile = {
  id: 'demo-user',
  username: 'Alex',
  avatar: 'fox',
  goal: '1400+',
  testDate: '3months',
  level: 'Developing',
  streak: 7,
  classId: 'demo-class',
  createdAt: '2026-04-01T00:00:00.000Z',
};

function daysAgo(n: number): string {
  return new Date(Date.now() - n * 86_400_000).toISOString();
}

interface Seed {
  wordId: number;
  word: string;
  definition: string;
  mastery: CollectedWord['mastery'];
  retention: number;
  reviewCount: number;
  collected: number;
  lastReview: number | null;
}

const seeds: Seed[] = [
  { wordId: 7, word: 'ASTUTE', definition: 'having sharp judgment; shrewd and perceptive', mastery: 'mastered', retention: 96, reviewCount: 9, collected: 40, lastReview: 2 },
  { wordId: 9, word: 'PRUDENT', definition: 'acting with care and thought for the future', mastery: 'mastered', retention: 92, reviewCount: 8, collected: 38, lastReview: 3 },
  { wordId: 12, word: 'ELOQUENT', definition: 'fluent or persuasive in speaking or writing', mastery: 'mastered', retention: 90, reviewCount: 7, collected: 35, lastReview: 4 },
  { wordId: 15, word: 'PLACID', definition: 'calm and peaceful, free from disturbance', mastery: 'mastered', retention: 88, reviewCount: 7, collected: 33, lastReview: 5 },
  { wordId: 10, word: 'GREGARIOUS', definition: 'fond of company; sociable', mastery: 'strong', retention: 81, reviewCount: 5, collected: 28, lastReview: 3 },
  { wordId: 17, word: 'BENEVOLENT', definition: 'well meaning and kindly', mastery: 'strong', retention: 78, reviewCount: 5, collected: 26, lastReview: 4 },
  { wordId: 19, word: 'DILIGENT', definition: 'showing care and conscientiousness in one’s work', mastery: 'strong', retention: 76, reviewCount: 4, collected: 24, lastReview: 6 },
  { wordId: 13, word: 'ZEALOUS', definition: 'having great energy or enthusiasm for a cause', mastery: 'familiar', retention: 68, reviewCount: 3, collected: 20, lastReview: 6 },
  { wordId: 16, word: 'AUSTERE', definition: 'severe or strict in manner; plain and unadorned', mastery: 'familiar', retention: 64, reviewCount: 3, collected: 18, lastReview: 7 },
  { wordId: 20, word: 'FRUGAL', definition: 'sparing or economical with money or food', mastery: 'familiar', retention: 71, reviewCount: 3, collected: 17, lastReview: 5 },
  { wordId: 18, word: 'CACOPHONY', definition: 'a harsh, discordant mixture of sounds', mastery: 'learning', retention: 58, reviewCount: 2, collected: 12, lastReview: 5 },
  { wordId: 11, word: 'OBSTINATE', definition: 'stubbornly refusing to change one’s opinion', mastery: 'learning', retention: 52, reviewCount: 2, collected: 11, lastReview: 6 },
  { wordId: 14, word: 'MERCURIAL', definition: 'subject to sudden or unpredictable mood changes', mastery: 'learning', retention: 41, reviewCount: 1, collected: 9, lastReview: 7 },
  { wordId: 3, word: 'OPULENT', definition: 'showing great wealth; lavish; luxurious', mastery: 'learning', retention: 38, reviewCount: 1, collected: 8, lastReview: 8 },
  { wordId: 8, word: 'EPHEMERAL', definition: 'lasting for a very short time', mastery: 'learning', retention: 44, reviewCount: 1, collected: 7, lastReview: 6 },
  { wordId: 5, word: 'VERBOSE', definition: 'using or expressed in more words than are needed', mastery: 'new', retention: 100, reviewCount: 0, collected: 1, lastReview: null },
  { wordId: 6, word: 'TERSE', definition: 'briefly and cleanly expressed; curt', mastery: 'new', retention: 100, reviewCount: 0, collected: 1, lastReview: null },
  { wordId: 1, word: 'LUCID', definition: 'clear, coherent; easy to understand', mastery: 'new', retention: 100, reviewCount: 0, collected: 1, lastReview: null },
  { wordId: 2, word: 'CANDOR', definition: 'the quality of being open, honest, and direct', mastery: 'new', retention: 100, reviewCount: 0, collected: 0, lastReview: null },
  { wordId: 4, word: 'STOIC', definition: 'enduring hardship without showing feelings', mastery: 'new', retention: 100, reviewCount: 0, collected: 0, lastReview: null },
];

export const demoCollectedWords: CollectedWord[] = seeds.map((s, i) => ({
  id: `demo-${s.wordId}`,
  userId: demoUser.id,
  wordId: s.wordId,
  word: s.word,
  definition: s.definition,
  mastery: s.mastery,
  retention: s.retention,
  reviewCount: s.reviewCount,
  collectedAt: daysAgo(s.collected),
  lastReviewAt: s.lastReview === null ? null : daysAgo(s.lastReview),
  puzzleDate: new Date(Date.now() - (47 - i) * 86_400_000).toISOString().slice(0, 10),
}));
