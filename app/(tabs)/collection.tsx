import React, { useMemo, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ScreenBackground } from '@/components/ScreenBackground';
import { WordCard } from '@/components/WordCard';
import { WordDetailSheet } from '@/components/WordDetailSheet';
import { RetentionArc } from '@/components/RetentionArc';
import { colors, radius, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { useApp } from '@/stores/AppStore';
import { daysSince, focusReason, isDue, urgencyScore } from '@/data/retention';
import type { CollectedWord } from '@/types/models';

type Tab = 'all' | 'review' | 'mastered';

export default function CollectionScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { collectedWords } = useApp();
  const [tab, setTab] = useState<Tab>('all');
  const [detail, setDetail] = useState<CollectedWord | null>(null);

  const mastered = collectedWords.filter((w) => w.mastery === 'mastered');
  const due = collectedWords.filter(isDue);

  const justCollected = useMemo(
    () =>
      [...collectedWords]
        .sort((a, b) => +new Date(b.collectedAt) - +new Date(a.collectedAt))
        .slice(0, 5),
    [collectedWords],
  );

  const focusQueue = useMemo(
    () =>
      [...collectedWords]
        .filter((w) => w.mastery !== 'mastered')
        .sort((a, b) => urgencyScore(b) - urgencyScore(a))
        .slice(0, 6),
    [collectedWords],
  );

  const filtered = useMemo(() => {
    const base =
      tab === 'mastered' ? mastered : tab === 'review' ? due : collectedWords;
    return [...base].sort((a, b) => urgencyScore(b) - urgencyScore(a));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, collectedWords]);

  const rows: CollectedWord[][] = [];
  for (let i = 0; i < filtered.length; i += 2) {
    rows.push(filtered.slice(i, i + 2));
  }

  return (
    <ScreenBackground floatingWords={false}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 8,
          paddingHorizontal: spacing.screen,
          paddingBottom: 28,
        }}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <Text style={styles.title}>My Collection</Text>
          <Pressable
            hitSlop={10}
            onPress={() => router.push('/(tabs)/profile')}
            accessibilityRole="button"
            accessibilityLabel="Settings"
          >
            <Text style={styles.gear}>⚙</Text>
          </Pressable>
        </View>

        {/* Stats strip */}
        <View style={styles.statsStrip}>
          <View style={styles.heroTile}>
            <Text style={styles.heroNumber}>{collectedWords.length}</Text>
            <Text style={styles.heroLabel}>Words Collected</Text>
          </View>
          <View style={styles.stackedColumn}>
            <View style={styles.smallTile}>
              <Text style={[styles.smallValue, { color: colors.masteryMastered }]}>
                {mastered.length}
              </Text>
              <Text style={styles.smallLabel}>Mastered</Text>
            </View>
            <View style={styles.smallTile}>
              <Text style={[styles.smallValue, { color: colors.red }]}>
                {due.length}
              </Text>
              <Text style={styles.smallLabel}>Due Today</Text>
            </View>
          </View>
        </View>

        {/* Class rank banner */}
        <View style={styles.rankBanner}>
          <Text style={styles.rankTrophy}>🏆</Text>
          <View style={{ flex: 1 }}>
            <Text style={styles.rankTitle}>#3 in English Honors — Period 2</Text>
            <Text style={styles.rankSub}>Collect 3 more words to reach #2</Text>
          </View>
          <Text style={styles.rankArrow}>View →</Text>
        </View>

        {/* Just collected */}
        <Text style={styles.sectionLabel}>● JUST COLLECTED</Text>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 8, paddingBottom: 4 }}
        >
          {justCollected.map((w) => (
            <Pressable
              key={w.id}
              style={styles.justCard}
              onPress={() => setDetail(w)}
            >
              <View style={styles.justNewBadge}>
                <Text style={styles.justNewText}>NEW</Text>
              </View>
              <Text style={styles.justWord}>{w.word}</Text>
              <Text style={styles.justDef} numberOfLines={3}>
                {w.definition}
              </Text>
            </Pressable>
          ))}
        </ScrollView>

        {/* AI Focus Queue */}
        <View style={styles.focusHeader}>
          <Text style={styles.sectionLabel}>🤖 AI FOCUS QUEUE</Text>
          <Text style={styles.focusCount}>{focusQueue.length} prioritized ↘</Text>
        </View>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ gap: 8, paddingBottom: 4 }}
        >
          {focusQueue.map((w) => {
            const reason = focusReason(w);
            return (
              <Pressable
                key={w.id}
                style={styles.focusCard}
                onPress={() => router.push('/(tabs)/review')}
              >
                <View
                  style={[styles.reasonBadge, { backgroundColor: reason.color + '22' }]}
                >
                  <Text style={[styles.reasonText, { color: reason.color }]}>
                    {reason.label}
                  </Text>
                </View>
                <View style={styles.focusBody}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.focusWord}>{w.word}</Text>
                    <Text style={styles.focusDef} numberOfLines={2}>
                      {w.definition}
                    </Text>
                  </View>
                  <RetentionArc value={w.retention} size={42} stroke={4} />
                </View>
                <View style={styles.reviewBtn}>
                  <Text style={styles.reviewBtnText}>Review</Text>
                </View>
              </Pressable>
            );
          })}
        </ScrollView>

        {/* Tabs */}
        <View style={styles.tabBar}>
          <TabButton label="All" count={collectedWords.length} active={tab === 'all'} onPress={() => setTab('all')} />
          <TabButton label="Review" count={due.length} active={tab === 'review'} onPress={() => setTab('review')} />
          <TabButton label="Mastered" count={mastered.length} active={tab === 'mastered'} onPress={() => setTab('mastered')} />
        </View>

        {/* Word grid */}
        {filtered.length === 0 ? (
          <Text style={styles.empty}>No words here yet — solve a puzzle to collect some.</Text>
        ) : (
          rows.map((row, i) => (
            <View key={i} style={styles.gridRow}>
              {row.map((w) => (
                <WordCard key={w.id} word={w} onPress={setDetail} />
              ))}
              {row.length === 1 && <View style={{ flex: 1 }} />}
            </View>
          ))
        )}
      </ScrollView>

      <WordDetailSheet
        word={detail}
        onClose={() => setDetail(null)}
        onPractice={() => {
          setDetail(null);
          router.push('/(tabs)/review');
        }}
      />
    </ScreenBackground>
  );
}

function TabButton({
  label,
  count,
  active,
  onPress,
}: {
  label: string;
  count: number;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.tabButton, active && styles.tabButtonActive]}
    >
      <Text style={[styles.tabLabel, active && { color: colors.text }]}>{label}</Text>
      <View style={[styles.tabCount, active && { backgroundColor: colors.yellow }]}>
        <Text style={[styles.tabCountText, active && { color: '#3A2A00' }]}>
          {count}
        </Text>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  title: {
    fontFamily: fonts.display,
    fontSize: 22,
    color: colors.text,
  },
  gear: { fontSize: 20, color: colors.textMuted },
  statsStrip: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: spacing.sectionGap,
  },
  heroTile: {
    flex: 1.3,
    backgroundColor: 'rgba(255,229,102,0.08)',
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: 'rgba(255,229,102,0.22)',
    padding: 16,
    justifyContent: 'center',
  },
  heroNumber: {
    fontFamily: fonts.display,
    fontSize: 40,
    color: colors.yellow,
  },
  heroLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  stackedColumn: {
    flex: 1,
    gap: 8,
  },
  smallTile: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 11,
    justifyContent: 'center',
  },
  smallValue: {
    fontFamily: fonts.display,
    fontSize: 20,
  },
  smallLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 9,
    color: colors.textMuted,
    marginTop: 1,
  },
  rankBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: 'rgba(99,102,241,0.14)',
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.3)',
    borderRadius: radius.card,
    padding: 12,
    marginBottom: spacing.sectionGap,
  },
  rankTrophy: { fontSize: 20 },
  rankTitle: {
    fontFamily: fonts.bodyExtra,
    fontSize: 12.5,
    color: colors.text,
  },
  rankSub: {
    fontFamily: fonts.body,
    fontSize: 10.5,
    color: colors.textMuted,
    marginTop: 2,
  },
  rankArrow: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
    color: '#A5B4FC',
  },
  sectionLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    color: colors.textMuted,
    letterSpacing: 0.9,
    marginTop: 14,
    marginBottom: 8,
  },
  justCard: {
    width: 130,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: 'rgba(255,229,102,0.3)',
    padding: 11,
  },
  justNewBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.yellow,
    borderRadius: 4,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
  justNewText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 7.5,
    color: '#3A2A00',
    letterSpacing: 0.5,
  },
  justWord: {
    fontFamily: fonts.display,
    fontSize: 15,
    color: colors.text,
    marginTop: 7,
  },
  justDef: {
    fontFamily: fonts.serif,
    fontSize: 10,
    color: colors.textMuted,
    marginTop: 3,
    lineHeight: 14,
  },
  focusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  focusCount: {
    fontFamily: fonts.bodyExtra,
    fontSize: 10,
    color: colors.red,
  },
  focusCard: {
    width: 210,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 12,
  },
  reasonBadge: {
    alignSelf: 'flex-start',
    borderRadius: 5,
    paddingHorizontal: 7,
    paddingVertical: 3,
  },
  reasonText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 8.5,
    letterSpacing: 0.3,
  },
  focusBody: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 8,
  },
  focusWord: {
    fontFamily: fonts.display,
    fontSize: 16,
    color: colors.text,
  },
  focusDef: {
    fontFamily: fonts.serif,
    fontSize: 10.5,
    color: colors.textMuted,
    marginTop: 2,
    lineHeight: 14,
  },
  reviewBtn: {
    backgroundColor: colors.card,
    borderRadius: radius.pill,
    paddingVertical: 8,
    alignItems: 'center',
    marginTop: 9,
    borderWidth: 1,
    borderColor: colors.border,
  },
  reviewBtnText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
    color: colors.yellow,
  },
  tabBar: {
    flexDirection: 'row',
    gap: 6,
    marginTop: 16,
    marginBottom: 12,
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 9,
    paddingHorizontal: 13,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabButtonActive: {
    backgroundColor: 'rgba(255,229,102,0.12)',
    borderColor: 'rgba(255,229,102,0.4)',
  },
  tabLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 12,
    color: colors.textMuted,
  },
  tabCount: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 7,
    minWidth: 18,
    paddingHorizontal: 5,
    paddingVertical: 1,
    alignItems: 'center',
  },
  tabCountText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    color: colors.textMuted,
  },
  gridRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  empty: {
    fontFamily: fonts.body,
    fontSize: 12.5,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 24,
  },
});
