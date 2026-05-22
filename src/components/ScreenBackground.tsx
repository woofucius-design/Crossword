import React from 'react';
import { StyleSheet, View } from 'react-native';
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
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1 },
});
