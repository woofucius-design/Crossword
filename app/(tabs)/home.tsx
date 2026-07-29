import React, { useEffect, useMemo, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ScreenBackground } from '@/components/ScreenBackground';
import { GradientText } from '@/components/GradientText';
import { Avatar } from '@/components/Avatar';
import { WordChip } from '@/components/WordChip';
import { colors, radius, shadows, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { useApp } from '@/stores/AppStore';
import { samplePuzzle } from '@/data/samplePuzzle';
import { isSlipping, isDue } from '@/data/retention';

const DATE_FMT = new Intl.DateTimeFormat('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
});

const TICKER_WORDS = ['ELOQUENT', 'CANDOR', 'ASTUTE', 'NUANCE', 'PRUDENT'];

export default function HomeScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { profile, collectedWords } = useApp();

  const [tickerIndex, setTickerIndex] = useState(0);
  useEffect(() => {
    const id = setInterval(
      () => setTickerIndex((i) => (i + 1) % TICKER_WORDS.length),
      2200,
    );
    return () => clearInterval(id);
  }, []);

  const stats = useMemo(() => {
    const mastered = collectedWords.filter((w) => w.mastery === 'mastered').length;
    const due = collectedWords.filter(isDue).length;
    return { collected: collectedWords.length, mastered, due };
  }, [collectedWords]);

  const slipping = useMemo(
    () => collectedWords.filter(isSlipping).slice(0, 3),
    [collectedWords],
  );

  const featured = samplePuzzle.words.filter((w) => w.isSATVocab).slice(0, 4);

  return (
    <ScreenBackground floatingOpacity={0.7}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 8,
          paddingHorizontal: spacing.screen,
          paddingBottom: 28,
        }}
        showsVerticalScrollIndicator={false}
      >
        {/* Logo row */}
        <View style={styles.logoRow}>
          <View>
            <GradientText style={styles.logo}>LEXICON</GradientText>
            <Text style={styles.subtitle}>SAT Vocabulary · {DATE_FMT.format(new Date())}</Text>
          </View>
          <Pressable onPress={() => router.push('/(tabs)/profile')}>
            <Avatar avatar={profile?.avatar ?? 'fox'} size={38} showDot />
          </Pressable>
        </View>

        {/* Stats row */}
        <View style={styles.statsRow}>
          <StatTile icon="🔥" value={String(profile?.streak ?? 0)} label="Streak" tint={colors.orange} />
          <StatTile icon="📚" value={String(stats.collected)} label="Collected" tint={colors.yellow} />
          <StatTile icon="◆" value={String(stats.mastered)} label="Mastered" tint={colors.masteryMastered} />
          <StatTile icon="🏆" value="#3" label="Class Rank" tint={colors.mint} />
        </View>

        {/* Daily puzzle card */}
        <Pressable onPress={() => router.push(`/puzzle/${samplePuzzle.date}`)}>
          <LinearGradient
            colors={['#1B3A5B', '#16293D']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={[styles.puzzleCard, shadows.card]}
          >
            <View style={styles.puzzleHeader}>
              <View style={{ flex: 1 }}>
                <View style={styles.badgeRow}>
                  <View style={styles.dailyBadge}>
                    <Text style={styles.dailyBadgeText}>DAILY</Text>
                  </View>
                  <View style={styles.newBadge}>
                    <Text style={styles.newBadgeText}>New Today</Text>
                  </View>
                </View>
                <Text style={styles.puzzleTitle}>Puzzle #{samplePuzzle.number}</Text>
                <Text style={styles.puzzleMeta}>
                  {featured.length} SAT words · ~5 min
                </Text>
              </View>
              <MiniGrid solution={samplePuzzle.solution} />
            </View>

            <Text style={styles.sectionMicro}>TODAY'S FEATURED WORDS INCLUDE</Text>
            <View style={styles.chipRow}>
              {featured.map((w) => (
                <WordChip key={w.id} word={w.answer} />
              ))}
            </View>

            <LinearGradient
              colors={[colors.yellow, colors.yellowDark]}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={[styles.playButton, shadows.gold]}
            >
              <Text style={styles.playButtonText}>▶  Play Today's Puzzle</Text>
            </LinearGradient>
          </LinearGradient>
        </Pressable>

        {/* AI notice banner */}
        {slipping.length > 0 && (
          <Pressable style={styles.aiBanner} onPress={() => router.push('/(tabs)/review')}>
            <Text style={styles.aiIcon}>🧠</Text>
            <View style={{ flex: 1 }}>
              <Text style={styles.aiTitle}>AI Notice: {slipping.length} words slipping</Text>
              <Text style={styles.aiBody}>
                <Text style={styles.aiWords}>
                  {slipping.map((w) => w.word).join(', ')}
                </Text>{' '}
                near the forgetting threshold.
              </Text>
            </View>
            <View style={styles.aiCta}>
              <Text style={styles.aiCtaText}>Review →</Text>
            </View>
          </Pressable>
        )}

        {/* Quick actions */}
        <Text style={styles.sectionLabel}>QUICK ACCESS</Text>
        <View style={styles.quickGrid}>
          <QuickAction
            icon="★"
            tint={colors.yellow}
            title="Collection"
            sub={`${stats.collected} words`}
            onPress={() => router.push('/(tabs)/collection')}
          />
          <QuickAction
            icon="↻"
            tint={colors.masteryNew}
            title="Review"
            sub={`${stats.due} due`}
            badge={stats.due > 0}
            onPress={() => router.push('/(tabs)/review')}
          />
          <QuickAction
            icon="✎"
            tint={colors.mint}
            title="Write"
            sub="Passage mode"
            onPress={() => router.push('/write')}
          />
          <QuickAction
            icon="🏆"
            tint={colors.orange}
            title="Rankings"
            sub="You're #3"
            onPress={() => router.push('/(tabs)/profile')}
          />
        </View>

        {/* Class challenge banner */}
        <Pressable onPress={() => router.push('/write')}>
          <LinearGradient
            colors={['#4338CA', '#6366F1']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.classBanner}
          >
            <View style={styles.classIcon}>
              <Text style={{ fontSize: 18 }}>✎</Text>
            </View>
            <View style={{ flex: 1 }}>
              <View style={styles.classTitleRow}>
                <Text style={styles.classTitle}>Class Writing Challenge</Text>
                <View style={styles.liveBadge}>
                  <Text style={styles.liveText}>LIVE</Text>
                </View>
              </View>
              <Text style={styles.classSub}>Ms. Harmander · 14 students · Due 3pm</Text>
            </View>
            <View style={styles.joinButton}>
              <Text style={styles.joinText}>Join</Text>
            </View>
          </LinearGradient>
        </Pressable>

        {/* Activity ticker */}
        <View style={styles.ticker}>
          <View style={styles.tickerDot} />
          <Text style={styles.tickerText}>
            Your class just collected{' '}
            <Text style={styles.tickerWord}>{TICKER_WORDS[tickerIndex]}</Text>
          </Text>
        </View>
      </ScrollView>
    </ScreenBackground>
  );
}

function StatTile({
  icon,
  value,
  label,
  tint,
}: {
  icon: string;
  value: string;
  label: string;
  tint: string;
}) {
  return (
    <View style={styles.statTile}>
      <Text style={styles.statIcon}>{icon}</Text>
      <Text style={[styles.statValue, { color: tint }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function MiniGrid({ solution }: { solution: string[][] }) {
  const preview = solution.slice(0, 5).map((row) => row.slice(0, 5));
  return (
    <View style={styles.miniGrid}>
      {preview.flatMap((row, r) =>
        row.map((cell, c) => (
          <View
            key={`${r},${c}`}
            style={[
              styles.miniCell,
              { backgroundColor: cell === '#' ? 'transparent' : 'rgba(255,229,102,0.55)' },
            ]}
          />
        )),
      )}
    </View>
  );
}

function QuickAction({
  icon,
  tint,
  title,
  sub,
  badge,
  onPress,
}: {
  icon: string;
  tint: string;
  title: string;
  sub: string;
  badge?: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable
      style={({ pressed }) => [styles.quickCard, pressed && { opacity: 0.85 }]}
      onPress={onPress}
    >
      <View style={[styles.quickIcon, { backgroundColor: tint + '22' }]}>
        <Text style={[styles.quickIconText, { color: tint }]}>{icon}</Text>
      </View>
      <View style={{ flex: 1 }}>
        <Text style={styles.quickTitle}>{title}</Text>
        <Text style={styles.quickSub}>{sub}</Text>
      </View>
      {badge && <View style={styles.quickBadge} />}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  logoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  logo: {
    fontFamily: fonts.display,
    fontSize: 26,
    letterSpacing: 1.5,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 10.5,
    color: colors.textMuted,
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    gap: spacing.cardGap,
    marginBottom: spacing.sectionGap,
  },
  statTile: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 11,
    alignItems: 'center',
    gap: 2,
  },
  statIcon: { fontSize: 15 },
  statValue: { fontFamily: fonts.display, fontSize: 18 },
  statLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 8,
    color: colors.textMuted,
    letterSpacing: 0.4,
    textTransform: 'uppercase',
  },
  puzzleCard: {
    borderRadius: radius.cardLarge,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 16,
    marginBottom: spacing.sectionGap,
  },
  puzzleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  badgeRow: { flexDirection: 'row', gap: 6, marginBottom: 6 },
  dailyBadge: {
    backgroundColor: colors.yellow,
    borderRadius: radius.pill,
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  dailyBadgeText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 8.5,
    color: '#3A2A00',
    letterSpacing: 0.6,
  },
  newBadge: {
    backgroundColor: 'rgba(52,211,153,0.16)',
    borderRadius: radius.pill,
    paddingHorizontal: 7,
    paddingVertical: 2,
  },
  newBadgeText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 8.5,
    color: colors.mint,
    letterSpacing: 0.4,
  },
  puzzleTitle: {
    fontFamily: fonts.display,
    fontSize: 23,
    color: colors.text,
  },
  puzzleMeta: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  miniGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    width: 54,
    height: 54,
    gap: 2,
  },
  miniCell: {
    width: 9,
    height: 9,
    borderRadius: 1.5,
  },
  sectionMicro: {
    fontFamily: fonts.bodyExtra,
    fontSize: 8.5,
    color: colors.textMuted,
    letterSpacing: 0.8,
    marginTop: 14,
    marginBottom: 7,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  playButton: {
    borderRadius: radius.button,
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 14,
  },
  playButtonText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 15,
    color: '#3A2A00',
    letterSpacing: 0.3,
  },
  aiBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: 'rgba(239,68,68,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.28)',
    borderRadius: radius.card,
    padding: 12,
    marginBottom: spacing.sectionGap,
  },
  aiIcon: { fontSize: 20 },
  aiTitle: {
    fontFamily: fonts.bodyExtra,
    fontSize: 12.5,
    color: colors.redLight,
  },
  aiBody: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
    lineHeight: 15,
  },
  aiWords: {
    fontFamily: fonts.bodyExtra,
    color: colors.text,
  },
  aiCta: {
    backgroundColor: colors.red,
    borderRadius: radius.pill,
    paddingHorizontal: 11,
    paddingVertical: 7,
  },
  aiCtaText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
    color: colors.text,
  },
  sectionLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    color: colors.textMuted,
    letterSpacing: 0.9,
    marginBottom: 8,
  },
  quickGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.cardGap,
    marginBottom: spacing.sectionGap,
  },
  quickCard: {
    width: '48.4%',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 12,
  },
  quickIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickIconText: { fontSize: 16 },
  quickTitle: {
    fontFamily: fonts.bodyExtra,
    fontSize: 13,
    color: colors.text,
  },
  quickSub: {
    fontFamily: fonts.body,
    fontSize: 10,
    color: colors.textMuted,
    marginTop: 1,
  },
  quickBadge: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.red,
  },
  classBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    borderRadius: radius.card,
    padding: 12,
    marginBottom: spacing.sectionGap,
  },
  classIcon: {
    width: 38,
    height: 38,
    borderRadius: 11,
    backgroundColor: 'rgba(255,255,255,0.16)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  classTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  classTitle: {
    fontFamily: fonts.bodyExtra,
    fontSize: 13,
    color: colors.text,
  },
  liveBadge: {
    backgroundColor: colors.red,
    borderRadius: 4,
    paddingHorizontal: 5,
    paddingVertical: 1,
  },
  liveText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 7.5,
    color: colors.text,
    letterSpacing: 0.5,
  },
  classSub: {
    fontFamily: fonts.body,
    fontSize: 10,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 2,
  },
  joinButton: {
    backgroundColor: colors.text,
    borderRadius: radius.pill,
    paddingHorizontal: 14,
    paddingVertical: 7,
  },
  joinText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11.5,
    color: '#4338CA',
  },
  ticker: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 11,
    paddingHorizontal: 13,
  },
  tickerDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: colors.mint,
  },
  tickerText: {
    fontFamily: fonts.body,
    fontSize: 11,
    color: colors.textMuted,
  },
  tickerWord: {
    fontFamily: fonts.bodyExtra,
    color: colors.yellow,
  },
});
