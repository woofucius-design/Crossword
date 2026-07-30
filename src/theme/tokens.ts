export const colors = {
  bg: '#0D1B2A',
  surface: '#132236',
  card: '#16293D',
  border: 'rgba(255,255,255,0.07)',

  text: '#FFFFFF',
  textMuted: 'rgba(255,255,255,0.45)',
  textDim: 'rgba(255,255,255,0.22)',

  yellow: '#FFE566',
  yellowDark: '#F5A623',
  orange: '#FF6B35',
  mint: '#34D399',
  red: '#EF4444',
  redLight: '#FCA5A5',

  masteryNew: '#60A5FA',
  masteryLearning: '#F97316',
  masteryFamiliar: '#EAB308',
  masteryStrong: '#22C55E',
  masteryMastered: '#A855F7',
  masteryMasteredLight: '#D8B4FE',

  cellBg: '#F8F5EE',
  cellSelected: '#FFD84C',
  cellSelectedBorder: '#E8A800',
  cellWordHighlight: '#C9E8FF',
  cellWordHighlightBorder: '#8DC8E8',
  cellBlack: '#1a1a1a',
  cellBorder: '#BBBBBB',
  cellNumberText: '#777',
  cellLetterText: '#111',
} as const;

/**
 * The layout is phone-first. On an iPad or a desktop browser, letting it
 * stretch to full width blows the crossword cells up to ~98pt and strands
 * text across the screen, so content is capped and centred while the
 * background art still fills the window.
 */
export const maxContentWidth = 520;

export const spacing = {
  screen: 14,
  cardGap: 8,
  sectionGap: 12,
} as const;

export const radius = {
  cell: 2,
  pill: 6,
  button: 13,
  card: 14,
  cardLarge: 20,
  modal: 20,
} as const;

export const shadows = {
  card: {
    shadowColor: '#000',
    shadowOpacity: 0.25,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 4 },
    elevation: 4,
  },
  toast: {
    shadowColor: '#000',
    shadowOpacity: 0.4,
    shadowRadius: 32,
    shadowOffset: { width: 0, height: 8 },
    elevation: 8,
  },
  gold: {
    shadowColor: '#F5A623',
    shadowOpacity: 0.35,
    shadowRadius: 20,
    shadowOffset: { width: 0, height: 4 },
    elevation: 6,
  },
} as const;

import type { MasteryTier } from '@/types/models';

export const masteryColor: Record<MasteryTier, string> = {
  new: colors.masteryNew,
  learning: colors.masteryLearning,
  familiar: colors.masteryFamiliar,
  strong: colors.masteryStrong,
  mastered: colors.masteryMastered,
};
