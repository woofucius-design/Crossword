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
import { demoCollectedWords, demoUser } from '@/data/demoData';
import { nextTier } from '@/data/retention';

const STORAGE_KEY = 'lexicon.appstate.v1';

interface PersistedState {
  profile: UserProfile | null;
  collectedWords: CollectedWord[];
  submissions: PassageSubmission[];
  onboarded: boolean;
}

interface AppStore extends PersistedState {
  hydrated: boolean;
  completeOnboarding: (profile: UserProfile, starterWords: CollectedWord[]) => void;
  collectWord: (word: PuzzleWord, puzzleDate: string) => CollectedWord | null;
  reviewWord: (wordId: number, gotIt: boolean) => void;
  addSubmission: (submission: PassageSubmission) => void;
  resetToDemo: () => void;
}

const AppContext = createContext<AppStore | null>(null);

function defaultState(): PersistedState {
  return {
    profile: demoUser,
    collectedWords: demoCollectedWords,
    submissions: [],
    onboarded: true,
  };
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<PersistedState>(defaultState);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem(STORAGE_KEY);
        if (raw) setState(JSON.parse(raw) as PersistedState);
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

  const resetToDemo = useCallback(() => setState(defaultState()), []);

  const value = useMemo<AppStore>(
    () => ({
      ...state,
      hydrated,
      completeOnboarding,
      collectWord,
      reviewWord,
      addSubmission,
      resetToDemo,
    }),
    [state, hydrated, completeOnboarding, collectWord, reviewWord, addSubmission, resetToDemo],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppStore {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used within AppProvider');
  return ctx;
}
