/**
 * Pre-baked passages used by the Story tab when the generate-passage edge
 * function is unavailable. Vocabulary words appear in ALL CAPS so the renderer
 * can highlight them.
 */
export interface FallbackPassage {
  words: string[];
  text: string;
}

export const fallbackPassages: FallbackPassage[] = [
  {
    words: ['LUCID', 'VERBOSE', 'TERSE'],
    text: 'My professor delivered a remarkably LUCID lecture, then ruined it with a VERBOSE three-hour appendix nobody requested. The teaching assistant, by contrast, was so TERSE that her entire summary fit on a sticky note.',
  },
  {
    words: ['OPULENT', 'STOIC', 'CANDOR'],
    text: 'The OPULENT mansion had golden faucets and a moat of sparkling cider, yet its owner remained utterly STOIC about the leaking roof. With surprising CANDOR, he admitted he had simply forgotten where he left the bucket.',
  },
  {
    words: ['ASTUTE', 'OBSTINATE', 'PRUDENT'],
    text: 'The ASTUTE detective noticed the cat had an alibi, but the OBSTINATE chief refused to release it from custody. A PRUDENT lawyer eventually negotiated the feline’s freedom in exchange for two cans of tuna.',
  },
  {
    words: ['EPHEMERAL', 'ELOQUENT', 'GREGARIOUS'],
    text: 'The mayfly gave an EPHEMERAL yet surprisingly ELOQUENT speech about seizing the day. Being deeply GREGARIOUS, it invited the entire pond, though the party regrettably ended before the cake arrived.',
  },
  {
    words: ['MERCURIAL', 'PLACID', 'BENEVOLENT'],
    text: 'Our MERCURIAL weather forecaster promised a PLACID afternoon, then sprinted indoors as hail the size of marbles fell. A BENEVOLENT neighbor handed out umbrellas and pretended not to notice his terrible prediction.',
  },
  {
    words: ['AUSTERE', 'CACOPHONY', 'DILIGENT'],
    text: 'The AUSTERE music hall was meant for quiet study, so the sudden CACOPHONY of forty kazoos was unwelcome. One DILIGENT student kept taking notes, convinced it was an avant-garde exam.',
  },
  {
    words: ['FRUGAL', 'ZEALOUS', 'LUCID'],
    text: 'My FRUGAL uncle reuses tea bags up to nine times and is ZEALOUS about saving every receipt. In a rare LUCID moment, he admitted the receipts had quietly taken over the entire garage.',
  },
  {
    words: ['STOIC', 'VERBOSE', 'ASTUTE'],
    text: 'The STOIC chess champion never flinched, even when her opponent gave a VERBOSE monologue about each move. An ASTUTE observer noticed she had already won three turns ago.',
  },
];

export function pickFallbackPassage(targetWords: string[]): FallbackPassage {
  const wanted = new Set(targetWords.map((w) => w.toUpperCase()));
  let best = fallbackPassages[0];
  let bestScore = -1;
  for (const p of fallbackPassages) {
    const score = p.words.filter((w) => wanted.has(w)).length;
    if (score > bestScore) {
      best = p;
      bestScore = score;
    }
  }
  return best;
}
