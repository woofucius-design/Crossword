import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ScreenBackground } from '@/components/ScreenBackground';
import { StoryTab } from '@/components/review/StoryTab';
import { FlashcardTab } from '@/components/review/FlashcardTab';
import { QuizTab } from '@/components/review/QuizTab';
import { colors, radius, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { useApp } from '@/stores/AppStore';
import { urgencyScore } from '@/data/retention';

type Tab = 'story' | 'cards' | 'quiz';

function parseFocus(raw?: string): string[] {
  return raw ? raw.split(',').filter(Boolean) : [];
}

const TABS: { key: Tab; icon: string; label: string }[] = [
  { key: 'story', icon: '✨', label: 'Story' },
  { key: 'cards', icon: '⟳', label: 'Cards' },
  { key: 'quiz', icon: '◉', label: 'Quiz' },
];

export default function ReviewScreen() {
  const insets = useSafeAreaInsets();
  const { collectedWords, profile, reviewWord } = useApp();
  const [tab, setTab] = useState<Tab>('story');
  // Set when arriving from a solved puzzle, so "Review These Words" actually
  // reviews those words. They'd otherwise sink to the bottom: urgencyScore
  // ranks by decay, and a word collected seconds ago is the least urgent
  // thing in the collection.
  const { focus } = useLocalSearchParams<{ focus?: string }>();
  const router = useRouter();

  // Captured into state rather than read straight from the param. Lazily
  // initialising covers a fresh mount (no frame of unpinned order), and the
  // effect covers arriving at an already-mounted tab with new params.
  const [pinned, setPinned] = useState<string[]>(() => parseFocus(focus));
  useEffect(() => {
    if (!focus) return;
    setPinned(parseFocus(focus));
    // Consume it: the param lives on the tab's route, so leaving it set
    // would re-pin these words every later visit.
    router.setParams({ focus: undefined });
  }, [focus, router]);

  // The pin belongs to the session the student arrived in. Coming back to
  // Review later should give the normal urgency ordering.
  useFocusEffect(useCallback(() => () => setPinned([]), []));

  const reviewWords = useMemo(() => {
    const byUrgency = [...collectedWords].sort(
      (a, b) => urgencyScore(b) - urgencyScore(a),
    );
    if (pinned.length === 0) return byUrgency.slice(0, 8);
    const wanted = new Set(pinned);
    const first = byUrgency.filter((w) => wanted.has(w.word));
    const rest = byUrgency.filter((w) => !wanted.has(w.word));
    return [...first, ...rest].slice(0, 8);
  }, [collectedWords, pinned]);

  const focused = pinned.length > 0;
  const highlight = reviewWords.slice(0, 2).map((w) => w.word);

  return (
    <ScreenBackground floatingWords={false}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 8,
          paddingHorizontal: spacing.screen,
          paddingBottom: 32,
        }}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.title}>Review Session</Text>
            <Text style={styles.subtitle}>
              {reviewWords.length} words · AI-selected
            </Text>
          </View>
          <View style={styles.streakChip}>
            <Text style={styles.streakText}>🔥 {profile?.streak ?? 0}</Text>
          </View>
        </View>

        {highlight.length > 0 && (
          <View style={styles.contextBanner}>
            <Text style={styles.contextIcon}>{focused ? '✨' : '🧠'}</Text>
            <Text style={styles.contextText}>
              {focused ? 'Just collected: ' : 'Most urgent: '}
              <Text style={styles.contextWords}>{highlight.join(', ')}</Text>
            </Text>
          </View>
        )}

        {/* Tab selector */}
        <View style={styles.tabSelector}>
          {TABS.map((t) => {
            const active = t.key === tab;
            return (
              <Pressable
                key={t.key}
                onPress={() => setTab(t.key)}
                style={[styles.tab, active && styles.tabActive]}
              >
                <Text style={styles.tabIcon}>{t.icon}</Text>
                <Text style={[styles.tabLabel, active && { color: colors.yellow }]}>
                  {t.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <View style={{ marginTop: 16 }}>
          {tab === 'story' && <StoryTab words={reviewWords} />}
          {tab === 'cards' && (
            <FlashcardTab words={reviewWords} onReview={reviewWord} />
          )}
          {tab === 'quiz' && <QuizTab words={reviewWords} onReview={reviewWord} />}
        </View>
      </ScrollView>
    </ScreenBackground>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  title: {
    fontFamily: fonts.display,
    fontSize: 22,
    color: colors.text,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  streakChip: {
    backgroundColor: 'rgba(255,107,53,0.16)',
    borderRadius: radius.pill,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  streakText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 12,
    color: colors.orange,
  },
  contextBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(239,68,68,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.25)',
    borderRadius: radius.card,
    padding: 11,
  },
  contextIcon: { fontSize: 15 },
  contextText: {
    flex: 1,
    fontFamily: fonts.body,
    fontSize: 11.5,
    color: colors.textMuted,
  },
  contextWords: {
    fontFamily: fonts.bodyExtra,
    color: colors.redLight,
  },
  tabSelector: {
    flexDirection: 'row',
    gap: 7,
    marginTop: 14,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 11,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  tabActive: {
    backgroundColor: 'rgba(255,229,102,0.1)',
    borderColor: 'rgba(255,229,102,0.4)',
  },
  tabIcon: { fontSize: 13 },
  tabLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 12,
    color: colors.textMuted,
  },
});
