import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type {
  CollectedWord,
  PassageSubmission,
  PuzzleWord,
  UserProfile,
} from '@/types/models';
import type { PuzzleCompletion } from '@/types/models';
import { demoCollectedWords, demoUser } from '@/data/demoData';
import { nextTier } from '@/data/retention';

const STORAGE_KEY = 'lexicon.appstate.v1';

interface PersistedState {
  profile: UserProfile | null;
  collectedWords: CollectedWord[];
  submissions: PassageSubmission[];
  completions: PuzzleCompletion[];
  onboarded: boolean;
}

interface AppStore extends PersistedState {
  hydrated: boolean;
  completeOnboarding: (profile: UserProfile, starterWords: CollectedWord[]) => void;
  collectWord: (word: PuzzleWord, puzzleDate: string) => CollectedWord | null;
  reviewWord: (wordId: number, gotIt: boolean) => void;
  addSubmission: (submission: PassageSubmission) => void;
  /** Records a solve. Idempotent per puzzle date: re-solving the same
   *  puzzle keeps the original result rather than inflating the streak. */
  recordCompletion: (c: PuzzleCompletion) => void;
  completionFor: (puzzleDate: string) => PuzzleCompletion | undefined;
}

const AppContext = createContext<AppStore | null>(null);

function defaultState(): PersistedState {
  return {
    profile: demoUser,
    collectedWords: demoCollectedWords,
    submissions: [],
    completions: [],
    onboarded: true,
  };
}

/**
 * Day number of an ISO timestamp, read in the device's local zone — a streak
 * is about the user's days, not UTC's.
 *
 * The local Y/M/D is re-projected through Date.UTC rather than dividing a
 * local-midnight epoch: local midnights are not a fixed distance apart across
 * a DST change, so in zones near the zero offset the naive version made
 * consecutive days differ by 0 or 2, silently freezing the streak in spring
 * and resetting it in autumn.
 */
function localDay(iso: string): number {
  const d = new Date(iso);
  return Math.floor(
    Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86_400_000,
  );
}

/**
 * A streak counts consecutive days solved, so it extends only when the last
 * solve was yesterday, holds when another puzzle is solved the same day, and
 * restarts at 1 after any gap. Incrementing per completion would just be a
 * solve count wearing a flame.
 */
function nextStreak(
  completions: PuzzleCompletion[],
  current: number,
  added: PuzzleCompletion,
): number {
  // No history yet (a fresh install, or a profile that predates completion
  // tracking) — hold whatever the profile already claims rather than
  // demoting it. Onboarding starts a user at 1.
  if (completions.length === 0) return Math.max(current, 1);
  const today = localDay(added.completedAt);
  const last = Math.max(...completions.map((c) => localDay(c.completedAt)));
  if (last === today) return Math.max(current, 1);
  if (today - last === 1) return current + 1;
  return 1;
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<PersistedState>(defaultState);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY);
        if (raw) {
          const saved = JSON.parse(raw) as PersistedState;
          // `completions` postdates the first release of this key, so a
          // stored state from before it is missing the field entirely.
          setState({ ...defaultState(), ...saved, completions: saved.completions ?? [] });
        }
      } catch {
        // keep defaults
      } finally {
        setHydrated(true);
      }
    })();
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(state)).catch(() => {});
  }, [state, hydrated]);

  const completeOnboarding = useCallback(
    (profile: UserProfile, starterWords: CollectedWord[]) => {
      setState((s) => ({
        ...s,
        profile,
        collectedWords: starterWords,
        onboarded: true,
      }));
    },
    [],
  );

  const recordCompletion = useCallback((c: PuzzleCompletion) => {
    setState((s) => {
      if (s.completions.some((x) => x.puzzleDate === c.puzzleDate)) return s;
      const profile = s.profile
        ? { ...s.profile, streak: nextStreak(s.completions, s.profile.streak, c) }
        : s.profile;
      return { ...s, profile, completions: [c, ...s.completions] };
    });
  }, []);

  const collectWord = useCallback(
    (word: PuzzleWord, puzzleDate: string): CollectedWord | null => {
      if (!word.isSATVocab) return null;
      let created: CollectedWord | null = null;
      setState((s) => {
        if (s.collectedWords.some((w) => w.word === word.answer)) return s;
        created = {
          id: `cw-${Date.now()}-${word.id}`,
          userId: s.profile?.id ?? 'demo-user',
          wordId: word.number,
          word: word.answer,
          definition: word.definition ?? '',
          mastery: 'new',
          retention: 100,
          reviewCount: 0,
          collectedAt: new Date().toISOString(),
          lastReviewAt: null,
          puzzleDate,
        };
        return { ...s, collectedWords: [created, ...s.collectedWords] };
      });
      return created;
    },
    [],
  );

  const reviewWord = useCallback((wordId: number, gotIt: boolean) => {
    setState((s) => ({
      ...s,
      collectedWords: s.collectedWords.map((w) => {
        if (w.wordId !== wordId) return w;
        const retention = gotIt
          ? Math.min(100, w.retention + 12)
          : Math.max(20, w.retention - 8);
        return {
          ...w,
          retention,
          reviewCount: w.reviewCount + 1,
          lastReviewAt: new Date().toISOString(),
          mastery: gotIt && retention >= 80 ? nextTier(w.mastery) : w.mastery,
        };
      }),
    }));
  }, []);

  const addSubmission = useCallback((submission: PassageSubmission) => {
    setState((s) => ({ ...s, submissions: [submission, ...s.submissions] }));
  }, []);

  const completionFor = useCallback(
    (puzzleDate: string) => state.completions.find((c) => c.puzzleDate === puzzleDate),
    [state.completions],
  );

  const value = useMemo<AppStore>(
    () => ({
      ...state,
      hydrated,
      completeOnboarding,
      collectWord,
      reviewWord,
      addSubmission,
      recordCompletion,
      completionFor,
    }),
    [state, hydrated, completeOnboarding, collectWord, reviewWord, addSubmission,
     recordCompletion, completionFor],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppStore {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
