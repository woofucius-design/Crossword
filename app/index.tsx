import React from 'react';
import { View } from 'react-native';
import { Redirect } from 'expo-router';
import { useApp } from '@/stores/AppStore';
import { colors } from '@/theme/tokens';

export default function Index() {
  const { hydrated, onboarded } = useApp();

  if (!hydrated) {
    return <View style={{ flex: 1, backgroundColor: colors.bg }} />;
  }

  return <Redirect href={onboarded ? '/(tabs)/home' : '/(auth)/onboarding'} />;
}
