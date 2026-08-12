import React, { useCallback, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ScreenBackground } from '@/components/ScreenBackground';
import { Grid, computeCellSize, type CellRenderState } from '@/components/crossword/Grid';
import { Keyboard } from '@/components/crossword/Keyboard';
import { ClueBar } from '@/components/crossword/ClueBar';
import { CollectionToast } from '@/components/crossword/CollectionToast';
import { CompletionSheet, type RecapWord } from '@/components/crossword/CompletionSheet';
import { colors, maxContentWidth, radius, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { durations } from '@/theme/animations';
import { getPuzzle, isWordComplete, wordAt, wordCells } from '@/data/puzzles';
import { useApp } from '@/stores/AppStore';
import { useAndroidBack } from '@/hooks/useAndroidBack';
import { rippleLight } from '@/theme/platform';
import { puzzleSolved, vocabCollected, wordSolved } from '@/theme/haptics';
import type { PuzzleWord } from '@/types/models';

type Direction = 'across' | 'down';

/** Cells stop growing past a comfortable thumb target. */
const MAX_CELL = 44;

/**
 * How long to hold the finished grid before the summary slides up. Tied to
 * the word-ripple so the last word visibly finishes flashing first — the win
 * should read as earned by the grid, not interrupted by a sheet.
 */
const SUMMARY_DELAY = durations.wordRippleFlash + 400;

function useTimer(running: boolean) {
  const [seconds, setSeconds] = useState(0);
  React.useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [running]);
  return seconds;
}

function fmtTime(total: number): string {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export default function PuzzleScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const { date } = useLocalSearchParams<{ date: string }>();
  const { profile, collectWord, collectedWords, recordCompletion } = useApp();

  const puzzle = useMemo(() => getPuzzle(date ?? ''), [date]);
  const puzzleDate = date ?? puzzle.date;

  const cellSize = Math.min(
    computeCellSize(
      Math.min(width, maxContentWidth) - spacing.screen * 2,
      puzzle.size.cols,
    ),
    MAX_CELL,
  );

  // ── Game state ──────────────────────────────────────────────
  const [letters, setLetters] = useState<Record<string, string>>(() => {
    const init: Record<string, string> = {};
    for (const [key, meta] of Object.entries(puzzle.cells)) {
      if (meta.preFilled) init[key] = meta.preFilled;
    }
    return init;
  });
  const [selected, setSelected] = useState<{ row: number; col: number }>(() => {
    const first = puzzle.words[0];
    return { row: first.row, col: first.col };
  });
  const [direction, setDirection] = useState<Direction>('across');
  const [completed, setCompleted] = useState<Set<string>>(new Set());
  const [collectedIds, setCollectedIds] = useState<Set<string>>(new Set());
  const [toastWord, setToastWord] = useState<PuzzleWord | null>(null);
  const [solved, setSolved] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  /** Answers that this solve actually added to the collection, as opposed to
   *  ones the student already owned — drives the NEW chips in the recap. */
  const [newlyCollected, setNewlyCollected] = useState<Set<string>>(new Set());

  const finishHandled = useRef(false);
  const popKeys = useRef<Record<string, number>>({});
  const [popVersion, setPopVersion] = useState(0);
  const ripples = useRef<Record<string, { key: number; delay: number; vocab: boolean }>>({});
  const [rippleVersion, setRippleVersion] = useState(0);

  // Stops the moment the grid is finished, so the summary reports solve time
  // rather than however long the sheet stayed open.
  const timer = useTimer(!solved);

  const isBlack = (r: number, c: number) => puzzle.solution[r][c] === '#';

  const activeWord = useMemo(
    () => wordAt(puzzle, selected.row, selected.col, direction) ??
      wordAt(puzzle, selected.row, selected.col, direction === 'across' ? 'down' : 'across'),
    [puzzle, selected, direction],
  );

  const highlightSet = useMemo(() => {
    const set = new Set<string>();
    if (activeWord) {
      for (const c of wordCells(activeWord)) set.add(`${c.row},${c.col}`);
    }
    return set;
  }, [activeWord]);

  // ── Cell render states ──────────────────────────────────────
  const cellStates = useMemo(() => {
    const states: Record<string, CellRenderState> = {};
    for (let r = 0; r < puzzle.size.rows; r++) {
      for (let c = 0; c < puzzle.size.cols; c++) {
        const key = `${r},${c}`;
        const ripple = ripples.current[key];
        states[key] = {
          letter: letters[key] ?? '',
          isBlack: isBlack(r, c),
          isSelected: selected.row === r && selected.col === c,
          isWordHighlight: highlightSet.has(key),
          number: puzzle.cells[key]?.number,
          popKey: popKeys.current[key] ?? 0,
          rippleKey: ripple?.key ?? 0,
          rippleDelay: ripple?.delay ?? 0,
          rippleVocab: ripple?.vocab ?? false,
        };
      }
    }
    return states;
    // popVersion / rippleVersion intentionally included to refresh ref-backed values
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [puzzle, letters, selected, highlightSet, popVersion, rippleVersion]);

  // ── Interaction ─────────────────────────────────────────────
  const onCellPress = useCallback(
    (row: number, col: number) => {
      if (isBlack(row, col)) return;
      if (selected.row === row && selected.col === col) {
        setDirection((d) => (d === 'across' ? 'down' : 'across'));
      } else {
        setSelected({ row, col });
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selected],
  );

  const toggleDirection = useCallback(
    () => setDirection((d) => (d === 'across' ? 'down' : 'across')),
    [],
  );

  const checkCompletions = useCallback(
    (nextLetters: Record<string, string>) => {
      const newlyDone: PuzzleWord[] = [];
      for (const w of puzzle.words) {
        if (completed.has(w.id)) continue;
        if (isWordComplete(w, nextLetters)) newlyDone.push(w);
      }
      if (newlyDone.length === 0) return;

      setCompleted((prev) => {
        const next = new Set(prev);
        for (const w of newlyDone) next.add(w.id);
        return next;
      });

      for (const w of newlyDone) {
        const cells = wordCells(w);
        cells.forEach((cell, i) => {
          ripples.current[`${cell.row},${cell.col}`] = {
            key: Date.now() + i,
            delay: i * durations.wordRipplePerCell,
            vocab: w.isSATVocab,
          };
        });
      }
      setRippleVersion((v) => v + 1);

      const finishes = puzzle.words.every((w) => isWordComplete(w, nextLetters));

      const vocabDone = newlyDone.filter(
        (w) => w.isSATVocab && !collectedIds.has(w.id),
      );
      if (vocabDone.length > 0) {
        setCollectedIds((prev) => {
          const next = new Set(prev);
          for (const w of vocabDone) next.add(w.id);
          return next;
        });
        // Check ownership BEFORE collecting: collectWord assigns its return
        // value inside a setState updater, which React defers, so the value
        // it hands back here is still null.
        const fresh = vocabDone.filter(
          (w) => !collectedWords.some((c) => c.word === w.answer),
        );
        for (const w of vocabDone) collectWord(w, puzzleDate);
        if (fresh.length > 0) {
          setNewlyCollected((prev) => {
            const next = new Set(prev);
            for (const w of fresh) next.add(w.answer);
            return next;
          });
        }
      }
      // The toast can only show one; the summary lists them all anyway.
      const vocab = vocabDone[0];

      // Exactly once: checkCompletions runs inside a setLetters updater, and
      // React may invoke an updater more than once for the same change.
      const firstFinish = finishes && !finishHandled.current;

      // One cue per event: stacking these reads as a single muddy buzz. A
      // repeat invocation must stay silent rather than fall through to a
      // different cue.
      if (finishes) {
        if (firstFinish) puzzleSolved();
      } else if (vocab) {
        vocabCollected();
      } else {
        wordSolved();
      }

      if (firstFinish) {
        finishHandled.current = true;
        setSolved(true);
        // The toast is suppressed here even for a vocab word: the summary
        // lists it anyway, and a toast sliding up under a modal is a mess.
        // The delay lets the final word-ripple finish, so the win reads as
        // earned by the grid rather than interrupted by a sheet.
        setTimeout(() => setShowSummary(true), SUMMARY_DELAY);
      } else if (!finishes && vocab) {
        setTimeout(() => setToastWord(vocab), 350);
      }
    },
    [puzzle, completed, collectedIds, collectWord, collectedWords],
  );

  const advance = useCallback(
    (back: boolean) => {
      if (!activeWord) return;
      const cells = wordCells(activeWord);
      const idx = cells.findIndex(
        (c) => c.row === selected.row && c.col === selected.col,
      );
      const nextIdx = back ? idx - 1 : idx + 1;
      if (nextIdx >= 0 && nextIdx < cells.length) {
        setSelected({ row: cells[nextIdx].row, col: cells[nextIdx].col });
      }
    },
    [activeWord, selected],
  );

  const onKey = useCallback(
    (letter: string) => {
      if (solved) return;
      const key = `${selected.row},${selected.col}`;
      if (isBlack(selected.row, selected.col)) return;
      popKeys.current[key] = (popKeys.current[key] ?? 0) + 1;
      setPopVersion((v) => v + 1);
      setLetters((prev) => {
        const next = { ...prev, [key]: letter };
        checkCompletions(next);
        return next;
      });
      advance(false);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selected, advance, checkCompletions, solved],
  );

  const onDelete = useCallback(() => {
    if (solved) return;
    const key = `${selected.row},${selected.col}`;
    // Both halves read one snapshot, so a backspace either erases or moves
    // the cursor and never does both. The delete itself still goes through a
    // functional updater so it can't clobber an uncommitted keystroke.
    const hadLetter = !!letters[key];
    if (hadLetter) {
      setLetters((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    } else {
      advance(true);
    }
  }, [selected, letters, advance, solved]);

  // Clearing a cell un-finishes every word running through it. `completed`
  // only ever grew before, so the progress bar over-reported and a stale
  // entry could survive into the finish check. Reconciling against the
  // committed letters keeps the two in step without a nested setState.
  React.useEffect(() => {
    setCompleted((done) => {
      if (done.size === 0) return done;
      const kept = new Set(
        [...done].filter((id) => {
          const w = puzzle.words.find((x) => x.id === id);
          return w ? isWordComplete(w, letters) : false;
        }),
      );
      return kept.size === done.size ? done : kept;
    });
  }, [letters, puzzle]);

  const progress = completed.size / puzzle.words.length;

  const across = puzzle.words
    .filter((w) => w.direction === 'across')
    .sort((a, b) => a.number - b.number);
  const down = puzzle.words
    .filter((w) => w.direction === 'down')
    .sort((a, b) => a.number - b.number);

  const selectWord = (w: PuzzleWord) => {
    setDirection(w.direction);
    setSelected({ row: w.row, col: w.col });
  };

  // Solving progress lives only in component state, so leaving the screen
  // discards it. Confirm first — on Android an accidental back-swipe would
  // otherwise wipe a half-solved grid with no warning.
  const hasProgress = useMemo(
    () =>
      !solved &&
      Object.entries(letters).some(
        ([key, value]) => value && !puzzle.cells[key]?.preFilled,
      ),
    [letters, puzzle, solved],
  );

  // Recap source: the generator's featured set when present, otherwise every
  // SAT entry in the grid — the bundled sample puzzle has no featured array.
  const recapWords = useMemo<RecapWord[]>(() => {
    const seen = new Set<string>();
    const rows: RecapWord[] = [];
    const push = (word: string, definition: string) => {
      if (!word || seen.has(word)) return;
      seen.add(word);
      rows.push({ word, definition, isNew: newlyCollected.has(word) });
    };
    if (puzzle.featured?.length) {
      for (const f of puzzle.featured) push(f.word, f.definition || f.clue);
    } else {
      for (const w of puzzle.words) {
        if (w.isSATVocab) push(w.answer, w.definition || w.clue);
      }
    }
    return rows;
  }, [puzzle, newlyCollected]);

  // Recorded as soon as the grid is finished rather than when the sheet is
  // dismissed, so a solve survives the app being killed on the summary.
  const recorded = useRef(false);
  React.useEffect(() => {
    if (!solved || recorded.current) return;
    recorded.current = true;
    recordCompletion({
      puzzleDate,
      puzzleNumber: puzzle.number,
      durationSeconds: timer,
      wordsCollected: newlyCollected.size,
      completedAt: new Date().toISOString(),
    });
    // timer/newlyCollected are read once at the moment of solving
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [solved]);

  const goReview = useCallback(() => {
    setShowSummary(false);
    // replace, not push: the finished puzzle shouldn't sit under the review tab.
    router.replace({
      pathname: '/(tabs)/review',
      params: { focus: recapWords.map((w) => w.word).join(',') },
    });
  }, [router, recapWords]);

  const leave = useCallback(() => {
    if (!hasProgress) {
      router.back();
      return;
    }
    Alert.alert(
      'Leave this puzzle?',
      'Your progress on this grid will be lost.',
      [
        { text: 'Keep solving', style: 'cancel' },
        { text: 'Leave', style: 'destructive', onPress: () => router.back() },
      ],
    );
  }, [hasProgress, router]);

  const onAndroidBack = useCallback(() => {
    // The summary is a Modal and handles its own back via onRequestClose.
    if (showSummary) return false;
    // The collection toast is a plain absolute View, not a Modal, so it
    // has to be dismissed here before back may leave the screen.
    if (toastWord) {
      setToastWord(null);
      return true;
    }
    leave();
    return true;
  }, [showSummary, toastWord, leave]);

  useAndroidBack(onAndroidBack);

  return (
    <ScreenBackground floatingWords={false}>
      <View style={{ flex: 1, paddingTop: insets.top + 4 }}>
        {/* Header */}
        <View style={styles.header}>
          <Pressable
            onPress={leave}
            hitSlop={12}
            style={styles.back}
            accessibilityRole="button"
            accessibilityLabel="Back"
          >
            <Text style={styles.backText}>←</Text>
          </Pressable>
          <View style={{ flex: 1 }}>
            <Text style={styles.headerTitle}>Daily Mini #{puzzle.number}</Text>
            <Text style={styles.headerDate}>SAT Vocabulary · {puzzleDate}</Text>
          </View>
          <View style={styles.streakChip}>
            <Text style={styles.streakText}>🔥 {profile?.streak ?? 0}</Text>
          </View>
          {solved ? (
            <Pressable
              style={styles.solvedChip}
              onPress={() => setShowSummary(true)}
              accessibilityRole="button"
              accessibilityLabel="Show puzzle summary"
              hitSlop={8}
            >
              <Text style={styles.solvedText}>✓ {fmtTime(timer)}</Text>
            </Pressable>
          ) : (
            <View style={styles.timerChip}>
              <Text style={styles.timerText}>{fmtTime(timer)}</Text>
            </View>
          )}
        </View>

        {/* Progress bar */}
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${progress * 100}%` }]} />
        </View>

        <View style={styles.clueBarPinned}>
          <ClueBar word={activeWord} onToggleDirection={toggleDirection} />
        </View>

        <ScrollView
          contentContainerStyle={{ paddingHorizontal: spacing.screen, paddingBottom: 12 }}
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.progressLabelRow}>
            <Text style={styles.progressLabel}>
              {completed.size}/{puzzle.words.length} WORDS
            </Text>
            <Text style={[styles.progressLabel, { color: colors.mint }]}>
              {Math.round(progress * 100)}%
            </Text>
          </View>

          <Grid
            rows={puzzle.size.rows}
            cols={puzzle.size.cols}
            cellSize={cellSize}
            states={cellStates}
            onCellPress={onCellPress}
          />

          <View style={{ height: 10 }} />

          {/* Compact clue list */}
          <View style={styles.clueColumns}>
            <ClueColumn
              title="ACROSS"
              words={across}
              activeId={activeWord?.id}
              completed={completed}
              onSelect={selectWord}
            />
            <ClueColumn
              title="DOWN"
              words={down}
              activeId={activeWord?.id}
              completed={completed}
              onSelect={selectWord}
            />
          </View>
        </ScrollView>

        {/* Keyboard */}
        <View style={[styles.keyboardWrap, { paddingBottom: Math.max(insets.bottom, 8) }]}>
          <Keyboard onKey={onKey} onDelete={onDelete} />
        </View>

        {toastWord && (
          <CollectionToast word={toastWord} onDismiss={() => setToastWord(null)} />
        )}

        <CompletionSheet
          visible={showSummary}
          puzzleNumber={puzzle.number}
          durationSeconds={timer}
          words={recapWords}
          streak={profile?.streak ?? 0}
          onReview={goReview}
          onDone={() => {
            setShowSummary(false);
            router.back();
          }}
          onDismiss={() => setShowSummary(false)}
        />
      </View>
    </ScreenBackground>
  );
}

function ClueColumn({
  title,
  words,
  activeId,
  completed,
  onSelect,
}: {
  title: string;
  words: PuzzleWord[];
  activeId?: string;
  completed: Set<string>;
  onSelect: (w: PuzzleWord) => void;
}) {
  return (
    <View style={{ flex: 1 }}>
      <Text style={styles.clueColTitle}>{title}</Text>
      {words.map((w) => {
        const active = w.id === activeId;
        const done = completed.has(w.id);
        return (
          <Pressable
            key={w.id}
            onPress={() => onSelect(w)}
            android_ripple={rippleLight()}
            style={[styles.clueRow, active && styles.clueRowActive]}
          >
            <Text style={[styles.clueNum, w.isSATVocab && { color: colors.yellow }]}>
              {w.number}
            </Text>
            <Text
              style={[
                styles.clueText,
                done && styles.clueTextDone,
                active && { color: colors.text },
              ]}
              numberOfLines={2}
            >
              {w.clue}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: spacing.screen,
    paddingBottom: 8,
  },
  back: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backText: { fontSize: 22, color: colors.text },
  headerTitle: {
    fontFamily: fonts.display,
    fontSize: 15,
    color: colors.text,
  },
  headerDate: {
    fontFamily: fonts.body,
    fontSize: 10,
    color: colors.textMuted,
    marginTop: 1,
  },
  streakChip: {
    backgroundColor: 'rgba(255,107,53,0.16)',
    borderRadius: radius.pill,
    paddingHorizontal: 9,
    paddingVertical: 5,
  },
  streakText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
    color: colors.orange,
  },
  solvedChip: {
    backgroundColor: 'rgba(52,211,153,0.16)',
    borderWidth: 1,
    borderColor: 'rgba(52,211,153,0.4)',
    borderRadius: radius.pill,
    paddingHorizontal: 9,
    paddingVertical: 4,
    marginLeft: 6,
  },
  solvedText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
    color: colors.mint,
  },
  timerChip: {
    backgroundColor: colors.card,
    borderRadius: radius.pill,
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderWidth: 1,
    borderColor: colors.border,
  },
  timerText: {
    fontFamily: fonts.displayMedium,
    fontSize: 11,
    color: colors.text,
  },
  progressTrack: {
    height: 3,
    backgroundColor: 'rgba(255,255,255,0.06)',
    marginHorizontal: spacing.screen,
    borderRadius: 2,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: 3,
    backgroundColor: colors.mint,
  },
  progressLabelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    color: colors.textMuted,
    letterSpacing: 0.8,
  },
  clueColumns: {
    flexDirection: 'row',
    gap: 14,
    marginTop: 14,
  },
  clueColTitle: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    color: colors.yellow,
    letterSpacing: 0.9,
    marginBottom: 6,
  },
  clueRow: {
    flexDirection: 'row',
    gap: 7,
    paddingVertical: 6,
    paddingHorizontal: 6,
    borderRadius: 8,
  },
  clueRowActive: {
    backgroundColor: colors.surface,
  },
  clueNum: {
    fontFamily: fonts.display,
    fontSize: 11,
    color: colors.textMuted,
    width: 16,
  },
  clueText: {
    flex: 1,
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textMuted,
    lineHeight: 15,
  },
  clueTextDone: {
    textDecorationLine: 'line-through',
    color: colors.textDim,
  },
  clueBarPinned: {
    paddingHorizontal: spacing.screen,
    paddingBottom: 8,
  },
  keyboardWrap: {
    paddingTop: 8,
    paddingHorizontal: spacing.screen,
    backgroundColor: 'rgba(13,27,42,0.94)',
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
});
