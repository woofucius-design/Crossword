import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import Animated, {
  useAnimatedProps,
  useAnimatedReaction,
  useSharedValue,
  withDelay,
  withTiming,
  runOnJS,
} from 'react-native-reanimated';
import { colors } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { durations, easing } from '@/theme/animations';

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

interface ScoreRingProps {
  value: number; // 0-100
  label: string;
  color: string;
  size?: number;
  delay?: number;
}

/** SVG ring that fills and counts up from 0 — used on the grading results. */
export function ScoreRing({
  value,
  label,
  color,
  size = 86,
  delay = 0,
}: ScoreRingProps) {
  const stroke = 7;
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;
  const progress = useSharedValue(0);
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    progress.value = withDelay(
      delay,
      withTiming(value, { duration: durations.ringFill, easing: easing.outCubic }),
    );
  }, [value, delay, progress]);

  // Round inside the prepare step so the JS thread is only woken when the
  // displayed integer actually changes. Reacting to the raw value fired
  // runOnJS every frame, and write.tsx renders three of these at once.
  useAnimatedReaction(
    () => Math.round(progress.value),
    (current, previous) => {
      if (current !== previous) runOnJS(setDisplay)(current);
    },
  );

  const animatedProps = useAnimatedProps(() => ({
    strokeDashoffset: circumference * (1 - progress.value / 100),
  }));

  return (
    <View style={{ alignItems: 'center' }}>
      <View style={{ width: size, height: size }}>
        <Svg width={size} height={size}>
          <Circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={stroke}
            fill="none"
          />
          <AnimatedCircle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke={color}
            strokeWidth={stroke}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            animatedProps={animatedProps}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        </Svg>
        <View style={styles.center}>
          <Text style={[styles.value, { color }]}>{display}</Text>
        </View>
      </View>
      <Text style={styles.label}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  center: {
    ...StyleSheet.absoluteFillObject,
    alignItems: 'center',
    justifyContent: 'center',
  },
  value: {
    fontFamily: fonts.display,
    fontSize: 24,
  },
  label: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    color: colors.textMuted,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginTop: 7,
  },
});
