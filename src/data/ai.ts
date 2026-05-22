import Constants from 'expo-constants';
import { pickFallbackPassage } from './fallbackPassages';
import type { PassageSubmission } from '@/types/models';

/**
 * Claude proxy client. All AI calls route through Supabase Edge Functions so
 * the ANTHROPIC_API_KEY never ships in the app binary. When the backend is not
 * configured (e.g. local dev / offline) every call degrades gracefully to a
 * local heuristic so the UI stays fully functional.
 */
const SUPABASE_URL: string | undefined =
  Constants.expoConfig?.extra?.supabaseUrl ?? process.env.EXPO_PUBLIC_SUPABASE_URL;
const SUPABASE_ANON_KEY: string | undefined =
  Constants.expoConfig?.extra?.supabaseAnonKey ?? process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY;

const backendConfigured = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);

export type Absurdity = 'low' | 'medium' | 'high';

async function callEdgeFunction<T>(name: string, body: unknown): Promise<T> {
  const res = await fetch(`${SUPABASE_URL}/functions/v1/${name}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${name} failed: ${res.status}`);
  return (await res.json()) as T;
}

export async function generatePassage(
  words: string[],
  absurdity: Absurdity,
): Promise<{ text: string; fromAI: boolean }> {
  if (backendConfigured) {
    try {
      const data = await callEdgeFunction<{ passage: string }>('generate-passage', {
        words,
        absurdity,
      });
      if (data.passage?.trim()) return { text: data.passage.trim(), fromAI: true };
    } catch {
      // fall through to local fallback
    }
  }
  return { text: pickFallbackPassage(words).text, fromAI: false };
}

type GradeResult = Pick<PassageSubmission, 'scores' | 'feedback' | 'wordFeedback'>;

export async function gradePassage(
  passage: string,
  targetWords: string[],
): Promise<{ result: GradeResult; fromAI: boolean }> {
  if (backendConfigured) {
    try {
      const data = await callEdgeFunction<GradeResult>('grade-passage', {
        passage,
        words: targetWords,
      });
      if (data?.scores) return { result: data, fromAI: true };
    } catch {
      // fall through to local heuristic
    }
  }
  return { result: localGrade(passage, targetWords), fromAI: false };
}

/** Local scoring heuristic — mirrors the fallback in the HTML prototype. */
function localGrade(passage: string, targetWords: string[]): GradeResult {
  const text = passage.trim();
  const lower = text.toLowerCase();
  const wordCount = text ? text.split(/\s+/).length : 0;

  const wordFeedback = targetWords.map((word) => {
    const used = new RegExp(`\\b${word.toLowerCase()}`, 'i').test(lower);
    return {
      word: word.toUpperCase(),
      used,
      correct: used,
      note: used ? 'Used in the passage — looks in context.' : 'Not used yet.',
    };
  });

  const usedCount = wordFeedback.filter((w) => w.used).length;
  const accuracy = targetWords.length
    ? Math.round((usedCount / targetWords.length) * 100)
    : 0;

  // Reward tight writing: ~10-16 words per target word is the sweet spot.
  const ideal = usedCount * 13 || 30;
  const ratio = wordCount / ideal;
  const conciseness = Math.max(
    35,
    Math.round(100 - Math.abs(1 - ratio) * 55),
  );

  // Crude creativity proxy: punctuation variety + length without padding.
  const variety = new Set(lower.replace(/[^a-z]/g, '')).size;
  const creativity = Math.min(
    95,
    Math.max(40, 45 + variety * 2 + (usedCount >= 3 ? 15 : 0)),
  );

  const overall = Math.round((accuracy + conciseness + creativity) / 3);

  return {
    scores: { accuracy, conciseness, creativity, overall },
    feedback:
      usedCount === targetWords.length
        ? 'Strong work — you wove every target word into a single scene. Tighten a few phrases and this is competition-ready.'
        : `You used ${usedCount} of ${targetWords.length} words. Fold in the rest to lift your accuracy score.`,
    wordFeedback,
  };
}
