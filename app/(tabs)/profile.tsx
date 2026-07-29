import React, { useMemo } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ScreenBackground } from '@/components/ScreenBackground';
import { Avatar } from '@/components/Avatar';
import { colors, masteryColor, radius, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { useApp } from '@/stores/AppStore';
import type { MasteryTier } from '@/types/models';

const TIERS: { key: MasteryTier; label: string }[] = [
  { key: 'new', label: 'New' },
  { key: 'learning', label: 'Learning' },
  { key: 'familiar', label: 'Familiar' },
  { key: 'strong', label: 'Strong' },
  { key: 'mastered', label: 'Mastered' },
];

export default function ProfileScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { profile, collectedWords, submissions, resetToDemo } = useApp();

  const tierCounts = useMemo(() => {
    const counts: Record<MasteryTier, number> = {
      new: 0,
      learning: 0,
      familiar: 0,
      strong: 0,
      mastered: 0,
    };
    for (const w of collectedWords) counts[w.mastery] += 1;
    return counts;
  }, [collectedWords]);

  const maxTier = Math.max(1, ...Object.values(tierCounts));

  const avgRetention = collectedWords.length
    ? Math.round(
        collectedWords.reduce((sum, w) => sum + w.retention, 0) / collectedWords.length,
      )
    : 0;

  const confirmDelete = () => {
    Alert.alert(
      'Delete Account',
      'This permanently erases your profile, collected words, and submissions. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: () => {
            resetToDemo();
            router.replace('/(auth)/onboarding');
          },
        },
      ],
    );
  };

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
        {/* Identity */}
        <View style={styles.identity}>
          <Avatar avatar={profile?.avatar ?? 'fox'} size={72} glow />
          <Text style={styles.username}>{profile?.username ?? 'Player'}</Text>
          <Text style={styles.meta}>
            {profile?.level ?? 'Developing'} · Goal {profile?.goal ?? '1400+'}
          </Text>
        </View>

        {/* Headline stats */}
        <View style={styles.statsRow}>
          <Stat value={String(profile?.streak ?? 0)} label="Day Streak" tint={colors.orange} />
          <Stat value={String(collectedWords.length)} label="Collected" tint={colors.yellow} />
          <Stat value={`${avgRetention}%`} label="Avg Retention" tint={colors.mint} />
          <Stat value={String(submissions.length)} label="Passages" tint={colors.masteryNew} />
        </View>

        {/* Mastery breakdown */}
        <Text style={styles.sectionLabel}>MASTERY BREAKDOWN</Text>
        <View style={styles.masteryCard}>
          {TIERS.map((tier) => (
            <View key={tier.key} style={styles.masteryRow}>
              <Text style={styles.masteryLabel}>{tier.label}</Text>
              <View style={styles.masteryTrack}>
                <View
                  style={[
                    styles.masteryFill,
                    {
                      width: `${(tierCounts[tier.key] / maxTier) * 100}%`,
                      backgroundColor: masteryColor[tier.key],
                    },
                  ]}
                />
              </View>
              <Text style={styles.masteryCount}>{tierCounts[tier.key]}</Text>
            </View>
          ))}
        </View>

        {/* Achievements */}
        <Text style={styles.sectionLabel}>ACHIEVEMENTS</Text>
        <View style={styles.badgeRow}>
          <Badge emoji="🔥" label="7-Day Streak" earned={(profile?.streak ?? 0) >= 7} />
          <Badge emoji="📚" label="20 Words" earned={collectedWords.length >= 20} />
          <Badge emoji="◆" label="First Mastery" earned={tierCounts.mastered > 0} />
          <Badge emoji="✍️" label="First Passage" earned={submissions.length > 0} />
        </View>

        {/* Settings */}
        <Text style={styles.sectionLabel}>SETTINGS</Text>
        <View style={styles.settingsCard}>
          <SettingRow label="Daily puzzle reminder" value="9:00 AM" />
          <SettingRow label="Review nudges" value="On" />
          <SettingRow label="Class" value="English Honors · P2" last />
        </View>

        <Pressable style={styles.dangerButton} onPress={confirmDelete}>
          <Text style={styles.dangerText}>Delete Account</Text>
        </Pressable>
        <Text style={styles.legal}>
          LEXICON v1.0.0 · Privacy Policy · Terms of Service
        </Text>
      </ScrollView>
    </ScreenBackground>
  );
}

function Stat({ value, label, tint }: { value: string; label: string; tint: string }) {
  return (
    <View style={styles.statTile}>
      <Text style={[styles.statValue, { color: tint }]}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

function Badge({ emoji, label, earned }: { emoji: string; label: string; earned: boolean }) {
  return (
    <View style={[styles.badge, { opacity: earned ? 1 : 0.35 }]}>
      <Text style={styles.badgeEmoji}>{emoji}</Text>
      <Text style={styles.badgeLabel}>{label}</Text>
    </View>
  );
}

function SettingRow({
  label,
  value,
  last,
}: {
  label: string;
  value: string;
  last?: boolean;
}) {
  return (
    <View style={[styles.settingRow, last && { borderBottomWidth: 0 }]}>
      <Text style={styles.settingLabel}>{label}</Text>
      <Text style={styles.settingValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  identity: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  username: {
    fontFamily: fonts.display,
    fontSize: 24,
    color: colors.text,
    marginTop: 10,
  },
  meta: {
    fontFamily: fonts.body,
    fontSize: 11.5,
    color: colors.textMuted,
    marginTop: 3,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 6,
  },
  statTile: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 12,
    alignItems: 'center',
  },
  statValue: {
    fontFamily: fonts.display,
    fontSize: 17,
  },
  statLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 8,
    color: colors.textMuted,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    marginTop: 3,
    textAlign: 'center',
  },
  sectionLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    color: colors.textMuted,
    letterSpacing: 0.9,
    marginTop: 20,
    marginBottom: 8,
  },
  masteryCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
    gap: 10,
  },
  masteryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  masteryLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 10.5,
    color: colors.textMuted,
    width: 60,
  },
  masteryTrack: {
    flex: 1,
    height: 8,
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 4,
    overflow: 'hidden',
  },
  masteryFill: {
    height: 8,
    borderRadius: 4,
    minWidth: 4,
  },
  masteryCount: {
    fontFamily: fonts.display,
    fontSize: 12,
    color: colors.text,
    width: 22,
    textAlign: 'right',
  },
  badgeRow: {
    flexDirection: 'row',
    gap: 8,
  },
  badge: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 13,
    alignItems: 'center',
    gap: 5,
  },
  badgeEmoji: { fontSize: 20 },
  badgeLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 8,
    color: colors.textMuted,
    textAlign: 'center',
  },
  settingsCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 13,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  settingLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 12,
    color: colors.text,
  },
  settingValue: {
    fontFamily: fonts.body,
    fontSize: 11.5,
    color: colors.textMuted,
  },
  dangerButton: {
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.4)',
    borderRadius: radius.button,
    paddingVertical: 13,
    alignItems: 'center',
    marginTop: 20,
  },
  dangerText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 13,
    color: colors.red,
  },
  legal: {
    fontFamily: fonts.body,
    fontSize: 10,
    color: colors.textDim,
    textAlign: 'center',
    marginTop: 16,
  },
});
