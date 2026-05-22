import React, { useEffect } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import Animated, {
  interpolateColor,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withSequence,
  withTiming,
} from 'react-native-reanimated';
import { colors, radius } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { durations, easing } from '@/theme/animations';

export interface CellProps {
  row: number;
  col: number;
  size: number;
  letter: string;
  isBlack: boolean;
  isSelected: boolean;
  isWordHighlight: boolean;
  number?: number;
  /** Bumped each keystroke into this cell to retrigger the letter-pop. */
  popKey: number;
  /** Ripple flash when the word completes. */
  rippleKey: number;
  rippleDelay: number;
  rippleVocab: boolean;
  onPress: (row: number, col: number) => void;
}

function CellBase({
  row,
  col,
  size,
  letter,
  isBlack,
  isSelected,
  isWordHighlight,
  number,
  popKey,
  rippleKey,
  rippleDelay,
  rippleVocab,
  onPress,
}: CellProps) {
  const pop = useSharedValue(1);
  const ripple = useSharedValue(0);

  useEffect(() => {
    if (popKey > 0) {
      pop.value = withSequence(
        withTiming(0.4, { duration: 0 }),
        withTiming(1.18, { duration: durations.letterPop * 0.55, easing: easing.swift }),
        withTiming(0.96, { duration: durations.letterPop * 0.25, easing: easing.swift }),
        withTiming(1, { duration: durations.letterPop * 0.2, easing: easing.swift }),
      );
    }
  }, [popKey, pop]);

  useEffect(() => {
    if (rippleKey > 0) {
      ripple.value = withDelay(
        rippleDelay,
        withSequence(
          withTiming(1, { duration: durations.wordRippleFlash * 0.4 }),
          withTiming(0, { duration: durations.wordRippleFlash * 0.6 }),
        ),
      );
    }
  }, [rippleKey, rippleDelay, ripple]);

  const letterStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pop.value }],
  }));

  const baseBg = isSelected
    ? colors.cellSelected
    : isWordHighlight
    ? colors.cellWordHighlight
    : colors.cellBg;

  const rippleStyle = useAnimatedStyle(() => ({
    backgroundColor: interpolateColor(
      ripple.value,
      [0, 1],
      [baseBg, rippleVocab ? colors.yellow : colors.mint],
    ),
  }));

  if (isBlack) {
    return (
      <View
        style={[
          styles.cell,
          { width: size, height: size, backgroundColor: colors.cellBlack },
        ]}
      />
    );
  }

  const borderColor = isSelected
    ? colors.cellSelectedBorder
    : isWordHighlight
    ? colors.cellWordHighlightBorder
    : colors.cellBorder;

  return (
    <Pressable onPress={() => onPress(row, col)}>
      <Animated.View
        style={[
          styles.cell,
          { width: size, height: size, borderColor },
          rippleStyle,
        ]}
      >
        {number !== undefined && (
          <Text
            style={[
              styles.number,
              { color: isSelected ? '#7A5C00' : colors.cellNumberText },
            ]}
          >
            {number}
          </Text>
        )}
        {letter !== '' && (
          <Animated.Text style={[styles.letter, letterStyle]}>{letter}</Animated.Text>
        )}
      </Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  cell: {
    borderRadius: radius.cell,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  number: {
    position: 'absolute',
    top: 1.5,
    left: 2.5,
    fontFamily: fonts.display,
    fontSize: 7,
    lineHeight: 8,
  },
  letter: {
    fontFamily: fonts.display,
    fontSize: 14,
    color: colors.cellLetterText,
  },
});

export const Cell = React.memo(CellBase);
