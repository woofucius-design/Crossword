import React from 'react';
import { Text, View } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { colors } from '@/theme/tokens';
import { fonts } from '@/theme/typography';

interface RetentionArcProps {
  value: number; // 0-100
  size?: number;
  stroke?: number;
  color?: string;
  showLabel?: boolean;
}

/** SVG ring showing a word's retention percentage. */
export function RetentionArc({
  value,
  size = 44,
  stroke = 4,
  color,
  showLabel = true,
}: RetentionArcProps) {
  const clamped = Math.max(0, Math.min(100, value));
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - clamped / 100);
  const arcColor =
    color ?? (clamped < 45 ? colors.red : clamped < 70 ? '#F97316' : colors.mint);

  return (
    <View style={{ width: size, height: size, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size} height={size} style={{ position: 'absolute' }}>
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="rgba(255,255,255,0.09)"
          strokeWidth={stroke}
          fill="none"
        />
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={arcColor}
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </Svg>
      {showLabel && (
        <Text
          style={{
            fontFamily: fonts.display,
            fontSize: size * 0.26,
            color: arcColor,
          }}
        >
          {Math.round(clamped)}
        </Text>
      )}
    </View>
  );
}
