import type { SATWord } from '@/types/models';

/**
 * A small curated slice of the SAT word bank. The production app fetches the
 * full 1,500-word list from the puzzle pipeline; this seed set powers the
 * onboarding level check, starter pack, and offline fallbacks.
 */
export const satWords: SATWord[] = [
  { id: 1, word: 'LUCID', definition: 'clear, coherent; easy to understand', partOfSpeech: 'adjective' },
  { id: 2, word: 'CANDOR', definition: 'the quality of being open, honest, and direct', partOfSpeech: 'noun' },
  { id: 3, word: 'OPULENT', definition: 'showing great wealth; lavish; luxurious', partOfSpeech: 'adjective' },
  { id: 4, word: 'STOIC', definition: 'enduring hardship without showing feelings', partOfSpeech: 'adjective' },
  { id: 5, word: 'VERBOSE', definition: 'using or expressed in more words than are needed', partOfSpeech: 'adjective' },
  { id: 6, word: 'TERSE', definition: 'briefly and cleanly expressed; curt', partOfSpeech: 'adjective' },
  { id: 7, word: 'ASTUTE', definition: 'having sharp judgment; shrewd and perceptive', partOfSpeech: 'adjective' },
  { id: 8, word: 'EPHEMERAL', definition: 'lasting for a very short time', partOfSpeech: 'adjective' },
  { id: 9, word: 'PRUDENT', definition: 'acting with care and thought for the future', partOfSpeech: 'adjective' },
  { id: 10, word: 'GREGARIOUS', definition: 'fond of company; sociable', partOfSpeech: 'adjective' },
  { id: 11, word: 'OBSTINATE', definition: 'stubbornly refusing to change one’s opinion', partOfSpeech: 'adjective' },
  { id: 12, word: 'ELOQUENT', definition: 'fluent or persuasive in speaking or writing', partOfSpeech: 'adjective' },
  { id: 13, word: 'ZEALOUS', definition: 'having great energy or enthusiasm for a cause', partOfSpeech: 'adjective' },
  { id: 14, word: 'MERCURIAL', definition: 'subject to sudden or unpredictable mood changes', partOfSpeech: 'adjective' },
  { id: 15, word: 'PLACID', definition: 'calm and peaceful, free from disturbance', partOfSpeech: 'adjective' },
  { id: 16, word: 'AUSTERE', definition: 'severe or strict in manner; plain and unadorned', partOfSpeech: 'adjective' },
  { id: 17, word: 'BENEVOLENT', definition: 'well meaning and kindly', partOfSpeech: 'adjective' },
  { id: 18, word: 'CACOPHONY', definition: 'a harsh, discordant mixture of sounds', partOfSpeech: 'noun' },
  { id: 19, word: 'DILIGENT', definition: 'showing care and conscientiousness in one’s work', partOfSpeech: 'adjective' },
  { id: 20, word: 'FRUGAL', definition: 'sparing or economical with money or food', partOfSpeech: 'adjective' },
];

export const satWordMap: Record<string, SATWord> = Object.fromEntries(
  satWords.map((w) => [w.word, w]),
);

export interface QuizQuestion {
  word: string;
  definition: string;
  options: string[];
  correctIndex: number;
}

/** Multiple-choice questions for the onboarding level check + Review quiz tab. */
export function buildQuiz(words: SATWord[], count: number): QuizQuestion[] {
  const pool = [...words];
  const pick = pool.sort(() => Math.random() - 0.5).slice(0, count);
  return pick.map((w) => {
    const distractors = words
      .filter((d) => d.id !== w.id)
      .sort(() => Math.random() - 0.5)
      .slice(0, 3)
      .map((d) => d.definition);
    const options = [...distractors, w.definition].sort(() => Math.random() - 0.5);
    return {
      word: w.word,
      definition: w.definition,
      options,
      correctIndex: options.indexOf(w.definition),
    };
  });
}
