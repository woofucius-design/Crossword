import React, { useEffect } from 'react';
import {
  AccessibilityInfo,
  Modal,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import Animated, {
  useAnimatedStyle,
  useReducedMotion,
  useSharedValue,
  withDelay,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Button } from '@/components/Button';
import { colors, maxContentWidth, radius, shadows } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { easing } from '@/theme/animations';
import { buildShareText } from '@/data/share';
import { select } from '@/theme/haptics';

export interface RecapWord {
  word: string;
  definition: string;
  /** Collected for the first time in this solve, rather than already owned. */
  isNew: boolean;
}

interface CompletionSheetProps {
  visible: boolean;
  puzzleNumber: number;
  durationSeconds: number;
  words: RecapWord[];
  streak: number;
  onReview: () => void;
  onDone: () => void;
  onDismiss: () => void;
}

function fmtDuration(total: number): string {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

/**
 * Post-solve summary.
 *
 * Solving is the app's emotional peak and, for a vocabulary game, its only
 * guaranteed teaching moment: a student can fill a SAT word purely from
 * crossings without ever reading its clue. So the celebration is the frame,
 * and the definition recap is the substance — this is the screen that has to
 * leave them knowing what the words mean.
 *
 * Dismissible rather than blocking. Backdrop or hardware back returns to the
 * finished grid, which solvers usually want to look at, and the header keeps
 * a way back in.
 */
export function CompletionSheet({
  visible,
  puzzleNumber,
  durationSeconds,
  words,
  streak,
  onReview,
  onDone,
  onDismiss,
}: CompletionSheetProps) {
  const insets = useSafeAreaInsets();
  const reduceMotion = useReducedMotion();
  const mark = useSharedValue(reduceMotion ? 1 : 0);

  useEffect(() => {
    if (!visible) {
      mark.value = reduceMotion ? 1 : 0;
      return;
    }
    AccessibilityInfo.announceForAccessibility?.(
      `Puzzle solved in ${fmtDuration(durationSeconds)}. ${words.length} vocabulary words to review.`,
    );
    if (reduceMotion) {
      mark.value = 1;
      return;
    }
    // Overshoot and settle: the badge should feel stamped on, not faded in.
    mark.value = withDelay(
      90,
      withSequence(
        withTiming(1.12, { duration: 260, easing: easing.swift }),
        withTiming(1, { duration: 160, easing: easing.swift }),
      ),
    );
  }, [visible, reduceMotion, mark, durationSeconds, words.length]);

  const markStyle = useAnimatedStyle(() => ({
    transform: [{ scale: mark.value }],
    opacity: mark.value === 0 ? 0 : 1,
  }));

  const newCount = words.filter((w) => w.isNew).length;

  const onShare = async () => {
    select();
    try {
      await Share.share({
        message: buildShareText({ puzzleNumber, durationSeconds, words, streak }),
      });
    } catch {
      // Dismissing the share sheet rejects on some platforms; not an error.
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onDismiss}
      supportedOrientations={['portrait']}
    >
      <Pressable
        style={styles.backdrop}
        onPress={onDismiss}
        accessibilityRole="button"
        accessibilityLabel="Close summary"
      />
      <View
        style={[styles.sheet, { paddingBottom: insets.bottom + 14 }]}
        accessibilityViewIsModal
      >
        <View style={styles.handle} />

        <ScrollView
          bounces={false}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 6 }}
        >
          <View style={styles.hero}>
            <Animated.View style={[styles.badge, shadows.gold, markStyle]}>
              <Text style={styles.badgeMark}>◆</Text>
            </Animated.View>
            <Text style={styles.title}>Solved</Text>
            <Text style={styles.subtitle}>Puzzle #{puzzleNumber}</Text>
          </View>

          <View style={styles.statsRow}>
            <Stat value={fmtDuration(durationSeconds)} label="Time" tint={colors.text} />
            <Stat value={String(words.length)} label="SAT words" tint={colors.yellow} />
            <Stat value={`${streak}`} label="Day streak" tint={colors.orange} />
          </View>

          <Pressable
            style={styles.shareRow}
            onPress={onShare}
            accessibilityRole="button"
            accessibilityLabel="Share your result"
          >
            <Text style={styles.shareText}>Share result</Text>
          </Pressable>

          {words.length > 0 && (
            <>
              <View style={styles.recapHeader}>
                <Text style={styles.sectionLabel}>WORDS FROM THIS PUZZLE</Text>
                {newCount > 0 && (
                  <Text style={styles.newSummary}>
                    {newCount} new to your collection
                  </Text>
                )}
              </View>

              {words.map((w) => (
                <View key={w.word} style={styles.wordCard}>
                  <View style={styles.wordRow}>
                    <Text style={styles.word}>{w.word}</Text>
                    {w.isNew && (
                      <View style={styles.newChip}>
                        <Text style={styles.newChipText}>NEW</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.definition}>{w.definition}</Text>
                </View>
              ))}
            </>
          )}
        </ScrollView>

        <View style={styles.actions}>
          {words.length > 0 && (
            <Button label="Review These Words" onPress={onReview} style={{ flex: 1 }} />
          )}
          <Button
            label="Done"
            variant={words.length > 0 ? 'secondary' : 'primary'}
            onPress={onDone}
            style={words.length > 0 ? undefined : { flex: 1 }}
          />
        </View>
      </View>
    </Modal>
  );
}

function Stat({ value, label, tint }: { value: string; label: string; tint: string }) {
  return (
    <View style={styles.stat}>
      <Text style={[styles.statValue, { color: tint }]} maxFontSizeMultiplier={1.4}>
        {value}
      </Text>
      <Text style={styles.statLabel} maxFontSizeMultiplier={1.4}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(4,10,18,0.72)',
  },
  sheet: {
    marginTop: 'auto',
    width: '100%',
    maxWidth: maxContentWidth,
    alignSelf: 'center',
    maxHeight: '92%',
    backgroundColor: colors.card,
    borderTopLeftRadius: radius.modal,
    borderTopRightRadius: radius.modal,
    borderWidth: 1,
    borderColor: 'rgba(255,229,102,0.22)',
    paddingHorizontal: 20,
    paddingTop: 10,
  },
  handle: {
    alignSelf: 'center',
    width: 38,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(255,255,255,0.16)',
    marginBottom: 14,
  },
  hero: {
    alignItems: 'center',
  },
  badge: {
    width: 58,
    height: 58,
    borderRadius: 29,
    backgroundColor: 'rgba(255,229,102,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255,229,102,0.45)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeMark: {
    fontSize: 24,
    color: colors.yellow,
  },
  title: {
    fontFamily: fonts.display,
    fontSize: 30,
    color: colors.text,
    marginTop: 12,
    letterSpacing: 0.5,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    marginTop: 20,
    paddingVertical: 14,
    borderTopWidth: 1,
    borderBottomWidth: 1,
    borderColor: colors.border,
  },
  stat: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontFamily: fonts.display,
    fontSize: 19,
  },
  statLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 9.5,
    color: colors.textMuted,
    letterSpacing: 0.4,
    marginTop: 3,
  },
  shareRow: {
    alignSelf: 'center',
    marginTop: 14,
    paddingVertical: 7,
    paddingHorizontal: 16,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  shareText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 12,
    color: colors.textMuted,
  },
  recapHeader: {
    flexDirection: 'row',
    alignItems: 'baseline',
    justifyContent: 'space-between',
    marginTop: 18,
    marginBottom: 8,
  },
  sectionLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 10,
    color: colors.textMuted,
    letterSpacing: 0.6,
  },
  newSummary: {
    fontFamily: fonts.bodyBold,
    fontSize: 10,
    color: colors.mint,
  },
  wordCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 13,
    marginBottom: 8,
  },
  wordRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  word: {
    fontFamily: fonts.display,
    fontSize: 17,
    color: colors.yellow,
    letterSpacing: 0.4,
  },
  newChip: {
    backgroundColor: 'rgba(52,211,153,0.14)',
    borderRadius: radius.pill,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  newChipText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 8,
    color: colors.mint,
    letterSpacing: 0.5,
  },
  definition: {
    fontFamily: fonts.serifItalic,
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 5,
    lineHeight: 19,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
});
