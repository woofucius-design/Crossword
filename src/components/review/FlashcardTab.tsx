import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from 'react-native-reanimated';
import { Button } from '@/components/Button';
import { colors, radius } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { durations, easing } from '@/theme/animations';
import { NEEDS_BACKFACE_GUARD } from '@/theme/platform';
import type { CollectedWord } from '@/types/models';

interface FlashcardTabProps {
  words: CollectedWord[];
  onReview: (wordId: number, gotIt: boolean) => void;
}

export function FlashcardTab({ words, onReview }: FlashcardTabProps) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const [gotCount, setGotCount] = useState(0);
  const [done, setDone] = useState(false);
  const rotation = useSharedValue(0);

  const card = words[index];

  // backfaceVisibility alone is unreliable on Android — the hidden face
  // often shows through or renders mirrored mid-flip — so there each face
  // is also switched off by opacity as the card passes 90 degrees. iOS
  // hands the faces over smoothly on its own, and forcing the same binary
  // cut there turns the flip into a snap.
  const frontStyle = useAnimatedStyle(() => ({
    transform: [{ perspective: 1000 }, { rotateY: `${rotation.value}deg` }],
    opacity: NEEDS_BACKFACE_GUARD ? (rotation.value < 90 ? 1 : 0) : 1,
  }));
  const backStyle = useAnimatedStyle(() => ({
    transform: [{ perspective: 1000 }, { rotateY: `${rotation.value + 180}deg` }],
    opacity: NEEDS_BACKFACE_GUARD ? (rotation.value < 90 ? 0 : 1) : 1,
  }));

  const flip = () => {
    const next = flipped ? 0 : 180;
    rotation.value = withTiming(next, {
      duration: durations.cardFlip,
      easing: easing.flip,
    });
    setFlipped(!flipped);
  };

  const answer = (gotIt: boolean) => {
    if (card) onReview(card.wordId, gotIt);
    if (gotIt) setGotCount((c) => c + 1);
    if (index + 1 >= words.length) {
      setDone(true);
    } else {
      rotation.value = 0;
      setFlipped(false);
      setIndex((i) => i + 1);
    }
  };

  const restart = () => {
    setIndex(0);
    setFlipped(false);
    setGotCount(0);
    setDone(false);
    rotation.value = 0;
  };

  if (words.length === 0) {
    return <Text style={styles.empty}>Collect some words to start reviewing.</Text>;
  }

  if (done) {
    const pct = Math.round((gotCount / words.length) * 100);
    return (
      <View style={styles.results}>
        <Text style={styles.resultEmoji}>{pct >= 70 ? '🎉' : '💪'}</Text>
        <Text style={styles.resultPct}>{pct}%</Text>
        <Text style={styles.resultLabel}>
          {gotCount} of {words.length} words confident
        </Text>
        <Button label="Review Again" onPress={restart} style={{ marginTop: 18 }} />
      </View>
    );
  }

  return (
    <View>
      {/* Progress segments */}
      <View style={styles.progressRow}>
        {words.map((_, i) => (
          <View
            key={i}
            style={[
              styles.segment,
              {
                backgroundColor:
                  i < index ? colors.mint : i === index ? colors.yellow : 'rgba(255,255,255,0.1)',
              },
            ]}
          />
        ))}
      </View>
      <Text style={styles.counter}>
        Card {index + 1} of {words.length}
      </Text>

      {/* Flip card */}
      <Pressable onPress={flip} style={styles.cardWrap}>
        <Animated.View style={[styles.card, styles.cardFront, frontStyle]}>
          <Text style={styles.frontWord}>{card.word}</Text>
          <Text style={styles.tapHint}>Tap to flip</Text>
        </Animated.View>
        <Animated.View style={[styles.card, styles.cardBack, backStyle]}>
          <Text style={styles.backDef}>{card.definition}</Text>
        </Animated.View>
      </Pressable>

      {flipped && (
        <View style={styles.answerRow}>
          <Button
            label="😕 Still Learning"
            variant="secondary"
            onPress={() => answer(false)}
            style={{ flex: 1 }}
          />
          <Button label="✓ Got it!" onPress={() => answer(true)} style={{ flex: 1 }} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  empty: {
    fontFamily: fonts.body,
    fontSize: 12.5,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 30,
  },
  progressRow: {
    flexDirection: 'row',
    gap: 4,
  },
  segment: {
    flex: 1,
    height: 4,
    borderRadius: 2,
  },
  counter: {
    fontFamily: fonts.bodyBold,
    fontSize: 10.5,
    color: colors.textMuted,
    marginTop: 8,
    textAlign: 'center',
  },
  cardWrap: {
    height: 240,
    marginTop: 16,
  },
  card: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    borderRadius: radius.cardLarge,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backfaceVisibility: 'hidden',
  },
  cardFront: {
    backgroundColor: colors.card,
    borderColor: 'rgba(255,229,102,0.25)',
  },
  cardBack: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
  },
  frontWord: {
    fontFamily: fonts.display,
    fontSize: 34,
    color: colors.yellow,
    letterSpacing: 0.5,
  },
  tapHint: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textDim,
    marginTop: 14,
  },
  backDef: {
    fontFamily: fonts.serifItalic,
    fontSize: 18,
    color: colors.text,
    textAlign: 'center',
    lineHeight: 27,
  },
  answerRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 16,
  },
  results: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  resultEmoji: { fontSize: 48 },
  resultPct: {
    fontFamily: fonts.display,
    fontSize: 44,
    color: colors.mint,
    marginTop: 8,
  },
  resultLabel: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 4,
  },
});
