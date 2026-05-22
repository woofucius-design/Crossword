import {
  Nunito_400Regular,
  Nunito_600SemiBold,
  Nunito_700Bold,
  Nunito_800ExtraBold,
  Nunito_900Black,
} from '@expo-google-fonts/nunito';
import {
  SpaceGrotesk_400Regular,
  SpaceGrotesk_500Medium,
  SpaceGrotesk_600SemiBold,
  SpaceGrotesk_700Bold,
} from '@expo-google-fonts/space-grotesk';
import {
  Lora_400Regular,
  Lora_600SemiBold,
  Lora_400Regular_Italic,
  Lora_600SemiBold_Italic,
} from '@expo-google-fonts/lora';

/**
 * Font map passed to expo-font's useFonts. Keys match the family names
 * referenced in src/theme/typography.ts.
 */
export const fontAssets = {
  'Nunito-Regular': Nunito_400Regular,
  'Nunito-SemiBold': Nunito_600SemiBold,
  'Nunito-Bold': Nunito_700Bold,
  'Nunito-ExtraBold': Nunito_800ExtraBold,
  'Nunito-Black': Nunito_900Black,
  'SpaceGrotesk-Regular': SpaceGrotesk_400Regular,
  'SpaceGrotesk-Medium': SpaceGrotesk_500Medium,
  'SpaceGrotesk-SemiBold': SpaceGrotesk_600SemiBold,
  'SpaceGrotesk-Bold': SpaceGrotesk_700Bold,
  'Lora-Regular': Lora_400Regular,
  'Lora-SemiBold': Lora_600SemiBold,
  'Lora-Italic': Lora_400Regular_Italic,
  'Lora-SemiBoldItalic': Lora_600SemiBold_Italic,
};
