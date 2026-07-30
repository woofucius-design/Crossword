import React, { useCallback } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Tabs } from 'expo-router';
import type { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, maxContentWidth } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { useAndroidBack } from '@/hooks/useAndroidBack';
import { rippleGold, tightText } from '@/theme/platform';

const TAB_META: Record<string, { label: string; icon: string }> = {
  home: { label: 'Home', icon: '◫' },
  puzzles: { label: 'Puzzles', icon: '⊞' },
  collection: { label: 'Collection', icon: '★' },
  review: { label: 'Review', icon: '↻' },
  profile: { label: 'Profile', icon: '◉' },
};

function TabBar({ state, navigation }: BottomTabBarProps) {
  const insets = useSafeAreaInsets();
  const homeIndex = state.routes.findIndex((r) => r.name === 'home');

  // Android convention: back from a secondary tab returns to the first
  // tab, and only exits the app from there. The default pops the whole
  // navigator, which quits mid-review with state lost.
  useAndroidBack(
    useCallback(() => {
      if (state.index === homeIndex || homeIndex < 0) return false;
      navigation.navigate('home' as never);
      return true;
    }, [state.index, homeIndex, navigation]),
  );

  return (
    <View style={[styles.bar, { paddingBottom: Math.max(insets.bottom, 8) }]}>
      <View style={styles.barInner}>
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
              android_ripple={rippleGold()}
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
    backgroundColor: 'rgba(13,27,42,0.96)',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    paddingTop: 8,
  },
  // Full-bleed bar, but the tabs themselves stay phone-width so they don't
  // drift to the far corners of an iPad or a desktop browser.
  barInner: {
    flexDirection: 'row',
    width: '100%',
    maxWidth: maxContentWidth,
    alignSelf: 'center',
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
    ...tightText,
  },
  label: {
    fontFamily: fonts.bodyBold,
    fontSize: 9.5,
    letterSpacing: 0.3,
  },
});
