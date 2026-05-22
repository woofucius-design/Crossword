import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, radius } from '@/theme/tokens';
import { fonts } from '@/theme/typography';

const ROWS = ['QWERTYUIOP', 'ASDFGHJKL', 'ZXCVBNM'];

interface KeyboardProps {
  onKey: (letter: string) => void;
  onDelete: () => void;
}

/** Custom on-screen keyboard — the system keyboard is never used for the grid. */
export function Keyboard({ onKey, onDelete }: KeyboardProps) {
  return (
    <View style={styles.keyboard}>
      {ROWS.map((row, i) => (
        <View key={i} style={styles.row}>
          {i === 2 && <View style={{ flex: 0.5 }} />}
          {row.split('').map((letter) => (
            <Pressable
              key={letter}
              onPress={() => onKey(letter)}
              style={({ pressed }) => [styles.key, pressed && styles.keyPressed]}
            >
              <Text style={styles.keyText}>{letter}</Text>
            </Pressable>
          ))}
          {i === 2 && (
            <Pressable
              onPress={onDelete}
              style={({ pressed }) => [
                styles.key,
                styles.keyWide,
                pressed && styles.keyPressed,
              ]}
            >
              <Text style={styles.keyText}>⌫</Text>
            </Pressable>
          )}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  keyboard: {
    gap: 7,
    paddingHorizontal: 4,
  },
  row: {
    flexDirection: 'row',
    gap: 5,
    justifyContent: 'center',
  },
  key: {
    flex: 1,
    height: 44,
    backgroundColor: colors.card,
    borderRadius: 7,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  keyWide: {
    flex: 1.6,
  },
  keyPressed: {
    backgroundColor: colors.yellow,
  },
  keyText: {
    fontFamily: fonts.displayMedium,
    fontSize: 16,
    color: colors.text,
  },
});
