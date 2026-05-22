import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Cell } from './Cell';
import { colors, radius } from '@/theme/tokens';

export interface CellRenderState {
  letter: string;
  isBlack: boolean;
  isSelected: boolean;
  isWordHighlight: boolean;
  number?: number;
  popKey: number;
  rippleKey: number;
  rippleDelay: number;
  rippleVocab: boolean;
}

const GRID_GAP = 2;
const GRID_PADDING = 5;

interface GridProps {
  rows: number;
  cols: number;
  cellSize: number;
  states: Record<string, CellRenderState>;
  onCellPress: (row: number, col: number) => void;
}

export function Grid({ rows, cols, cellSize, states, onCellPress }: GridProps) {
  return (
    <View style={styles.container}>
      {Array.from({ length: rows }, (_, r) => (
        <View key={r} style={[styles.row, { gap: GRID_GAP }]}>
          {Array.from({ length: cols }, (_, c) => {
            const s = states[`${r},${c}`];
            return (
              <Cell
                key={c}
                row={r}
                col={c}
                size={cellSize}
                letter={s.letter}
                isBlack={s.isBlack}
                isSelected={s.isSelected}
                isWordHighlight={s.isWordHighlight}
                number={s.number}
                popKey={s.popKey}
                rippleKey={s.rippleKey}
                rippleDelay={s.rippleDelay}
                rippleVocab={s.rippleVocab}
                onPress={onCellPress}
              />
            );
          })}
        </View>
      ))}
    </View>
  );
}

export function computeCellSize(containerWidth: number, cols: number): number {
  return (containerWidth - GRID_PADDING * 2 - GRID_GAP * (cols - 1)) / cols;
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#0A1420',
    borderRadius: 10,
    padding: GRID_PADDING,
    gap: GRID_GAP,
    borderWidth: 1,
    borderColor: colors.border,
  },
  row: {
    flexDirection: 'row',
  },
});
