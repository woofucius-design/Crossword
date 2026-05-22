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
