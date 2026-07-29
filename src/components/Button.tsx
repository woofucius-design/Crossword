import React from 'react';
import { Pressable, StyleSheet, Text, ViewStyle } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors, radius, shadows } from '@/theme/tokens';
import { fonts } from '@/theme/typography';

interface ButtonProps {
  label: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'ghost';
  disabled?: boolean;
  style?: ViewStyle;
  small?: boolean;
}

export function Button({
  label,
  onPress,
  variant = 'primary',
  disabled = false,
  style,
  small = false,
}: ButtonProps) {
  const pad: ViewStyle = small
    ? { paddingVertical: 9, paddingHorizontal: 16 }
    : { paddingVertical: 15, paddingHorizontal: 20 };

  if (variant === 'primary') {
    return (
      <Pressable
        onPress={onPress}
        disabled={disabled}
        style={({ pressed }) => [
          // The radius has to be on the shadow-casting view too: Android
          // derives the elevation shadow from this view's outline, and
          // without it every rounded button casts a square one.
          { opacity: disabled ? 0.45 : pressed ? 0.9 : 1, borderRadius: radius.button },
          !disabled && shadows.gold,
          style,
        ]}
      >
        <LinearGradient
          colors={[colors.yellow, colors.yellowDark]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={[styles.base, pad]}
        >
          <Text style={[styles.label, { color: '#3A2A00', fontSize: small ? 13 : 15 }]}>
            {label}
          </Text>
        </LinearGradient>
      </Pressable>
    );
  }

  const bg = variant === 'secondary' ? colors.card : 'transparent';
  const borderColor = variant === 'secondary' ? colors.border : 'transparent';

  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.base,
        pad,
        { backgroundColor: bg, borderWidth: 1, borderColor, opacity: disabled ? 0.45 : pressed ? 0.85 : 1 },
        style,
      ]}
    >
      <Text style={[styles.label, { color: colors.text, fontSize: small ? 13 : 15 }]}>
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  base: {
    borderRadius: radius.button,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    fontFamily: fonts.bodyExtra,
    letterSpacing: 0.2,
  },
});
