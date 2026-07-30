import * as Haptics from 'expo-haptics';
import { Platform } from 'react-native';

/**
 * Haptic vocabulary for the game. Wrapped rather than called directly so
 * the intent lives at the call site ("a word landed") instead of a raw
 * impact style, and so failures stay silent — haptics are unavailable on
 * web, on Android devices without a vibrator, and when the user has
 * disabled system haptics. None of that should ever break a key press.
 */

const fire = (run: () => Promise<void>) => {
  if (Platform.OS === 'web') return;
  void run().catch(() => {});
};

/** A letter went into the grid. Deliberately the lightest tap there is:
 *  it fires on every keystroke, so anything heavier becomes fatiguing. */
export const tapKey = () =>
  fire(() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light));

/** Backspace — distinct from a letter so deleting feels different. */
export const tapDelete = () =>
  fire(() => Haptics.selectionAsync());

/** A word was completed correctly. */
export const wordSolved = () =>
  fire(() => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success));

/** A SAT word was collected — the payoff moment, so the heaviest cue. */
export const vocabCollected = () =>
  fire(() => Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy));

/** Quiz/flashcard answer feedback. */
export const answerCorrect = () =>
  fire(() => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success));

export const answerWrong = () =>
  fire(() => Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning));

/** Card flip / tab switch — a positional change, not a success. */
export const select = () => fire(() => Haptics.selectionAsync());
