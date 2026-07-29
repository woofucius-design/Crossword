import React, { useEffect } from 'react';
import { StyleSheet, useWindowDimensions } from 'react-native';
import Animated, {
  Easing,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withTiming,
} from 'react-native-reanimated';
import { fonts } from '@/theme/typography';
import { colors } from '@/theme/tokens';

const WORDS = [
  'LUCID', 'CANDOR', 'OPULENT', 'STOIC', 'VERBOSE', 'TERSE', 'ASTUTE',
  'PRUDENT', 'ZEALOUS', 'PLACID', 'AUSTERE', 'FRUGAL', 'DILIGENT',
  'ELOQUENT', 'OBSTINATE', 'BENEVOLENT', 'EPHEMERAL', 'GREGARIOUS',
  'MERCURIAL', 'CACOPHONY', 'NUANCE', 'TENACIOUS', 'AMBIGUOUS',
  'PARADOX', 'CYNICAL', 'EMPATHY', 'RESILIENT', 'WHIMSICAL',
];

type DriftSpec = {
  word: string;
  left: number;
  top: number;
  delay: number;
  duration: number;
  size: number;
};

interface DriftWordProps {
  word: string;
  left: number;
  top: number;
  delay: number;
  duration: number;
  size: number;
}

function DriftWord({ word, left, top, delay, duration, size }: DriftWordProps) {
  const progress = useSharedValue(0);

  useEffect(() => {
    progress.value = withDelay(
      delay,
      withRepeat(
        withTiming(1, { duration, easing: Easing.inOut(Easing.ease) }),
        -1,
        true,
      ),
    );
  }, [progress, delay, duration]);

  const style = useAnimatedStyle(() => ({
    transform: [{ translateY: -progress.value * 32 }],
    opacity: 0.04 + progress.value * 0.05,
  }));

  return (
    <Animated.Text
      style={[
        styles.word,
        { left, top, fontSize: size },
        style,
      ]}
    >
      {word}
    </Animated.Text>
  );
}

interface FloatingWordsProps {
  opacity?: number;
  count?: number;
}

/** Low-opacity SAT vocabulary drifting upward — shared by Home + Onboarding. */
export function FloatingWords({ opacity = 1, count = 24 }: FloatingWordsProps) {
  const { width, height } = useWindowDimensions();

  // Seeded once and kept in a ref rather than recomputed from the live
  // window size. Android shrinks the window when the soft keyboard opens
  // (softwareKeyboardLayoutMode: resize), which previously re-randomised
  // every position and restarted all the drift animations the moment a
  // student tapped the name field during onboarding.
  const seeded = React.useRef<{ w: number; h: number; items: DriftSpec[] } | null>(null);
  if (
    !seeded.current ||
    seeded.current.items.length !== count ||
    // Only a real layout change (rotation, tablet split view) reseeds; a
    // keyboard-driven height change alone must not.
    seeded.current.w !== width
  ) {
    const h = Math.max(seeded.current?.h ?? 0, height);
    seeded.current = {
      w: width,
      h,
      items: Array.from({ length: count }, (_, i) => ({
        word: WORDS[i % WORDS.length],
        left: Math.random() * (width - 90),
        top: Math.random() * (h - 60),
        delay: Math.random() * 6000,
        duration: 9000 + Math.random() * 6000,
        size: 11 + Math.random() * 9,
      })),
    };
  }
  const items = seeded.current.items;

  return (
    <Animated.View style={[StyleSheet.absoluteFill, { opacity }]} pointerEvents="none">
      {items.map((it, i) => (
        <DriftWord key={i} {...it} />
      ))}
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  word: {
    position: 'absolute',
    fontFamily: fonts.display,
    color: colors.text,
    letterSpacing: 1,
  },
});
