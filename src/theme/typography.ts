import { TextStyle } from 'react-native';

export const fonts = {
  display: 'SpaceGrotesk-Bold',
  displayMedium: 'SpaceGrotesk-Medium',
  displayRegular: 'SpaceGrotesk-Regular',
  body: 'Nunito-Regular',
  bodySemi: 'Nunito-SemiBold',
  bodyBold: 'Nunito-Bold',
  bodyExtra: 'Nunito-ExtraBold',
  bodyBlack: 'Nunito-Black',
  serif: 'Lora-Regular',
  serifItalic: 'Lora-Italic',
} as const;

export const typography = {
  display: { fontFamily: fonts.display } as TextStyle,
  ui: { fontFamily: fonts.body } as TextStyle,
  uiBold: { fontFamily: fonts.bodyBold } as TextStyle,
  passage: { fontFamily: fonts.serifItalic, fontStyle: 'italic' } as TextStyle,
};
