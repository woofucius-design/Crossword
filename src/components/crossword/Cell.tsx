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
import { tightText } from '@/theme/platform';
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
        accessibilityElementsHidden
        importantForAccessibility="no-hide-descendants"
        style={[
          styles.cell,
          { width: size, height: size, backgroundColor: colors.cellBlack },
        ]}
      />
    );
  }

  // VoiceOver reads position first so a solver can navigate the grid, then
  // the clue number that starts here, then the letter (or that it's empty).
  const label = [
    `Row ${row + 1}, column ${col + 1}`,
    number !== undefined ? `clue ${number} starts here` : null,
    letter ? `letter ${letter}` : 'empty',
  ]
    .filter(Boolean)
    .join(', ');

  const borderColor = isSelected
    ? colors.cellSelectedBorder
    : isWordHighlight
    ? colors.cellWordHighlightBorder
    : colors.cellBorder;

  return (
    <Pressable
      onPress={() => onPress(row, col)}
      accessibilityRole="button"
      accessibilityLabel={label}
      accessibilityState={{ selected: isSelected }}
    >
      <Animated.View
        style={[
          styles.cell,
          { width: size, height: size, borderColor },
          rippleStyle,
        ]}
      >
        {number !== undefined && (
          <Text
            maxFontSizeMultiplier={1}
            style={[
              styles.number,
              { color: isSelected ? '#7A5C00' : colors.cellNumberText },
            ]}
          >
            {number}
          </Text>
        )}
        {letter !== '' && (
          <Animated.Text maxFontSizeMultiplier={1} style={[styles.letter, letterStyle]}>
            {letter}
          </Animated.Text>
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
    // Android pads glyphs vertically inside Text; at this size that pad
    // is larger than the line box and pushes the number out of the cell.
    ...tightText,
  },
  letter: {
    fontFamily: fonts.display,
    fontSize: 14,
    color: colors.cellLetterText,
    ...tightText,
  },
});

export const Cell = React.memo(CellBase);
