import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { colors } from '@/theme/tokens';
import { fonts } from '@/theme/typography';

interface PassageTextProps {
  passage: string;
  vocab: Record<string, string>; // WORD -> definition
  onWordPress: (word: string, definition: string) => void;
}

/**
 * Renders a passage with vocabulary words highlighted in gold italic serif.
 * Tokens are matched case-insensitively, ignoring surrounding punctuation.
 */
export function PassageText({ passage, vocab, onWordPress }: PassageTextProps) {
  const tokens = passage.split(/(\s+)/);

  return (
    <Text style={styles.base}>
      {tokens.map((token, i) => {
        const bare = token.replace(/[^a-zA-Z]/g, '').toUpperCase();
        const def = vocab[bare];
        if (def) {
          const lead = token.match(/^[^a-zA-Z]*/)?.[0] ?? '';
          const trail = token.match(/[^a-zA-Z]*$/)?.[0] ?? '';
          const core = token.slice(lead.length, token.length - trail.length);
          return (
            <Text key={i}>
              {lead}
              <Text style={styles.vocab} onPress={() => onWordPress(bare, def)}>
                {core}
              </Text>
              {trail}
            </Text>
          );
        }
        return <Text key={i}>{token}</Text>;
      })}
    </Text>
  );
}

const styles = StyleSheet.create({
  base: {
    fontFamily: fonts.serif,
    fontSize: 16,
    lineHeight: 27,
    color: colors.text,
  },
  vocab: {
    fontFamily: fonts.serifItalic,
    color: colors.yellow,
  },
});
