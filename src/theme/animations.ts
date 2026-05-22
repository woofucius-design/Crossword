import { Easing } from 'react-native-reanimated';

// cubic-bezier(0.22, 1, 0.36, 1) — the spring-like "swift" curve used throughout the design.
export const easing = {
  swift: Easing.bezier(0.22, 1, 0.36, 1),
  flip: Easing.bezier(0.4, 0, 0.2, 1),
  outCubic: Easing.out(Easing.cubic),
  inOut: Easing.inOut(Easing.ease),
} as const;

export const durations = {
  letterPop: 280,
  wordRipplePerCell: 50,
  wordRippleFlash: 500,
  toastIn: 450,
  toastDismiss: 2600,
  screenTransition: 260,
  cardEnter: 400,
  cardFlip: 400,
  ringFill: 900,
} as const;
