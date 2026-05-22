import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, masteryColor, radius } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import type { CollectedWord } from '@/types/models';
import { daysSince, isSlipping } from '@/data/retention';

interface WordCardProps {
  word: CollectedWord;
  onPress: (word: CollectedWord) => void;
}

const TIER_LABEL: Record<CollectedWord['mastery'], string> = {
  new: 'NEW',
  learning: 'LEARNING',
  familiar: 'FAMILIAR',
  strong: 'STRONG',
  mastered: 'MASTERED',
};

export function WordCard({ word, onPress }: WordCardProps) {
  const tint = masteryColor[word.mastery];
  const slipping = isSlipping(word);
  const isNew = word.mastery === 'new' && daysSince(word.collectedAt) <= 1;
  const accent = slipping ? colors.red : tint;

  return (
    <Pressable
      onPress={() => onPress(word)}
      style={({ pressed }) => [
        styles.card,
        {
          borderColor: slipping
            ? 'rgba(239,68,68,0.35)'
            : word.mastery === 'mastered'
            ? 'rgba(168,85,247,0.35)'
            : colors.border,
        },
        pressed && { opacity: 0.85 },
      ]}
    >
      <View style={[styles.accent, { backgroundColor: accent }]} />

      <View style={styles.cardTop}>
        <View style={[styles.tierBadge, { backgroundColor: tint + '22' }]}>
          <Text style={[styles.tierText, { color: tint }]}>
            {TIER_LABEL[word.mastery]}
          </Text>
        </View>
        {isNew && (
          <View style={styles.newBadge}>
            <Text style={styles.newText}>NEW</Text>
          </View>
        )}
      </View>

      <Text style={[styles.word, { color: slipping ? colors.redLight : colors.text }]}>
        {word.word}
      </Text>
      <Text style={styles.definition} numberOfLines={2}>
        {word.definition}
      </Text>

      <View style={styles.retentionRow}>
        <View style={styles.retentionTrack}>
          <View
            style={[
              styles.retentionFill,
              {
                width: `${word.retention}%`,
                backgroundColor: accent,
              },
            ]}
          />
        </View>
        <Text style={[styles.retentionPct, { color: accent }]}>
          {word.retention}%
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    padding: 12,
    paddingLeft: 14,
    overflow: 'hidden',
  },
  accent: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 4,
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  tierBadge: {
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  tierText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 7.5,
    letterSpacing: 0.5,
  },
  newBadge: {
    backgroundColor: colors.yellow,
    borderRadius: 4,
    paddingHorizontal: 5,
    paddingVertical: 2,
  },
  newText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 7.5,
    color: '#3A2A00',
    letterSpacing: 0.5,
  },
  word: {
    fontFamily: fonts.display,
    fontSize: 17,
    marginTop: 8,
    letterSpacing: 0.4,
  },
  definition: {
    fontFamily: fonts.serif,
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 3,
    lineHeight: 15,
    minHeight: 30,
  },
  retentionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    marginTop: 9,
  },
  retentionTrack: {
    flex: 1,
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 2,
    overflow: 'hidden',
  },
  retentionFill: {
    height: 4,
    borderRadius: 2,
  },
  retentionPct: {
    fontFamily: fonts.display,
    fontSize: 10,
  },
});
