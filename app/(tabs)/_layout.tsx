import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Tabs } from 'expo-router';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors } from '@/theme/tokens';
import { fonts } from '@/theme/typography';

const TAB_META: Record<string, { label: string; icon: string }> = {
  home: { label: 'Home', icon: '◫' },
  puzzles: { label: 'Puzzles', icon: '⊞' },
  collection: { label: 'Collection', icon: '★' },
  review: { label: 'Review', icon: '↻' },
  profile: { label: 'Profile', icon: '◉' },
};

function TabBar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 8) }]}>
      {state.routes
        .filter((r) => TAB_META[r.name])
        .map((route) => {
          const routeIndex = state.routes.findIndex((r) => r.key === route.key);
          const focused = state.index === routeIndex;
          const meta = TAB_META[route.name];
          const tint = focused ? colors.yellow : colors.textMuted;

          return (
            <Pressable
              key={route.key}
              style={styles.tab}
              onPress={() => {
                const event = navigation.emit({
                  type: 'tabPress',
                  target: route.key,
                  canPreventDefault: true,
                });
                if (!focused && !event.defaultPrevented) {
                  navigation.navigate(route.name);
                }
              }}
            >
              <Text style={[styles.icon, { color: tint }]}>{meta.icon}</Text>
              <Text style={[styles.label, { color: tint }]}>{meta.label}</Text>
            </Pressable>
          );
        })}
    </View>
  );
}

export default function TabsLayout() {
  return (
    <Tabs
      tabBar={(props) => <TabBar {...props} />}
      screenOptions={{ headerShown: false }}
    >
      <Tabs.Screen name="home" />
      <Tabs.Screen name="puzzles" />
      <Tabs.Screen name="collection" />
      <Tabs.Screen name="review" />
      <Tabs.Screen name="profile" />
      <Tabs.Screen name="write" options={{ href: null }} />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    backgroundColor: 'rgba(13,27,42,0.96)',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 8,
    paddingHorizontal: 6,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    gap: 3,
  },
  icon: {
    fontSize: 19,
    lineHeight: 22,
  },
  label: {
    fontFamily: fonts.bodyBold,
    fontSize: 9.5,
    letterSpacing: 0.3,
  },
});
