import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radius } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import type { PuzzleWord } from '@/types/models';

interface ClueBarProps {
  word: PuzzleWord | null;
  onToggleDirection: () => void;
}

export function ClueBar({ word, onToggleDirection }: ClueBarProps) {
  if (!word) return null;
  const vocab = word.isSATVocab;

  return (
    <View style={styles.bar}>
      <View
        style={[
          styles.badge,
          { backgroundColor: vocab ? colors.yellow : colors.card },
        ]}
      >
        <Text
          style={[
            styles.badgeText,
            { color: vocab ? '#3A2A00' : colors.text },
          ]}
        >
          {word.number}
          {word.direction === 'across' ? 'A' : 'D'}
        </Text>
      </View>

      <View style={styles.clueWrap}>
        <Text style={styles.clue} numberOfLines={2}>
          {word.clue}
        </Text>
        {vocab && <Text style={styles.vocabTag}>SAT VOCABULARY</Text>}
      </View>

      <Pressable
        onPress={onToggleDirection}
        style={({ pressed }) => [styles.toggle, pressed && { opacity: 0.7 }]}
      >
        <Text style={styles.toggleText}>⇄</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 10,
    gap: 10,
  },
  badge: {
    width: 36,
    height: 36,
    borderRadius: 9,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeText: {
    fontFamily: fonts.display,
    fontSize: 13,
  },
  clueWrap: {
    flex: 1,
  },
  clue: {
    fontFamily: fonts.bodyBold,
    fontSize: 13.5,
    color: colors.text,
    lineHeight: 18,
  },
  vocabTag: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9,
    color: 'rgba(255,229,102,0.6)',
    letterSpacing: 0.5,
    marginTop: 2,
  },
  toggle: {
    width: 36,
    height: 36,
    borderRadius: 9,
    backgroundColor: colors.card,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  toggleText: {
    fontSize: 16,
    color: colors.text,
  },
});
