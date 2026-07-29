import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import type { Avatar as AvatarType } from '@/types/models';
import { colors } from '@/theme/tokens';
import { glowFallback } from '@/theme/platform';

export const avatarEmoji: Record<AvatarType, string> = {
  owl: '🦉',
  fox: '🦊',
  lion: '🦁',
  shark: '🦈',
  wolf: '🐺',
  eagle: '🦅',
};

export const avatarOrder: AvatarType[] = ['owl', 'fox', 'lion', 'shark', 'wolf', 'eagle'];

interface AvatarProps {
  avatar: AvatarType;
  size?: number;
  showDot?: boolean;
  glow?: boolean;
}

export function Avatar({ avatar, size = 38, showDot = false, glow = false }: AvatarProps) {
  return (
    <View style={{ width: size, height: size }}>
      <LinearGradient
        colors={['#6366F1', '#A855F7']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[
          styles.circle,
          { width: size, height: size, borderRadius: size / 2 },
          glow && {
            shadowColor: '#A855F7',
            shadowOpacity: 0.6,
            shadowRadius: 16,
            shadowOffset: { width: 0, height: 0 },
            elevation: 8,
          },
          // Android's elevation shadow ignores shadowColor below API 28,
          // so the purple halo would read as a grey smudge; a hairline
          // ring of the same hue stands in for it.
          glow && glowFallback('rgba(168,85,247,0.55)'),
        ]}
      >
        <Text style={{ fontSize: size * 0.52 }}>{avatarEmoji[avatar]}</Text>
      </LinearGradient>
      {showDot && (
        <View
          style={[
            styles.dot,
            { borderColor: colors.bg, width: size * 0.3, height: size * 0.3, borderRadius: size * 0.15 },
          ]}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  circle: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  dot: {
    position: 'absolute',
    // Flush with the corner rather than overhanging it: Android clips
    // absolutely-positioned children that fall outside the parent box,
    // which made the unread dot vanish entirely.
    top: 0,
    right: 0,
    backgroundColor: colors.orange,
    borderWidth: 2,
  },
});
