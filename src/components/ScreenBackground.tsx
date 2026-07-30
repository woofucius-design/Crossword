import React from 'react';
import { StyleSheet, View } from 'react-native';
import { maxContentWidth } from '@/theme/tokens';
import { MeshBg } from './backgrounds/MeshBg';
import { FloatingWords } from './backgrounds/FloatingWords';

interface ScreenBackgroundProps {
  children: React.ReactNode;
  floatingWords?: boolean;
  floatingOpacity?: number;
}

export function ScreenBackground({
  children,
  floatingWords = true,
  floatingOpacity = 1,
}: ScreenBackgroundProps) {
  return (
    <View style={styles.root}>
      <MeshBg />
      {floatingWords && <FloatingWords opacity={floatingOpacity} />}
      <View style={styles.content}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  content: {
    flex: 1,
    width: '100%',
    maxWidth: maxContentWidth,
    alignSelf: 'center',
  },
});
