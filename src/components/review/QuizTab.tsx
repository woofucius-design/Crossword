import React, { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Button } from '@/components/Button';
import { colors, radius } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import type { CollectedWord } from '@/types/models';

interface QuizTabProps {
  words: CollectedWord[];
  onReview: (wordId: number, gotIt: boolean) => void;
}

interface Question {
  wordId: number;
  word: string;
  options: string[];
  correctIndex: number;
}

const PREFIX = ['A', 'B', 'C', 'D'];

function buildQuestions(words: CollectedWord[]): Question[] {
  const picks = [...words].sort(() => Math.random() - 0.5).slice(0, 4);
  return picks.map((w) => {
    const distractors = words
      .filter((d) => d.wordId !== w.wordId)
      .sort(() => Math.random() - 0.5)
      .slice(0, 3)
      .map((d) => d.definition);
    const options = [...distractors, w.definition].sort(() => Math.random() - 0.5);
    return {
      wordId: w.wordId,
      word: w.word,
      options,
      correctIndex: options.indexOf(w.definition),
    };
  });
}

export function QuizTab({ words, onReview }: QuizTabProps) {
  const [seed, setSeed] = useState(0);
  const questions = useMemo(() => buildQuestions(words), [words, seed]);
  const [index, setIndex] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);

  if (words.length < 4) {
    return (
      <Text style={styles.empty}>
        Collect at least 4 words to unlock the quiz.
      </Text>
    );
  }

  const q = questions[index];

  const choose = (optionIndex: number) => {
    if (picked !== null) return;
    setPicked(optionIndex);
    const correct = optionIndex === q.correctIndex;
    if (correct) setScore((s) => s + 1);
    onReview(q.wordId, correct);
    setTimeout(() => {
      if (index + 1 >= questions.length) {
        setDone(true);
      } else {
        setIndex((i) => i + 1);
        setPicked(null);
      }
    }, 1000);
  };

  const restart = () => {
    setSeed((s) => s + 1);
    setIndex(0);
    setPicked(null);
    setScore(0);
    setDone(false);
  };

  if (done) {
    const pct = Math.round((score / questions.length) * 100);
    return (
      <View style={styles.results}>
        <Text style={styles.resultEmoji}>
          {pct >= 75 ? '🌟' : pct >= 50 ? '👍' : '📖'}
        </Text>
        <Text style={styles.resultPct}>{pct}%</Text>
        <Text style={styles.resultLabel}>
          {score} of {questions.length} correct
        </Text>
        <Button label="Try Again" onPress={restart} style={{ marginTop: 18 }} />
      </View>
    );
  }

  return (
    <View>
      <Text style={styles.counter}>
        Question {index + 1} of {questions.length}
      </Text>
      <View style={styles.wordCard}>
        <Text style={styles.word}>{q.word}</Text>
      </View>
      <Text style={styles.prompt}>Which definition fits?</Text>

      {q.options.map((option, i) => {
        const isCorrect = i === q.correctIndex;
        const isPicked = i === picked;
        let bg: string = colors.surface;
        let border: string = colors.border;
        if (picked !== null) {
          if (isCorrect) {
            bg = 'rgba(52,211,153,0.15)';
            border = colors.mint;
          } else if (isPicked) {
            bg = 'rgba(239,68,68,0.15)';
            border = colors.red;
          }
        }
        return (
          <Pressable
            key={i}
            onPress={() => choose(i)}
            style={[styles.option, { backgroundColor: bg, borderColor: border }]}
          >
            <View style={styles.optionPrefix}>
              <Text style={styles.optionPrefixText}>{PREFIX[i]}</Text>
            </View>
            <Text style={styles.optionText}>{option}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  empty: {
    fontFamily: fonts.body,
    fontSize: 12.5,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 30,
  },
  counter: {
    fontFamily: fonts.bodyBold,
    fontSize: 10.5,
    color: colors.textMuted,
    textAlign: 'center',
  },
  wordCard: {
    backgroundColor: colors.card,
    borderRadius: radius.cardLarge,
    borderWidth: 1,
    borderColor: 'rgba(255,229,102,0.25)',
    paddingVertical: 26,
    alignItems: 'center',
    marginTop: 10,
  },
  word: {
    fontFamily: fonts.display,
    fontSize: 32,
    color: colors.yellow,
    letterSpacing: 0.5,
  },
  prompt: {
    fontFamily: fonts.bodyBold,
    fontSize: 12,
    color: colors.textMuted,
    marginTop: 14,
    marginBottom: 8,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    borderRadius: radius.card,
    borderWidth: 1,
    padding: 13,
    marginBottom: 8,
  },
  optionPrefix: {
    width: 26,
    height: 26,
    borderRadius: 8,
    backgroundColor: 'rgba(255,255,255,0.07)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  optionPrefixText: {
    fontFamily: fonts.display,
    fontSize: 12,
    color: colors.textMuted,
  },
  optionText: {
    flex: 1,
    fontFamily: fonts.serif,
    fontSize: 13,
    color: colors.text,
    lineHeight: 18,
  },
  results: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  resultEmoji: { fontSize: 48 },
  resultPct: {
    fontFamily: fonts.display,
    fontSize: 44,
    color: colors.mint,
    marginTop: 8,
  },
  resultLabel: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 4,
  },
});
