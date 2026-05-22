import React, { useEffect } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Animated, {
  Easing,
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { colors, radius, shadows } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { durations, easing } from '@/theme/animations';
import type { PuzzleWord } from '@/types/models';

interface CollectionToastProps {
  word: PuzzleWord;
  onDismiss: () => void;
}

const STAR_COUNT = 7;

function Star({ index }: { index: number }) {
  const progress = useSharedValue(0);

  useEffect(() => {
    progress.value = withDelay(
      index * 70,
      withTiming(1, { duration: 1000, easing: Easing.out(Easing.ease) }),
    );
  }, [index, progress]);

  const style = useAnimatedStyle(() => ({
    transform: [
      { translateY: -progress.value * 54 },
      { translateX: (index - STAR_COUNT / 2) * 16 },
      { scale: 1 - progress.value * 0.5 },
    ],
    opacity: 1 - progress.value,
  }));

  return <Animated.Text style={[styles.star, style]}>⭐</Animated.Text>;
}

/** Auto-triggered toast when a SAT vocab word is collected from the grid. */
export function CollectionToast({ word, onDismiss }: CollectionToastProps) {
  const translateY = useSharedValue(140);
  const drain = useSharedValue(1);

  useEffect(() => {
    translateY.value = withSequence(
      withTiming(-4, { duration: durations.toastIn, easing: easing.swift }),
      withTiming(0, { duration: 120, easing: easing.swift }),
    );
    drain.value = withTiming(0, { duration: durations.toastDismiss }, (done) => {
      if (done) runOnJS(onDismiss)();
    });
  }, [translateY, drain, onDismiss]);

  const containerStyle = useAnimatedStyle(() => ({
    transform: [{ translateY: translateY.value }],
  }));
  const drainStyle = useAnimatedStyle(() => ({
    width: `${drain.value * 100}%`,
  }));

  return (
    <Animated.View style={[styles.toast, shadows.toast, containerStyle]}>
      <View style={styles.starField} pointerEvents="none">
        {Array.from({ length: STAR_COUNT }, (_, i) => (
          <Star key={i} index={i} />
        ))}
      </View>

      <Pressable style={styles.close} onPress={onDismiss} hitSlop={10}>
        <Text style={styles.closeText}>×</Text>
      </Pressable>

      <Text style={styles.header}>⭐ Added to Collection!</Text>
      <Text style={styles.word}>{word.answer}</Text>
      <Text style={styles.definition} numberOfLines={3}>
        {word.definition}
      </Text>

      <View style={styles.drainTrack}>
        <Animated.View style={[styles.drainFill, drainStyle]} />
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  toast: {
    position: 'absolute',
    left: 14,
    right: 14,
    bottom: 16,
    backgroundColor: colors.card,
    borderRadius: radius.modal,
    borderWidth: 1,
    borderColor: 'rgba(255,229,102,0.3)',
    padding: 18,
    paddingTop: 22,
  },
  starField: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  star: {
    position: 'absolute',
    fontSize: 16,
  },
  close: {
    position: 'absolute',
    top: 10,
    right: 12,
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    fontSize: 20,
    color: colors.textMuted,
    lineHeight: 22,
  },
  header: {
    fontFamily: fonts.bodyExtra,
    fontSize: 12,
    color: colors.yellow,
    letterSpacing: 0.4,
  },
  word: {
    fontFamily: fonts.display,
    fontSize: 28,
    color: colors.text,
    marginTop: 6,
    letterSpacing: 0.5,
  },
  definition: {
    fontFamily: fonts.serifItalic,
    fontStyle: 'italic',
    fontSize: 13.5,
    color: colors.textMuted,
    marginTop: 4,
    lineHeight: 19,
  },
  drainTrack: {
    height: 3,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 2,
    marginTop: 14,
    overflow: 'hidden',
  },
  drainFill: {
    height: 3,
    backgroundColor: colors.yellow,
  },
});
