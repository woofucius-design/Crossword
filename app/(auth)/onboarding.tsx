import React, { useCallback, useMemo, useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Animated, { FadeIn, FadeOut } from 'react-native-reanimated';
import { ScreenBackground } from '@/components/ScreenBackground';
import { GradientText } from '@/components/GradientText';
import { Button } from '@/components/Button';
import { WordChip } from '@/components/WordChip';
import { Avatar, avatarEmoji, avatarOrder } from '@/components/Avatar';
import { colors, radius, spacing } from '@/theme/tokens';
import { fonts } from '@/theme/typography';
import { useApp } from '@/stores/AppStore';
import { satWords, buildQuiz } from '@/data/satWords';
import { useAndroidBack } from '@/hooks/useAndroidBack';
import type {
  Avatar as AvatarType,
  CollectedWord,
  Goal,
  Level,
  TestDate,
  UserProfile,
} from '@/types/models';

const GOALS: { key: Goal; color: string }[] = [
  { key: '1200+', color: colors.masteryNew },
  { key: '1400+', color: colors.mint },
  { key: '1500+', color: colors.masteryFamiliar },
  { key: '1600', color: colors.masteryMastered },
];

const TEST_DATES: { key: TestDate; label: string }[] = [
  { key: '1month', label: '1 month' },
  { key: '3months', label: '3 months' },
  { key: '6months', label: '6 months' },
  { key: '1year', label: '1 year' },
  { key: 'unsure', label: 'Not sure' },
];

const STARTER_WORDS = ['ELOQUENT', 'PRUDENT', 'ASTUTE', 'ZEALOUS', 'PLACID'];

function levelFromScore(score: number): Level {
  if (score >= 4) return 'Advanced';
  if (score >= 3) return 'Intermediate';
  if (score >= 2) return 'Developing';
  return 'Beginner';
}

export default function Onboarding() {
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const { completeOnboarding } = useApp();

  const [step, setStep] = useState(0);
  const [avatar, setAvatar] = useState<AvatarType>('owl');
  const [username, setUsername] = useState('');
  const [goal, setGoal] = useState<Goal>('1400+');
  const [testDate, setTestDate] = useState<TestDate>('3months');
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizScore, setQuizScore] = useState(0);
  const [picked, setPicked] = useState<number | null>(null);

  const quiz = useMemo(() => buildQuiz(satWords, 5), []);
  const level = levelFromScore(quizScore);

  const finish = () => {
    const profile: UserProfile = {
      id: `user-${Date.now()}`,
      username: username.trim() || 'Player',
      avatar,
      goal,
      testDate,
      level,
      streak: 1,
      classId: undefined,
      createdAt: new Date().toISOString(),
    };
    const starter: CollectedWord[] = STARTER_WORDS.map((word, i) => {
      const meta = satWords.find((w) => w.word === word);
      return {
        id: `starter-${i}`,
        userId: profile.id,
        wordId: meta?.id ?? 1000 + i,
        word,
        definition: meta?.definition ?? '',
        mastery: 'new',
        retention: 100,
        reviewCount: 0,
        collectedAt: new Date().toISOString(),
        lastReviewAt: null,
        puzzleDate: new Date().toISOString().slice(0, 10),
      };
    });
    completeOnboarding(profile, starter);
    router.replace('/(tabs)/home');
  };

  // Android back walks the steps instead of popping the route — popping
  // lands on index.tsx, which redirects straight back to step 0 and loses
  // everything the student just entered.
  const onAndroidBack = useCallback(() => {
    if (step === 0) return false; // nothing entered yet; let it exit
    if (step === 5) return true; // quiz already scored; finish via the button
    if (step === 4) {
      // Leaving mid-quiz: reset so re-entry can't double-count the score.
      setQuizIndex(0);
      setQuizScore(0);
      setPicked(null);
      setStep(3);
      return true;
    }
    setStep((s) => s - 1);
    return true;
  }, [step]);

  useAndroidBack(onAndroidBack);

  const answerQuiz = (optionIndex: number) => {
    if (picked !== null) return;
    setPicked(optionIndex);
    const correct = optionIndex === quiz[quizIndex].correctIndex;
    if (correct) setQuizScore((s) => s + 1);
    setTimeout(() => {
      if (quizIndex + 1 >= quiz.length) {
        setStep(5);
      } else {
        setQuizIndex((i) => i + 1);
        setPicked(null);
      }
    }, 900);
  };

  return (
    <ScreenBackground floatingOpacity={step <= 1 ? 1 : 0.3}>
      <View style={{ flex: 1, paddingTop: insets.top + 12 }}>
        {/* Progress dots for steps 2-4 */}
        {step >= 2 && step <= 4 && (
          <View style={styles.dots}>
            {[2, 3, 4].map((s) => (
              <View
                key={s}
                style={[
                  styles.dot,
                  { backgroundColor: s <= step ? colors.yellow : 'rgba(255,255,255,0.15)' },
                ]}
              />
            ))}
          </View>
        )}

        <ScrollView
          contentContainerStyle={{
            flexGrow: 1,
            paddingHorizontal: 24,
            paddingBottom: insets.bottom + 24,
            justifyContent: 'center',
          }}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          <Animated.View key={step} entering={FadeIn.duration(260)} exiting={FadeOut.duration(120)}>
            {/* Step 0 — Splash */}
            {step === 0 && (
              <View style={styles.centered}>
                <GradientText style={styles.bigLogo}>LEXICON</GradientText>
                <Text style={styles.tagline}>Collect words. Beat the SAT.</Text>
                <View style={styles.chipCloud}>
                  {['LUCID', 'CANDOR', 'OPULENT', 'STOIC', 'TERSE'].map((w) => (
                    <WordChip key={w} word={w} />
                  ))}
                </View>
                <Button
                  label="Start Collecting  →"
                  onPress={() => setStep(1)}
                  style={{ marginTop: 36, alignSelf: 'stretch' }}
                />
              </View>
            )}

            {/* Step 1 — Collection Hook */}
            {step === 1 && (
              <View style={styles.centered}>
                <Text style={styles.stepTitle}>Words are trophies</Text>
                <Text style={styles.stepBody}>
                  Solve a crossword and the SAT words you uncover are collected
                  automatically — like a Pokédex for vocabulary.
                </Text>
                <View style={styles.hookCards}>
                  {satWords.slice(0, 5).map((w, i) => (
                    <Animated.View
                      key={w.id}
                      entering={FadeIn.delay(i * 140).duration(420)}
                      style={[
                        styles.hookCard,
                        { borderLeftColor: GOALS[i % GOALS.length].color },
                      ]}
                    >
                      <Text style={styles.hookWord}>{w.word}</Text>
                      <Text style={styles.hookDef} numberOfLines={1}>
                        {w.definition}
                      </Text>
                    </Animated.View>
                  ))}
                </View>
                <Button
                  label="Continue"
                  onPress={() => setStep(2)}
                  style={{ marginTop: 28, alignSelf: 'stretch' }}
                />
              </View>
            )}

            {/* Step 2 — Profile Setup */}
            {step === 2 && (
              <View>
                <Text style={styles.stepTitle}>Make it yours</Text>
                <View style={styles.avatarPreview}>
                  <Avatar avatar={avatar} size={80} glow />
                </View>
                <View style={styles.avatarGrid}>
                  {avatarOrder.map((a) => (
                    <Pressable
                      key={a}
                      onPress={() => setAvatar(a)}
                      style={[
                        styles.avatarOption,
                        avatar === a && styles.avatarOptionActive,
                      ]}
                    >
                      <Text style={{ fontSize: 26 }}>{avatarEmoji[a]}</Text>
                    </Pressable>
                  ))}
                </View>
                <TextInput
                  style={styles.usernameInput}
                  value={username}
                  onChangeText={setUsername}
                  placeholder="Your name"
                  placeholderTextColor={colors.textDim}
                  selectionColor={colors.yellow}
                  maxLength={16}
                  textAlign="center"
                  // iOS defaults to a light keyboard, which flashes white
                  // against this dark theme.
                  keyboardAppearance="dark"
                  autoCapitalize="words"
                  autoCorrect={false}
                  returnKeyType="done"
                  textContentType="nickname"
                  onSubmitEditing={() => username.trim() && setStep(3)}
                />
                <Button
                  label={username.trim() ? `Looks good, ${username.trim()}!` : 'Choose a name'}
                  onPress={() => setStep(3)}
                  disabled={!username.trim()}
                  style={{ marginTop: 24 }}
                />
              </View>
            )}

            {/* Step 3 — SAT Goal */}
            {step === 3 && (
              <View>
                <Text style={styles.stepTitle}>What's your target?</Text>
                <View style={styles.goalGrid}>
                  {GOALS.map((g) => (
                    <Pressable
                      key={g.key}
                      onPress={() => setGoal(g.key)}
                      style={[
                        styles.goalTile,
                        {
                          borderColor: goal === g.key ? g.color : colors.border,
                          backgroundColor: goal === g.key ? g.color + '1A' : colors.surface,
                        },
                      ]}
                    >
                      <Text style={[styles.goalScore, { color: g.color }]}>{g.key}</Text>
                    </Pressable>
                  ))}
                </View>

                <Text style={styles.subLabel}>When's your test?</Text>
                <View style={styles.dateRow}>
                  {TEST_DATES.map((d) => (
                    <Pressable
                      key={d.key}
                      onPress={() => setTestDate(d.key)}
                      style={[
                        styles.dateChip,
                        testDate === d.key && styles.dateChipActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.dateChipText,
                          testDate === d.key && { color: colors.yellow },
                        ]}
                      >
                        {d.label}
                      </Text>
                    </Pressable>
                  ))}
                </View>

                <View style={styles.insight}>
                  <Text style={styles.insightText}>
                    For {goal} in {TEST_DATES.find((d) => d.key === testDate)?.label},
                    aim for{' '}
                    <Text style={styles.insightBold}>
                      {testDate === '1month' ? 8 : testDate === '3months' ? 4 : 2} new
                      words/day
                    </Text>
                    .
                  </Text>
                </View>

                <Button label="Continue" onPress={() => setStep(4)} style={{ marginTop: 22 }} />
              </View>
            )}

            {/* Step 4 — Level Check */}
            {step === 4 && (
              <View>
                <Text style={styles.stepTitle}>Quick level check</Text>
                <Text style={styles.stepBody}>
                  Question {quizIndex + 1} of {quiz.length}
                </Text>
                <View style={styles.quizWordCard}>
                  <Text style={styles.quizWord}>{quiz[quizIndex].word}</Text>
                </View>
                {quiz[quizIndex].options.map((option, i) => {
                  const isCorrect = i === quiz[quizIndex].correctIndex;
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
                      onPress={() => answerQuiz(i)}
                      style={[styles.quizOption, { backgroundColor: bg, borderColor: border }]}
                    >
                      <Text style={styles.quizOptionText}>{option}</Text>
                    </Pressable>
                  );
                })}
              </View>
            )}

            {/* Step 5 — Welcome */}
            {step === 5 && (
              <View style={styles.centered}>
                <Avatar avatar={avatar} size={90} glow />
                <Text style={styles.welcomeTitle}>Ready, {username.trim() || 'Player'}!</Text>
                <Text style={styles.levelPill}>{level} level</Text>
                <Text style={styles.stepBody}>
                  Here's your starter pack — 5 words already in your collection.
                </Text>
                <View style={styles.chipCloud}>
                  {STARTER_WORDS.map((w) => (
                    <WordChip key={w} word={w} done />
                  ))}
                </View>
                <Button
                  label="Play First Puzzle"
                  onPress={finish}
                  style={{ marginTop: 32, alignSelf: 'stretch' }}
                />
              </View>
            )}
          </Animated.View>
        </ScrollView>
      </View>
    </ScreenBackground>
  );
}

const styles = StyleSheet.create({
  dots: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 8,
    marginBottom: 8,
  },
  dot: {
    width: 22,
    height: 5,
    borderRadius: 3,
  },
  centered: {
    alignItems: 'center',
  },
  bigLogo: {
    fontFamily: fonts.display,
    fontSize: 46,
    letterSpacing: 3,
  },
  tagline: {
    fontFamily: fonts.serifItalic,
    fontSize: 15,
    color: colors.textMuted,
    marginTop: 8,
  },
  chipCloud: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 8,
    marginTop: 28,
  },
  stepTitle: {
    fontFamily: fonts.display,
    fontSize: 26,
    color: colors.text,
    textAlign: 'center',
  },
  stepBody: {
    fontFamily: fonts.body,
    fontSize: 13,
    color: colors.textMuted,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 19,
  },
  hookCards: {
    alignSelf: 'stretch',
    gap: 8,
    marginTop: 22,
  },
  hookCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderLeftWidth: 4,
    padding: 12,
  },
  hookWord: {
    fontFamily: fonts.display,
    fontSize: 16,
    color: colors.text,
  },
  hookDef: {
    fontFamily: fonts.serif,
    fontSize: 11,
    color: colors.textMuted,
    marginTop: 2,
  },
  avatarPreview: {
    alignItems: 'center',
    marginVertical: 18,
  },
  avatarGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  avatarOption: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: colors.surface,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarOptionActive: {
    borderColor: colors.yellow,
    backgroundColor: 'rgba(255,229,102,0.12)',
  },
  usernameInput: {
    fontFamily: fonts.display,
    fontSize: 24,
    color: colors.text,
    borderBottomWidth: 1.5,
    borderBottomColor: colors.border,
    paddingVertical: 12,
    marginTop: 28,
  },
  goalGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginTop: 20,
  },
  goalTile: {
    width: '47.5%',
    borderRadius: radius.card,
    borderWidth: 1.5,
    paddingVertical: 22,
    alignItems: 'center',
  },
  goalScore: {
    fontFamily: fonts.display,
    fontSize: 24,
  },
  subLabel: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
    color: colors.textMuted,
    letterSpacing: 0.6,
    marginTop: 22,
    marginBottom: 10,
  },
  dateRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
  },
  dateChip: {
    paddingHorizontal: 13,
    paddingVertical: 8,
    borderRadius: radius.pill,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  dateChipActive: {
    backgroundColor: 'rgba(255,229,102,0.12)',
    borderColor: 'rgba(255,229,102,0.4)',
  },
  dateChipText: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11.5,
    color: colors.textMuted,
  },
  insight: {
    backgroundColor: 'rgba(52,211,153,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(52,211,153,0.25)',
    borderRadius: radius.card,
    padding: 12,
    marginTop: 18,
  },
  insightText: {
    fontFamily: fonts.body,
    fontSize: 12.5,
    color: colors.textMuted,
    lineHeight: 18,
  },
  insightBold: {
    fontFamily: fonts.bodyExtra,
    color: colors.mint,
  },
  quizWordCard: {
    backgroundColor: colors.card,
    borderRadius: radius.cardLarge,
    borderWidth: 1,
    borderColor: 'rgba(255,229,102,0.25)',
    paddingVertical: 24,
    alignItems: 'center',
    marginVertical: 16,
  },
  quizWord: {
    fontFamily: fonts.display,
    fontSize: 30,
    color: colors.yellow,
    letterSpacing: 0.5,
  },
  quizOption: {
    borderRadius: radius.card,
    borderWidth: 1,
    padding: 13,
    marginBottom: 8,
  },
  quizOptionText: {
    fontFamily: fonts.serif,
    fontSize: 13,
    color: colors.text,
    lineHeight: 18,
  },
  welcomeTitle: {
    fontFamily: fonts.display,
    fontSize: 28,
    color: colors.text,
    marginTop: 16,
  },
  levelPill: {
    fontFamily: fonts.bodyExtra,
    fontSize: 11,
    color: colors.yellow,
    backgroundColor: 'rgba(255,229,102,0.12)',
    borderRadius: radius.pill,
    paddingHorizontal: 12,
    paddingVertical: 5,
    marginTop: 10,
    overflow: 'hidden',
  },
});
