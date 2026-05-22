import React from 'react';
import { Modal, Pressable, StyleSheet, Text, View } from 'react-native';
import { Button } from './Button';
import { RetentionArc } from './RetentionArc';
import { colors, masteryColor, radius } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import type { CollectedWord } from '@/types/models';
import { daysSince, focusReason } from '@/data/retention';

interface WordDetailSheetProps {
  word: CollectedWord | null;
  onClose: () => void;
  onPractice: (word: CollectedWord) => void;
}

const TIER_LABEL: Record<CollectedWord['mastery'], string> = {
  new: 'New',
  learning: 'Learning',
  familiar: 'Familiar',
  strong: 'Strong',
  mastered: 'Mastered',
};

export function WordDetailSheet({ word, onClose, onPractice }: WordDetailSheetProps) {
  return (
    <Modal
      visible={word !== null}
      transparent
      animationType="slide"
      onRequestClose={onClose}
    >
      <Pressable style={styles.backdrop} onPress={onClose} />
      {word && (
        <View style={styles.sheet}>
          <View style={styles.handle} />

          <View style={styles.headerRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.word}>{word.word}</Text>
              <View
                style={[
                  styles.tierBadge,
                  { backgroundColor: masteryColor[word.mastery] + '22' },
                ]}
              >
                <Text style={[styles.tierText, { color: masteryColor[word.mastery] }]}>
                  {TIER_LABEL[word.mastery]}
                </Text>
              </View>
            </View>
            <RetentionArc value={word.retention} size={58} stroke={5} />
          </View>

          <Text style={styles.definition}>{word.definition}</Text>

          <View style={styles.insight}>
            <Text style={styles.insightIcon}>🧠</Text>
            <Text style={styles.insightText}>
              {focusReason(word).label}. Reviewed {word.reviewCount}{' '}
              {word.reviewCount === 1 ? 'time' : 'times'} so far.
            </Text>
          </View>

          <View style={styles.statsRow}>
            <Stat label="Collected" value={`${daysSince(word.collectedAt)}d ago`} />
            <Stat label="Reviews" value={String(word.reviewCount)} />
            <Stat
              label="Last seen"
              value={
                word.lastReviewAt ? `${daysSince(word.lastReviewAt)}d ago` : 'Never'
              }
            />
          </View>

          <View style={styles.actions}>
            <Button
              label="Practice Now"
              onPress={() => onPractice(word)}
              style={{ flex: 1 }}
            />
            <Button label="Close" variant="secondary" onPress={onClose} />
          </View>
        </View>
      )}
    </Modal>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
  },
  sheet: {
    backgroundColor: colors.card,
    borderTopLeftRadius: radius.modal,
    borderTopRightRadius: radius.modal,
    padding: 20,
    paddingBottom: 34,
    borderWidth: 1,
    borderColor: colors.border,
  },
  handle: {
    alignSelf: 'center',
    width: 38,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'rgba(255,255,255,0.18)',
    marginBottom: 16,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  word: {
    fontFamily: fonts.display,
    fontSize: 30,
    color: colors.text,
    letterSpacing: 0.5,
  },
  tierBadge: {
    alignSelf: 'flex-start',
    borderRadius: 5,
    paddingHorizontal: 8,
    paddingVertical: 3,
    marginTop: 6,
  },
  tierText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    letterSpacing: 0.5,
  },
  definition: {
    fontFamily: fonts.serif,
    fontSize: 15,
    color: colors.text,
    lineHeight: 22,
    marginTop: 14,
  },
  insight: {
    flexDirection: 'row',
    gap: 8,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    padding: 12,
    marginTop: 14,
  },
  insightIcon: { fontSize: 15 },
  insightText: {
    flex: 1,
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.textMuted,
    lineHeight: 17,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 14,
  },
  stat: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    paddingVertical: 12,
    alignItems: 'center',
  },
  statValue: {
    fontFamily: fonts.display,
    fontSize: 14,
    color: colors.text,
  },
  statLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 8.5,
    color: colors.textMuted,
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    marginTop: 3,
  },
  actions: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 18,
  },
});
