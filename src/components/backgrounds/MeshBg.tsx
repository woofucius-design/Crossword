import React from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Defs, RadialGradient, Rect, Stop } from 'react-native-svg';
import { colors } from '@/theme/tokens';

/**
 * Radial-gradient mesh background: indigo blob top-left, mint blob
 * bottom-right, gold blob center over the deep-navy base.
 */
export function MeshBg() {
  return (
    <View
      style={[StyleSheet.absoluteFill, { backgroundColor: colors.bg }]}
      pointerEvents="none"
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg style={StyleSheet.absoluteFill} width="100%" height="100%">
        <Defs>
          <RadialGradient id="indigo" cx="12%" cy="8%" r="55%">
            <Stop offset="0%" stopColor="#6366F1" stopOpacity={0.34} />
            <Stop offset="100%" stopColor="#6366F1" stopOpacity={0} />
          </RadialGradient>
          <RadialGradient id="mint" cx="92%" cy="96%" r="58%">
            <Stop offset="0%" stopColor="#34D399" stopOpacity={0.22} />
            <Stop offset="100%" stopColor="#34D399" stopOpacity={0} />
          </RadialGradient>
          <RadialGradient id="gold" cx="52%" cy="46%" r="48%">
            <Stop offset="0%" stopColor="#F5A623" stopOpacity={0.14} />
            <Stop offset="100%" stopColor="#F5A623" stopOpacity={0} />
          </RadialGradient>
        </Defs>
        <Rect width="100%" height="100%" fill="url(#indigo)" />
        <Rect width="100%" height="100%" fill="url(#mint)" />
        <Rect width="100%" height="100%" fill="url(#gold)" />
      </Svg>
    </View>
  );
}
