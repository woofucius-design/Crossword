import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { ScreenBackground } from '@/components/ScreenBackground';
import { Button } from '@/components/Button';
import { colors, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';

/**
 * Catch-all for routes that don't exist. Without this, a stale or malformed
 * deep link (`lexicon://puzzle/not-a-date`) drops the user on expo-router's
 * raw developer error screen.
 */
export default function NotFound() {
  const router = useRouter();

  return (
    <ScreenBackground floatingWords={false}>
      <View style={styles.wrap}>
        <Text style={styles.mark}>◆</Text>
        <Text style={styles.title}>This page went missing</Text>
        <Text style={styles.body}>
          That link doesn't point anywhere in LEXICON. It may be out of date.
        </Text>
        <Button
          label="Back to Home"
          onPress={() => router.replace('/(tabs)/home')}
          style={{ marginTop: 26, alignSelf: 'stretch' }}
        />
      </View>
    </ScreenBackground>
  );
}

const styles = StyleSheet.create({
  wrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.screen + 12,
  },
  mark: {
    fontSize: 34,
    color: colors.yellowDark,
  },
  title: {
    fontFamily: fonts.display,
    fontSize: 22,
    color: colors.text,
    marginTop: 14,
    textAlign: 'center',
  },
  body: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 8,
    textAlign: 'center',
    lineHeight: 19,
  },
});
