import { useEffect } from 'react';
import { BackHandler, Platform } from 'react-native';

/**
 * Run `handler` when Android's hardware/gesture back is pressed.
 *
 * Return `true` to say "I handled it" and stop the event; return `false`
 * to let it fall through to the default (pop the route, or exit the app
 * at the root). iOS has no hardware back, so this is a no-op there.
 *
 * Listeners registered later win, which means a screen and an overlay it
 * owns can each register one and the overlay — mounted last — gets first
 * refusal.
 */
export function useAndroidBack(handler: () => boolean, enabled = true) {
  useEffect(() => {
    if (Platform.OS !== 'android' || !enabled) return;
    const sub = BackHandler.addEventListener('hardwareBackPress', handler);
    return () => sub.remove();
  }, [handler, enabled]);
}
