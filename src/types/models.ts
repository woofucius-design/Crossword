export type MasteryTier = 'new' | 'learning' | 'familiar' | 'strong' | 'mastered';

export type PartOfSpeech = 'noun' | 'verb' | 'adjective' | 'adverb';

export interface SATWord {
  id: number;
  word: string; // ALL CAPS
  definition: string;
  partOfSpeech: PartOfSpeech;
}

export interface CollectedWord {
  id: string;
  userId: string;
  wordId: number;
  word: string;
  definition: string;
  mastery: MasteryTier;
  retention: number; // 0-100
  reviewCount: number;
  collectedAt: string; // ISO timestamp
  lastReviewAt: string | null;
  puzzleDate: string; // YYYY-MM-DD
}

export interface Puzzle {
  date: string; // YYYY-MM-DD
  number: number;
  size: { rows: number; cols: number };
  solution: string[][]; // '#' = black square
  cells: Record<string, { number?: number; preFilled?: string }>;
  words: PuzzleWord[];
  /**
   * The SAT words this puzzle was built around, emitted by the generator
   * (see puzzle-pipeline/marquee_15.py). Present on pipeline puzzles and
   * absent on the bundled sample, so the post-solve recap falls back to
   * every isSATVocab entry.
   */
  featured?: FeaturedWord[];
}

export interface FeaturedWord {
  word: string;
  clue: string;
  definition: string;
}

export interface PuzzleWord {
  id: string; // "1A", "2D"
  number: number;
  direction: 'across' | 'down';
  row: number;
  col: number;
  length: number;
  answer: string; // ALL CAPS
  clue: string;
  isSATVocab: boolean;
  definition?: string;
  /** Sits in one of the long symmetric theme slots. */
  isMarquee?: boolean;
  /** Alternate clues for the same answer — replay variety, or a hint that
   *  re-clues instead of revealing letters. */
  altClues?: string[];
}

export interface PuzzleCompletion {
  puzzleDate: string; // YYYY-MM-DD
  puzzleNumber: number;
  durationSeconds: number;
  wordsCollected: number;
  completedAt: string; // ISO timestamp
}

export type Avatar = 'owl' | 'fox' | 'lion' | 'shark' | 'wolf' | 'eagle';
export type Goal = '1200+' | '1400+' | '1500+' | '1600';
export type TestDate = '1month' | '3months' | '6months' | '1year' | 'unsure';
export type Level = 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced';

export interface UserProfile {
  id: string;
  username: string;
  avatar: Avatar;
  goal: Goal;
  testDate: TestDate;
  level: Level;
  streak: number;
  classId?: string;
  createdAt: string;
}

export interface PassageSubmission {
  id: string;
  userId: string;
  classId?: string;
  targetWords: string[];
  passage: string;
  scores: {
    accuracy: number;
    conciseness: number;
    creativity: number;
    overall: number;
  };
  wordFeedback: Array<{
    word: string;
    used: boolean;
    correct: boolean;
    note: string;
  }>;
  feedback: string;
  submittedAt: string;
}
