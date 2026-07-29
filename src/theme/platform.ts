import { Platform, type PressableAndroidRippleConfig } from 'react-native';
import { colors } from './tokens';

/**
 * Android-only touch affordances. iOS gets `undefined`, which leaves the
 * existing opacity/scale press styles as the only feedback — the platform
 * convention there. On Android a ripple is expected, and its absence reads
 * as an unresponsive control.
 */
export function ripple(
  color: string = 'rgba(255,229,102,0.24)',
  borderless = false,
): PressableAndroidRippleConfig | undefined {
  return Platform.OS === 'android' ? { color, borderless, foreground: true } : undefined;
}

export const rippleLight = () => ripple('rgba(255,255,255,0.14)');
export const rippleGold = () => ripple('rgba(255,229,102,0.30)');

/**
 * Android renders an extra ascender/descender pad inside Text, so a tight
 * `lineHeight` shifts or clips the glyph relative to iOS. Spread this into
 * any style where the line height is close to the font size.
 */
export const tightText = Platform.select({
  android: { includeFontPadding: false },
  default: {},
}) as { includeFontPadding?: boolean };

/**
 * `elevation` ignores `shadowColor` below API 28, so the app's coloured
 * glows (gold, purple) degrade to a grey drop shadow. Where the glow is
 * the point, fall back to a translucent border of the same hue.
 */
export function glowFallback(color: string) {
  return Platform.OS === 'android'
    ? { borderWidth: 1, borderColor: color }
    : {};
}

export const isAndroid = Platform.OS === 'android';
export { colors };
