import React from 'react';
import { View } from 'react-native';
import { Redirect } from 'expo-router';
import { useApp } from '@/stores/AppStore';
import { colors } from '@/theme/tokens';

/**
 * Entry point. Always lands on Home, including on a first run.
 *
 * Onboarding used to gate the app: six steps, one of them a five-question
 * quiz, before a first-time visitor could see a puzzle. For a free app whose
 * growth depends on people actually reaching the thing that makes it good,
 * that is the most expensive screen in the product. It is now optional and
 * offered from Home once someone has played, when personalising is something
 * they want rather than a toll.
 */
export default function Index() {
  const { hydrated } = useApp();

  if (!hydrated) {
    return <View style={{ flex: 1, backgroundColor: colors.bg }} />;
  }

  return <Redirect href="/(tabs)/home" />;
}
