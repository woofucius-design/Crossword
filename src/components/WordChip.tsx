import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { colors, radius } from '@/theme/tokens';
import { fonts } from '@/theme/typography';

interface WordChipProps {
  word: string;
  accent?: string;
  done?: boolean;
  dim?: boolean;
}

export function WordChip({ word, accent = colors.yellow, done = false, dim = false }: WordChipProps) {
  return (
    <View
      style={[
        styles.chip,
        {
          borderColor: done ? colors.mint : accent + '55',
          backgroundColor: done ? colors.mint + '22' : accent + '14',
          opacity: dim ? 0.4 : 1,
        },
      ]}
    >
      {done && <Text style={[styles.check, { color: colors.mint }]}>✓ </Text>}
      <Text
        style={[
          styles.text,
          { color: done ? colors.mint : accent },
        ]}
      >
        {word}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: radius.pill,
    borderWidth: 1,
  },
  text: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
    letterSpacing: 0.6,
  },
  check: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
  },
});
