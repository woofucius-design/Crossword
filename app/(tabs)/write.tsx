import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ScreenBackground } from '@/components/ScreenBackground';
import { Button } from '@/components/Button';
import { WordChip } from '@/components/WordChip';
import { ScoreRing } from '@/components/ScoreRing';
import { colors, radius, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { useApp } from '@/stores/AppStore';
import { gradePassage } from '@/data/ai';
import { useAndroidBack } from '@/hooks/useAndroidBack';
import { satWords } from '@/data/satWords';
import type { PassageSubmission } from '@/types/models';

type Phase = 'form' | 'grading' | 'results';

const GRADING_STEPS = [
  'Checking word accuracy…',
  'Measuring conciseness…',
  'Evaluating creativity…',
  'Compiling your score…',
];

const EXAMPLE =
  'The OPULENT host showed surprising CANDOR about the leak, staying STOIC as guests waded toward the LUCID centerpiece.';

const LEADERBOARD = [
  { name: 'Maya R.', score: 94 },
  { name: 'Devon K.', score: 89 },
  { name: 'You', score: 0 },
  { name: 'Priya S.', score: 81 },
  { name: 'Liam T.', score: 77 },
];

export default function WriteScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { collectedWords, addSubmission, profile } = useApp();

  const targetWords = useMemo(() => {
    const fromCollection = collectedWords.slice(0, 5).map((w) => w.word);
    if (fromCollection.length === 5) return fromCollection;
    return satWords.slice(0, 5).map((w) => w.word);
  }, [collectedWords]);

  const [phase, setPhase] = useState<Phase>('form');
  const [text, setText] = useState('');
  const [step, setStep] = useState(0);
  const [result, setResult] = useState<PassageSubmission | null>(null);

  const lower = text.toLowerCase();
  const usedFlags = targetWords.map((w) =>
    new RegExp(`\\b${w.toLowerCase()}`, 'i').test(lower),
  );
  const usedCount = usedFlags.filter(Boolean).length;
  const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
  const canSubmit = usedCount >= 1 && text.trim().length >= 20;

  // Live score estimates.
  const estAccuracy = Math.round((usedCount / targetWords.length) * 100);
  const estConcise = wordCount === 0 ? 0 : Math.max(40, Math.min(95, 120 - wordCount));
  const estCreative = Math.min(90, 45 + wordCount);

  const submit = async () => {
    setPhase('grading');
    setStep(0);
    const stepTimer = setInterval(() => {
      setStep((s) => Math.min(s + 1, GRADING_STEPS.length - 1));
    }, 1000);

    const { result: grade } = await gradePassage(text, targetWords);
    clearInterval(stepTimer);
    // Android back can unmount this screen while grading is in flight.
    if (!mounted.current) return;

    const submission: PassageSubmission = {
      id: `sub-${Date.now()}`,
      userId: profile?.id ?? 'demo-user',
      classId: profile?.classId,
      targetWords,
      passage: text,
      scores: grade.scores,
      wordFeedback: grade.wordFeedback,
      feedback: grade.feedback,
      submittedAt: new Date().toISOString(),
    };
    setResult(submission);
    addSubmission(submission);
    setPhase('results');
  };

  const reset = () => {
    setText('');
    setResult(null);
    setPhase('form');
  };

  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);

  // Back during grading would drop an in-flight AI call; back on results
  // would silently discard the grade. Both get an explicit decision.
  const onAndroidBack = useCallback(() => {
    if (phase === 'grading') return true;
    if (phase === 'results') {
      Alert.alert('Discard this passage?', 'Your score and feedback will be lost.', [
        { text: 'Keep reading', style: 'cancel' },
        { text: 'Discard', style: 'destructive', onPress: () => router.back() },
      ]);
      return true;
    }
    if (text.trim().length >= 20) {
      Alert.alert('Discard this draft?', 'Your unsubmitted passage will be lost.', [
        { text: 'Keep writing', style: 'cancel' },
        { text: 'Discard', style: 'destructive', onPress: () => router.back() },
      ]);
      return true;
    }
    return false;
  }, [phase, text, router]);

  useAndroidBack(onAndroidBack);

  return (
    <ScreenBackground floatingWords={false}>
      {/* iOS needs explicit padding; Android's windowSoftInputMode=resize
          already shrinks the window, and 'padding' would double-count it. */}
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 8,
          paddingHorizontal: spacing.screen,
          paddingBottom: 36,
        }}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        keyboardDismissMode="interactive"
      >
        {/* Header */}
        <View style={styles.header}>
          <Pressable
            onPress={() => router.back()}
            hitSlop={10}
            accessibilityRole="button"
            accessibilityLabel="Back"
          >
            <Text style={styles.back}>←</Text>
          </Pressable>
          <View style={{ flex: 1 }}>
            <Text style={styles.title}>Passage Writing</Text>
            <Text style={styles.subtitle}>Ms. Harmander's class</Text>
          </View>
          <View style={styles.compBadge}>
            <Text style={styles.compText}>Class Competition</Text>
          </View>
        </View>

        {phase === 'form' && (
          <>
            <View style={styles.instructionCard}>
              <Text style={styles.instructionTitle}>Write a short passage</Text>
              <Text style={styles.instructionBody}>
                Use the target words below in context. You're scored on{' '}
                <Text style={styles.bold}>accuracy</Text>,{' '}
                <Text style={styles.bold}>conciseness</Text>, and{' '}
                <Text style={styles.bold}>creativity</Text>.
              </Text>
            </View>

            <Text style={styles.sectionLabel}>TARGET WORDS</Text>
            <View style={styles.chipRow}>
              {targetWords.map((w, i) => (
                <WordChip key={w} word={w} done={usedFlags[i]} />
              ))}
            </View>

            <View style={styles.editorCard}>
              <Text style={styles.quoteMark}>"</Text>
              <TextInput
                style={styles.editor}
                value={text}
                onChangeText={setText}
                multiline
                placeholder="Start writing your passage…"
                placeholderTextColor={colors.textDim}
                selectionColor={colors.yellow}
                textAlignVertical="top"
                keyboardAppearance="dark"
                autoCapitalize="sentences"
                autoCorrect
                spellCheck
                scrollEnabled={false}
              />
              <View style={styles.editorFooter}>
                <Text style={styles.wordCount}>{wordCount} words</Text>
                <Text style={styles.hint}>
                  {usedCount}/{targetWords.length} target words used
                </Text>
              </View>
            </View>

            <Pressable style={styles.exampleHint} onPress={() => setText(EXAMPLE)}>
              <Text style={styles.exampleLabel}>💡 Need a spark? Tap to use an example</Text>
              <Text style={styles.exampleText} numberOfLines={2}>
                {EXAMPLE}
              </Text>
            </Pressable>

            <Text style={styles.sectionLabel}>LIVE ESTIMATE</Text>
            <View style={styles.estimateRow}>
              <EstimateChip label="Accuracy" value={estAccuracy} color={colors.masteryNew} />
              <EstimateChip label="Concise" value={estConcise} color={colors.mint} />
              <EstimateChip label="Creative" value={estCreative} color={colors.masteryFamiliar} />
            </View>

            <Button
              label="Submit for Grading"
              onPress={submit}
              disabled={!canSubmit}
              style={{ marginTop: 18 }}
            />
            {!canSubmit && (
              <Text style={styles.lockHint}>
                Use at least 1 target word and 20+ characters to submit.
              </Text>
            )}
          </>
        )}

        {phase === 'grading' && (
          <View style={styles.gradingWrap}>
            <ActivityIndicator size="large" color={colors.yellow} />
            <Text style={styles.gradingTitle}>Grading your passage</Text>
            {GRADING_STEPS.map((label, i) => (
              <View key={i} style={styles.gradingStep}>
                <Text style={styles.gradingStepIcon}>
                  {i < step ? '✓' : i === step ? '◐' : '○'}
                </Text>
                <Text
                  style={[
                    styles.gradingStepText,
                    i <= step && { color: colors.text },
                  ]}
                >
                  {label}
                </Text>
              </View>
            ))}
          </View>
        )}

        {phase === 'results' && result && (
          <>
            <View style={styles.gradeHeader}>
              <Text style={styles.gradeEmoji}>
                {result.scores.overall >= 85 ? '🏆' : result.scores.overall >= 70 ? '🎯' : '📚'}
              </Text>
              <Text style={styles.gradeScore}>{result.scores.overall}</Text>
              <Text style={styles.gradeLabel}>Overall Score</Text>
            </View>

            <View style={styles.ringRow}>
              <ScoreRing value={result.scores.accuracy} label="Accuracy" color={colors.masteryNew} delay={0} />
              <ScoreRing value={result.scores.conciseness} label="Concise" color={colors.mint} delay={150} />
              <ScoreRing value={result.scores.creativity} label="Creative" color={colors.masteryFamiliar} delay={300} />
            </View>

            <View style={styles.feedbackCard}>
              <Text style={styles.feedbackLabel}>🤖 AI FEEDBACK</Text>
              <Text style={styles.feedbackText}>{result.feedback}</Text>
            </View>

            <Text style={styles.sectionLabel}>WORD-BY-WORD</Text>
            {result.wordFeedback.map((wf) => (
              <View key={wf.word} style={styles.wordFeedbackRow}>
                <Text style={styles.wfIcon}>
                  {!wf.used ? '○' : wf.correct ? '✅' : '⚠️'}
                </Text>
                <Text style={styles.wfWord}>{wf.word}</Text>
                <Text style={styles.wfNote} numberOfLines={2}>
                  {wf.note}
                </Text>
              </View>
            ))}

            {/* Leaderboard */}
            <Text style={styles.sectionLabel}>CLASS LEADERBOARD</Text>
            <View style={styles.leaderboard}>
              {LEADERBOARD.map((entry) => {
                const score = entry.name === 'You' ? result.scores.overall : entry.score;
                return { ...entry, score };
              })
                .sort((a, b) => b.score - a.score)
                .map((entry, i) => (
                  <View
                    key={entry.name}
                    style={[
                      styles.leaderRow,
                      entry.name === 'You' && styles.leaderRowYou,
                    ]}
                  >
                    <Text style={styles.leaderRank}>{i + 1}</Text>
                    <Text
                      style={[
                        styles.leaderName,
                        entry.name === 'You' && { color: colors.yellow },
                      ]}
                    >
                      {entry.name}
                    </Text>
                    <Text style={styles.leaderScore}>{entry.score}</Text>
                  </View>
                ))}
            </View>

            <Button label="Write Another" onPress={reset} style={{ marginTop: 18 }} />
          </>
        )}
      </ScrollView>
      </KeyboardAvoidingView>
    </ScreenBackground>
  );
}

function EstimateChip({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <View style={styles.estimateChip}>
      <Text style={[styles.estimateValue, { color }]}>{value}</Text>
      <Text style={styles.estimateLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 14,
  },
  back: { fontSize: 22, color: colors.text },
  title: {
    fontFamily: fonts.display,
    fontSize: 19,
    color: colors.text,
  },
  subtitle: {
    fontFamily: fonts.body,
    fontSize: 10.5,
    color: colors.textMuted,
    marginTop: 1,
  },
  compBadge: {
    backgroundColor: 'rgba(99,102,241,0.18)',
    borderRadius: radius.pill,
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.4)',
  },
  compText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9,
    color: '#A5B4FC',
  },
  instructionCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 13,
  },
  instructionTitle: {
    fontFamily: fonts.bodyExtra,
    fontSize: 13,
    color: colors.text,
  },
  instructionBody: {
    fontFamily: fonts.body,
    fontSize: 11.5,
    color: colors.textMuted,
    marginTop: 4,
    lineHeight: 17,
  },
  bold: {
    fontFamily: fonts.bodyExtra,
    color: colors.text,
  },
  sectionLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9.5,
    color: colors.textMuted,
    letterSpacing: 0.9,
    marginTop: 16,
    marginBottom: 8,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  editorCard: {
    backgroundColor: '#0F1E30',
    borderRadius: radius.cardLarge,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 14,
    paddingTop: 24,
    marginTop: 14,
  },
  quoteMark: {
    position: 'absolute',
    top: 0,
    left: 10,
    fontFamily: fonts.serif,
    fontSize: 50,
    color: 'rgba(255,229,102,0.14)',
  },
  editor: {
    fontFamily: fonts.serif,
    fontSize: 16,
    color: colors.text,
    lineHeight: 24,
    minHeight: 130,
  },
  editorFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 10,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  wordCount: {
    fontFamily: fonts.bodyBold,
    fontSize: 10,
    color: colors.textMuted,
  },
  hint: {
    fontFamily: fonts.bodyBold,
    fontSize: 10,
    color: colors.yellow,
  },
  exampleHint: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 11,
    marginTop: 10,
  },
  exampleLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 10.5,
    color: colors.textMuted,
  },
  exampleText: {
    fontFamily: fonts.serifItalic,
    fontSize: 11.5,
    color: colors.textDim,
    marginTop: 4,
    lineHeight: 16,
  },
  estimateRow: {
    flexDirection: 'row',
    gap: 8,
  },
  estimateChip: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: 11,
    alignItems: 'center',
  },
  estimateValue: {
    fontFamily: fonts.display,
    fontSize: 19,
  },
  estimateLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 9,
    color: colors.textMuted,
    marginTop: 2,
  },
  lockHint: {
    fontFamily: fonts.body,
    fontSize: 10.5,
    color: colors.textDim,
    textAlign: 'center',
    marginTop: 8,
  },
  gradingWrap: {
    alignItems: 'center',
    paddingVertical: 50,
  },
  gradingTitle: {
    fontFamily: fonts.display,
    fontSize: 17,
    color: colors.text,
    marginTop: 18,
    marginBottom: 18,
  },
  gradingStep: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    alignSelf: 'stretch',
    paddingHorizontal: 30,
    paddingVertical: 7,
  },
  gradingStepIcon: {
    fontSize: 14,
    color: colors.yellow,
    width: 18,
  },
  gradingStepText: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.textDim,
  },
  gradeHeader: {
    alignItems: 'center',
    paddingVertical: 14,
  },
  gradeEmoji: { fontSize: 40 },
  gradeScore: {
    fontFamily: fonts.display,
    fontSize: 54,
    color: colors.yellow,
    marginTop: 4,
  },
  gradeLabel: {
    fontFamily: fonts.bodyBold,
    fontSize: 11,
    color: colors.textMuted,
  },
  ringRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 8,
  },
  feedbackCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 13,
    marginTop: 18,
  },
  feedbackLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 9,
    color: colors.textMuted,
    letterSpacing: 0.7,
  },
  feedbackText: {
    fontFamily: fonts.serif,
    fontSize: 13.5,
    color: colors.text,
    lineHeight: 20,
    marginTop: 6,
  },
  wordFeedbackRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 11,
    marginBottom: 7,
  },
  wfIcon: { fontSize: 13, width: 20 },
  wfWord: {
    fontFamily: fonts.display,
    fontSize: 12,
    color: colors.text,
    width: 78,
  },
  wfNote: {
    flex: 1,
    fontFamily: fonts.body,
    fontSize: 10.5,
    color: colors.textMuted,
    lineHeight: 14,
  },
  leaderboard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  leaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 11,
    paddingHorizontal: 13,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  leaderRowYou: {
    backgroundColor: 'rgba(255,229,102,0.08)',
  },
  leaderRank: {
    fontFamily: fonts.display,
    fontSize: 13,
    color: colors.textMuted,
    width: 18,
  },
  leaderName: {
    flex: 1,
    fontFamily: fonts.bodyExtra,
    fontSize: 12.5,
    color: colors.text,
  },
  leaderScore: {
    fontFamily: fonts.display,
    fontSize: 14,
    color: colors.mint,
  },
});
