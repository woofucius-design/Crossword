import React, { useMemo } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ScreenBackground } from '@/components/ScreenBackground';
import { colors, radius, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { daysAgoISO } from '@/data/dates';
import { currentPuzzleDate, getPuzzle, hasPuzzleFor } from '@/data/puzzles';
import { useApp } from '@/stores/AppStore';

interface ArchiveItem {
  date: string;
  number: number;
  label: string;
  solved: boolean;
  satWords: number;
  size: number;
}

export default function PuzzlesScreen() {
  const router = useRouter();
  const { completions } = useApp();
  const insets = useSafeAreaInsets();

  const archive = useMemo<ArchiveItem[]>(() => {
    const done = new Set(completions.map((c) => c.puzzleDate));
    // Anchored on the newest published puzzle rather than the wall clock, so
    // the list never shows days the corpus has no puzzle for.
    const newest = currentPuzzleDate();
    const rows: ArchiveItem[] = [];
    for (let i = 0; rows.length < 14; i++) {
      const iso = daysAgoISO(i, new Date(`${newest}T12:00:00`));
      if (!hasPuzzleFor(iso)) break;
      const puzzle = getPuzzle(iso);
      rows.push({
        date: iso,
        number: puzzle.number,
        label: new Date(`${iso}T12:00:00`).toLocaleDateString('en-US', {
          weekday: 'short',
          month: 'short',
          day: 'numeric',
        }),
        solved: done.has(iso),
        satWords: puzzle.words.filter((w) => w.isSATVocab).length,
        size: puzzle.size.cols,
      });
    }
    return rows;
  }, [completions]);

  return (
    <ScreenBackground floatingWords={false}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 8,
          paddingHorizontal: spacing.screen,
          paddingBottom: 28,
        }}
        showsVerticalScrollIndicator={false}
      >
        <Text style={styles.title}>Puzzle Archive</Text>
        <Text style={styles.subtitle}>Replay any past Daily Mini</Text>

        {archive.map((item, i) => {
          const today = i === 0;
          return (
            <Pressable
              key={item.date}
              style={({ pressed }) => [styles.card, pressed && { opacity: 0.85 }]}
              onPress={() => router.push(`/puzzle/${item.date}`)}
            >
              <View
                style={[
                  styles.numberBox,
                  { backgroundColor: today ? colors.yellow : colors.card },
                ]}
              >
                <Text
                  style={[
                    styles.numberText,
                    { color: today ? '#3A2A00' : colors.textMuted },
                  ]}
                >
                  #{item.number}
                </Text>
              </View>
              <View style={{ flex: 1 }}>
                <View style={styles.cardTitleRow}>
                  <Text style={styles.cardTitle}>Daily Mini</Text>
                  {today && (
                    <View style={styles.todayBadge}>
                      <Text style={styles.todayText}>TODAY</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.cardMeta}>
                  {item.label} · {item.satWords} SAT words · {item.size}×{item.size}
                </Text>
              </View>
              <Text
                style={[
                  styles.status,
                  { color: item.solved ? colors.mint : colors.textDim },
                ]}
              >
                {item.solved ? '✓ Solved' : 'Play →'}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>
    </ScreenBackground>
  );
}

const styles = StyleSheet.create({
  title: {
    fontFamily: fonts.display,
    fontSize: 22,
    color: colors.text,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
    marginBottom: 16,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 12,
    marginBottom: 8,
  },
  numberBox: {
    width: 46,
    height: 46,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  numberText: {
    fontFamily: fonts.display,
    fontSize: 13,
  },
  cardTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  cardTitle: {
    fontFamily: fonts.bodyExtra,
    fontSize: 13.5,
    color: colors.text,
  },
  todayBadge: {
    backgroundColor: 'rgba(52,211,153,0.16)',
    borderRadius: 4,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
  todayText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 7.5,
    color: colors.mint,
    letterSpacing: 0.5,
  },
  cardMeta: {
    fontFamily: fonts.body,
    fontSize: 10.5,
    color: colors.textMuted,
    marginTop: 2,
  },
  status: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11.5,
  },
});
