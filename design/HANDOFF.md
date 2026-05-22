# Handoff: LEXICON — SAT Vocabulary Crossword App

> Implementation handoff for Claude Code. This package contains design references and a complete implementation plan for shipping LEXICON to the App Store and Google Play.

---

## What This Package Is

LEXICON is a mobile-first vocabulary learning game for high school students (14–18) preparing for the SAT. Core loop:

1. **Play a daily crossword puzzle** where featured answers are SAT vocabulary words
2. **Collect those words** automatically upon solving — like a Pokédex
3. **Review collected words** via AI-generated absurd passages, flashcards, and quizzes
4. **Write your own passage** using your vocabulary and get AI-graded scores

The differentiator is the **collection mechanic**: words are trophies, not flashcards. A class leaderboard lets teachers run word-collection competitions.

### Files in this bundle

```
design_handoff_lexicon_app/
├── README.md                        ← This document
└── screens/
    ├── Onboarding.html              ← 6-step onboarding flow
    ├── Home Screen.html             ← Daily hub
    ├── Crossword Puzzle.html        ← 10×10 interactive crossword
    ├── Word Collection.html         ← Pokédex-style word library
    ├── Review Mode.html             ← Story / Flashcard / Quiz tabs
    ├── Passage Writing.html         ← AI-graded writing + leaderboard
    └── Linked Prototype.html        ← All 6 screens wired together with shared state
```

### About the design files

The HTML files in `screens/` are **high-fidelity design references**, not production code. They are React-in-a-browser prototypes that show exact intended look, feel, and behavior down to the pixel. Open any file in a browser to see the live interactive prototype.

**The task is to recreate these designs as a real mobile app in React Native**, using the codebase patterns described below. Do not ship the HTML.

### Fidelity

**High-fidelity (hifi).** Pixel-accurate mockups with:
- Final color palette (dark navy theme, gold accents)
- Final typography (Nunito + Space Grotesk + Lora)
- Final spacing and layout
- Working interactions and animations
- Real data structures and game logic

Recreate them as closely as possible. Where the HTML uses CSS that doesn't translate cleanly to React Native (e.g. `background: linear-gradient(...)`), use the equivalent RN library (`expo-linear-gradient`) — described per-screen below.

---

## Recommended Stack

If starting fresh, use:

| Layer | Choice | Why |
|---|---|---|
| **App framework** | **Expo (React Native)** | Hifi React prototypes translate directly; one codebase for iOS + Android; managed workflow handles 90% of native config |
| **Language** | **TypeScript** | Strict mode; the data shapes are well-defined (see Data Models below) |
| **Navigation** | **expo-router** (file-based) | Cleaner than React Navigation for this app's flat structure |
| **Styling** | **StyleSheet** + design tokens module | No CSS-in-JS library needed; the token system is small and well-defined |
| **Animations** | **react-native-reanimated v3** | Letter pop, word ripple, toast slide all need 60fps native-thread animation |
| **Gradients** | **expo-linear-gradient** | Used throughout (buttons, cards, backgrounds) |
| **Fonts** | **expo-font** | Load Nunito, Space Grotesk, Lora at startup |
| **Storage (local)** | **expo-secure-store** (auth tokens) + **AsyncStorage** (preferences) | Word collection lives on server; only cache and auth on device |
| **Server** | **Supabase** | Postgres + Auth + Row-Level Security + Realtime for leaderboards. Free tier covers MVP. |
| **AI proxy** | **Supabase Edge Functions** | Never put `ANTHROPIC_API_KEY` in the app binary. Proxy through an edge function. |
| **AI model** | **claude-haiku-4-5** | Fast and cheap; passage gen + grading don't need a bigger model |
| **Puzzle hosting** | **Supabase Storage** (or S3 + CloudFront) | Pre-generated JSON puzzles served as static files |
| **Puzzle generation** | **Python pipeline run via GitHub Actions** | Nightly cron, see Puzzle Pipeline below |

If the user is already invested in a different stack (Flutter, native Swift/Kotlin), the design tokens, screen specs, and data models below all still apply — just translate the component-level guidance.

---

## Project Structure

```
lexicon/
├── app/                          # expo-router screens
│   ├── (auth)/
│   │   └── onboarding.tsx        # 6-step flow
│   ├── (tabs)/
│   │   ├── _layout.tsx           # Bottom nav
│   │   ├── home.tsx
│   │   ├── puzzles.tsx           # Archive (future)
│   │   ├── collection.tsx
│   │   ├── review.tsx
│   │   └── write.tsx
│   ├── puzzle/[date].tsx         # Crossword game (full-screen, not in tabs)
│   ├── word/[id].tsx             # Word detail modal
│   └── _layout.tsx               # Root, font loading, auth gate
├── src/
│   ├── components/               # Reusable UI primitives
│   │   ├── Button.tsx
│   │   ├── WordChip.tsx
│   │   ├── RetentionArc.tsx
│   │   ├── StatusBar.tsx
│   │   ├── crossword/
│   │   │   ├── Grid.tsx
│   │   │   ├── Cell.tsx
│   │   │   ├── Keyboard.tsx
│   │   │   ├── ClueBar.tsx
│   │   │   └── CollectionToast.tsx
│   │   └── backgrounds/
│   │       ├── MeshBg.tsx
│   │       └── FloatingWords.tsx
│   ├── theme/
│   │   ├── tokens.ts             # Colors, spacing, radii, shadows
│   │   ├── typography.ts         # Font definitions
│   │   └── animations.ts         # Easing curves, durations
│   ├── data/
│   │   ├── puzzles.ts            # Fetch + cache today's puzzle
│   │   ├── collection.ts         # User word collection (Supabase queries)
│   │   ├── retention.ts          # Forgetting-curve algorithm
│   │   └── ai.ts                 # Claude proxy client
│   ├── stores/                   # zustand or Jotai for global state
│   │   ├── user.ts
│   │   └── session.ts
│   └── types/
│       └── models.ts             # TypeScript types — see Data Models below
├── supabase/
│   ├── migrations/               # SQL schema
│   └── functions/                # Edge Functions
│       ├── generate-passage/     # Claude proxy for Story tab
│       └── grade-passage/        # Claude proxy for Passage Writing
├── puzzle-pipeline/              # Python — runs in CI, not in app
│   ├── word_selector.py
│   ├── grid_builder.py
│   ├── clue_writer.py
│   ├── data/
│   │   ├── sat_words.json        # 1500 SAT vocab words
│   │   ├── clean_fill.json       # 600 fillers
│   │   └── edu_proper.json       # 200 proper nouns
│   └── output/                   # puzzles/YYYY-MM-DD.json
└── .github/workflows/
    └── generate-puzzle.yml       # Nightly cron at 00:00 UTC
```

---

## Design Tokens

Put these in `src/theme/tokens.ts`. Every color, spacing value, and radius in the HTML prototypes is one of these tokens.

### Colors

```typescript
export const colors = {
  bg: '#0D1B2A',            // app background, deep navy
  surface: '#132236',       // card backgrounds (one tier up)
  card: '#16293D',          // elevated cards (two tiers up)
  border: 'rgba(255,255,255,0.07)',

  text: '#FFFFFF',
  textMuted: 'rgba(255,255,255,0.45)',
  textDim: 'rgba(255,255,255,0.22)',

  yellow: '#FFE566',        // primary CTA, SAT highlights
  yellowDark: '#F5A623',    // CTA gradient end
  orange: '#FF6B35',        // streak, urgency
  mint: '#34D399',          // correct, mastered, progress
  red: '#EF4444',           // errors, slipping words
  redLight: '#FCA5A5',

  // Mastery tier colors
  masteryNew: '#60A5FA',
  masteryLearning: '#F97316',
  masteryFamiliar: '#EAB308',
  masteryStrong: '#22C55E',
  masteryMastered: '#A855F7',
  masteryMasteredLight: '#D8B4FE',

  // Crossword cells
  cellBg: '#F8F5EE',          // empty white cell
  cellSelected: '#FFD84C',
  cellWordHighlight: '#C9E8FF',
  cellBlack: '#1a1a1a',
  cellBorder: '#BBBBBB',
  cellNumberText: '#777',
  cellLetterText: '#111',
};
```

### Typography

Load all three font families at startup with `expo-font`:

```typescript
export const fonts = {
  display: 'SpaceGrotesk-Bold',     // word titles, big numbers
  body: 'Nunito',                   // UI labels, body
  serif: 'Lora',                    // definitions, passages
};

export const typography = {
  display: { fontFamily: fonts.display, fontWeight: '700' as const },
  ui: { fontFamily: fonts.body },
  passage: { fontFamily: fonts.serif, fontStyle: 'italic' as const },
};
```

Weights to load:
- **Nunito**: 400, 600, 700, 800, 900
- **Space Grotesk**: 400, 500, 600, 700
- **Lora**: 400 (regular), 400 italic, 600 italic

### Spacing & Radius

```typescript
export const spacing = {
  screen: 14,        // horizontal screen padding
  cardGap: 8,
  sectionGap: 12,
};

export const radius = {
  cell: 2,           // crossword cells (intentionally tight)
  pill: 6,           // small chips
  button: 13,
  card: 14,
  cardLarge: 20,
  modal: 20,
};

export const shadows = {
  card:    { shadowColor: '#000', shadowOpacity: 0.25, shadowRadius: 20, shadowOffset: { width: 0, height: 4 }, elevation: 4 },
  toast:   { shadowColor: '#000', shadowOpacity: 0.40, shadowRadius: 32, shadowOffset: { width: 0, height: 8 }, elevation: 8 },
  gold:    { shadowColor: '#F5A623', shadowOpacity: 0.35, shadowRadius: 20, shadowOffset: { width: 0, height: 4 }, elevation: 6 },
};
```

### Animations

```typescript
export const easing = {
  swift: 'cubic-bezier(0.22, 1, 0.36, 1)',  // most spring-like motion
};

export const durations = {
  letterPop: 280,
  wordRipplePerCell: 50,
  wordRippleFlash: 500,
  toastIn: 450,
  toastDismiss: 2600,
  screenTransition: 260,
  cardEnter: 400,
};
```

---

## Data Models

```typescript
// src/types/models.ts

export type MasteryTier = 'new' | 'learning' | 'familiar' | 'strong' | 'mastered';

export interface SATWord {
  id: number;
  word: string;          // ALL CAPS
  definition: string;
  partOfSpeech: 'noun' | 'verb' | 'adjective' | 'adverb';
}

export interface CollectedWord {
  id: string;            // uuid
  userId: string;
  wordId: number;
  word: string;
  definition: string;
  mastery: MasteryTier;
  retention: number;     // 0-100
  reviewCount: number;
  collectedAt: string;   // ISO timestamp
  lastReviewAt: string | null;
  puzzleDate: string;    // YYYY-MM-DD of the puzzle that introduced it
}

export interface Puzzle {
  date: string;          // YYYY-MM-DD
  number: number;        // sequential, "Daily Mini #48"
  size: { rows: number; cols: number };  // 10x10 standard
  solution: string[][];  // 2D grid, '#' = black square
  cells: Record<string, { number?: number; preFilled?: string }>;  // "r,c" → metadata
  words: PuzzleWord[];
}

export interface PuzzleWord {
  id: string;            // "1A", "2D", etc
  number: number;
  direction: 'across' | 'down';
  row: number;
  col: number;
  length: number;
  answer: string;        // the word in ALL CAPS
  clue: string;
  isSATVocab: boolean;
  definition?: string;   // only present when isSATVocab=true
}

export interface UserProfile {
  id: string;
  username: string;
  avatar: 'owl' | 'fox' | 'lion' | 'shark' | 'wolf' | 'eagle';
  goal: '1200+' | '1400+' | '1500+' | '1600';
  testDate: '1month' | '3months' | '6months' | '1year' | 'unsure';
  level: 'Beginner' | 'Developing' | 'Intermediate' | 'Advanced';
  streak: number;
  classId?: string;
  createdAt: string;
}

export interface PassageSubmission {
  id: string;
  userId: string;
  classId?: string;
  targetWords: string[];
  passage: string;
  scores: {
    accuracy: number;
    conciseness: number;
    creativity: number;
    overall: number;
  };
  wordFeedback: Array<{
    word: string;
    used: boolean;
    correct: boolean;
    note: string;
  }>;
  feedback: string;
  submittedAt: string;
}
```

---

## Screens / Views

Each screen below maps to one HTML file in `screens/`. **Open the corresponding HTML file in a browser before implementing — the prototype is the source of truth for visual details.** This section documents structure, behavior, and React Native-specific implementation notes.

All screens are designed at **402×874 px** (iPhone 14 Pro form factor). Extract the inner `App` content from each HTML file — not the outer device frame wrapper, that's just for preview.

---

### 1. Onboarding Flow
**Reference:** `screens/Onboarding.html`
**Route:** `app/(auth)/onboarding.tsx`
**Purpose:** First-time setup. Gets the player into the game in under 30 seconds.

6 steps in sequence, each transitions with fade-out (opacity 0, translateY +8px, 260ms) then fade-in. Progress dots (steps 2–4) at top.

| # | Step | Key elements |
|---|---|---|
| 0 | **Splash** | LEXICON logo with white→gold gradient text; tagline "Collect words. Beat the SAT."; 5 word chips that fly in with `cardFlyIn` from staggered origins; gold CTA "Start Collecting →" |
| 1 | **Collection Hook** | 5 word cards animate in one at a time with `starBurst` effect (scale + rotate). Each card has colored border matching mastery tier. Auto-advances. |
| 2 | **Profile Setup** | 6 emoji avatars (🦉🦊🦁🦈🐺🦅) in a row, selected one shown 80×80 above. Username text input, transparent bg, Space Grotesk 24px centered. CTA personalizes once typed. |
| 3 | **SAT Goal** | 2×2 grid of score targets (1200+ / 1400+ / 1500+ / 1600), each colored. 5 test-date chips. Dynamic insight: "For 1400+ in 3 months, aim for 4 new words/day". |
| 4 | **Level Check** | 5 multiple-choice vocab questions, one at a time. Correct: green highlight. Wrong: red highlight + `wrongShake`. Auto-advances 900ms after pick. Final screen shows tier (Beginner/Developing/Intermediate/Advanced). |
| 5 | **Welcome** | Avatar 90×90 with glow; "Ready, {name}!"; starter pack of 5 word chips count up; CTA "Play First Puzzle". |

**On complete:** persist `UserProfile` to Supabase, route to `/home`. Insert the 5 starter pack words into `collected_words` table.

**React Native notes:**
- Use `Animated.View` + Reanimated `useSharedValue` for the per-step intro animations
- The floating background words (low-opacity vocabulary drifting up) should fade out on steps 2+ (`opacity: step <= 1 ? 1 : 0.3`)
- TextInput: `caretHidden={false}`, set `selectionColor={colors.yellow}` to match the gold caret

---

### 2. Home Screen
**Reference:** `screens/Home Screen.html`
**Route:** `app/(tabs)/home.tsx`
**Purpose:** Daily hub. Entry point to all features.

**Layout (top to bottom):**
1. Status bar + Dynamic Island spacer
2. Logo row: "LEXICON" gradient text + date subtitle; right: avatar 38×38 with notification dot
3. **Stats row** — 4 equal tiles: 🔥 Streak / 📚 Collected / ⬟ Mastered / 🏆 Class Rank
4. **Daily puzzle card** — gradient bg, "Daily Mini #N" with NEW badge, mini grid preview (25 dots in 5×5), featured word chips, gold play button with `glowRing` animation
5. **AI notice banner** (conditional) — red-tinted, lists 2–3 slipping words with "Review →" button → routes to `/review`
6. **Quick actions grid** — 2×2: Collection / Review / Write / Rankings
7. **Class challenge banner** (conditional) — indigo gradient, teacher name, pulsing LIVE badge, Join button → routes to `/write`
8. **Activity ticker** — pulsing mint dot + "Your class just collected [WORD]" — word cycles every 2.2s
9. **Bottom nav** (built into `(tabs)/_layout.tsx`)

**Background:** Radial gradient mesh — indigo blob top-left, mint blob bottom-right, gold blob center. Plus 28 floating SAT words at 5–10% opacity drifting up with staggered delays.

**React Native notes:**
- `MeshBg` and `FloatingWords` are reusable in `src/components/backgrounds/` — also used by Onboarding
- For the gradient text on "LEXICON", use `MaskedView` from `@react-native-masked-view/masked-view` + `LinearGradient`
- Avatar notification badge: position absolutely, `border: 2px solid bg` to create the inset effect
- The ticker words array can live in component state, swapped on `setInterval`

---

### 3. Crossword Puzzle Screen
**Reference:** `screens/Crossword Puzzle.html`
**Route:** `app/puzzle/[date].tsx` (full-screen, hides tab bar)
**Purpose:** The main game.

**Layout:**
1. Status bar + back arrow / "Daily Mini #N" + date / 🔥 streak chip / timer
2. **Progress bar** — 3px, green gradient, fills as words completed
3. **10×10 Grid** — 33px cells, 2px gap, 5px padding, rounded-10 container
4. **Clue bar** — active word number badge (gold for SAT vocab) + clue text + direction toggle
5. **Compact clue list** — two columns (Across / Down), tappable rows
6. **Keyboard** — 3 rows, 38px keys, custom render (do NOT use system keyboard)

**Grid cell states:**
- Black: `#1a1a1a`
- Empty: `#F8F5EE` bg, `#BBBBBB` border
- Word-highlighted: `#C9E8FF` bg, `#8DC8E8` border
- Selected: `#FFD84C` bg, `#E8A800` border
- Number: top-left, 7px Space Grotesk 700
- Letter: center, 14px Space Grotesk 700

**Animations:**
- **letterPop** on keystroke — scale 0.4→1.18→0.96→1, 280ms, `cubic-bezier(0.22,1,0.36,1)`
- **wordRipple** on word complete — background color flash left-to-right, 50ms stagger per cell. Green for filler words, gold for SAT vocab.
- **toastPop** — collection toast slides up from bottom

**Collection toast (auto-triggered):**
- Appears 350ms after a SAT vocab word completes
- Word is auto-collected — no button press needed
- Shows "⭐ Added to Collection!" + word + definition
- 7 stars float up from center with staggered delays
- Auto-dismiss after 2.6s with draining progress bar
- Tap × to dismiss early

**State management:**
```typescript
{
  grid: Record<string, string>,        // "r,c" → letter, pre-filled at load
  selected: { row: number, col: number },
  direction: 'across' | 'down',
  completedWords: Set<string>,         // word IDs ("1A", "2D")
  collectedWords: Set<string>,         // for the current puzzle
  toastWord: PuzzleWord | null,
  timerSeconds: number,
}
```

On every keystroke, check all 13 words for completion. If a SAT vocab word completes and hasn't been collected yet:
1. Add to `completedWords`
2. Add to `collectedWords`
3. After 350ms, show `CollectionToast`
4. Insert into Supabase `collected_words` table with `mastery: 'new'`, `retention: 100`, `reviewCount: 0`

**Sample puzzle (this one):** SAT words LUCID, CANDOR, OPULENT, STOIC, VERBOSE, TERSE. See `Crossword Puzzle.html` for the full grid layout and clue data.

**React Native notes:**
- Render the keyboard as a `View` with `Pressable` keys — never trigger the system keyboard
- For physical-keyboard support (iPad with keyboard, web), wrap the screen in a `View` with `onKeyPress` listener using `react-native-keyevent` (mobile) or DOM listeners (web)
- The grid is a `View` with `flexDirection: 'row'` and `flexWrap` — or `FlatList numColumns={10}` for very large grids (overkill for 10×10)
- Use Reanimated's `useAnimatedStyle` for the letter pop — it's per-cell so don't drive every cell with the same `Animated.Value`
- Disable the home indicator gesture during the toast animation to avoid accidental dismissal

---

### 4. Word Collection Screen
**Reference:** `screens/Word Collection.html`
**Route:** `app/(tabs)/collection.tsx`
**Purpose:** The "Pokédex" — library of all collected words with retention tracking.

**Layout:**
1. Header: "My Collection" + settings gear
2. **Stats strip** — 3-column: big hero tile (gold number "X Words Collected") / 2 stacked tiles (Mastered, Due Today) / Streak tile
3. **Class rank banner** — "#3 in English Honors", nudge to reach #2
4. **Just Collected row** — horizontal scroll of new word cards with "NEW" badge
5. **AI Focus Queue** — horizontal scroll of priority cards, each with reason badge (⚠ About to forget / ↘ Slipping fast / ⏰ Long overdue), word, definition, retention arc, "Review" button
6. **Tab bar** — All / Review / Mastered, counts as pills
7. **2-column word grid** — each card has tier-colored left accent, tier badge, word, definition, retention bar

**Word card visual states:**
- Mastered: purple tint + `shimmer` overlay animation
- New: gold border + "NEW" badge
- Slipping (retention < 70%): red-tinted border, word color `#FCA5A5`, pulsing retention %

**Word detail modal** (bottom sheet):
- Tap any card → slides up
- Shows: word large, mastery badge, full definition, AI insight, stats (collected date, review count, last seen), "Practice Now" + share buttons

**Retention algorithm** (used for the Focus Queue sort order):
```typescript
function urgencyScore(w: CollectedWord): number {
  const retDecay = (100 - w.retention) * 1.5;
  const dayPenalty = daysSince(w.lastReviewAt) * 8;
  const tierBonus = { learning: 10, familiar: 20, strong: 5, mastered: -10, new: 0 }[w.mastery];
  return retDecay + dayPenalty + tierBonus;
}

function focusReason(w: CollectedWord) {
  if (w.retention < 45) return { label: 'About to forget', color: colors.red };
  if (w.retention < 60) return { label: 'Slipping fast', color: '#F97316' };
  if (daysSince(w.lastReviewAt) >= 5) return { label: 'Long overdue', color: '#EAB308' };
  if (w.mastery === 'learning' && daysSince(w.lastReviewAt) >= 2)
    return { label: 'Reinforce now', color: '#60A5FA' };
  return { label: 'Good time to review', color: colors.mint };
}
```

**React Native notes:**
- Bottom sheet: use `@gorhom/bottom-sheet` library, snap points `['80%']`
- The horizontal scrolls (Just Collected, Focus Queue) are `ScrollView horizontal showsHorizontalScrollIndicator={false}`
- Retention arc is an SVG circle with `strokeDasharray` — use `react-native-svg`
- Shimmer animation on mastered cards: Reanimated `useSharedValue` driving a `LinearGradient` position

---

### 5. Review Mode Screen
**Reference:** `screens/Review Mode.html`
**Route:** `app/(tabs)/review.tsx`
**Purpose:** Three-mode review session.

**Layout:**
1. Header: "Review Session" / "8 words · AI-selected" / streak chip
2. **AI context banner** — red-tinted, lists 2 most urgent words
3. **Tab selector** — ✨ Story / ⟳ Cards / ◉ Quiz
4. Tab content area (scrollable)

#### Story Tab (hero feature)
- Robot icon, "AI Context Story" title, word count badge
- **Absurdity selector** — 3 pills: 😐 Mild / 😄 Absurd / 🤪 Unhinged
- **Passage card** — dark bg, large decorative quote mark, passage text with vocab words in gold italic Lora serif. Tapping a highlighted word opens a definition popover (bottom sheet)
- **"✨ Generate New Story"** button — calls Claude via Supabase Edge Function

**Claude prompt (in `supabase/functions/generate-passage/index.ts`):**
```
You are a vocabulary teacher creating memorable study passages for SAT students.

Generate a single short paragraph (2-4 sentences, max 80 words) that:
1. Uses as many of these words as possible IN CONTEXT: {words}
2. Uses each word grammatically correctly with its real meaning
3. {absurdityInstruction}
4. Is a single coherent (if ridiculous) story or scenario

Absurdity levels:
- low: "slightly quirky but mostly realistic"
- medium: "entertainingly absurd — ridiculous scenarios are fine as long as words are used correctly"
- high: "maximally unhinged and bizarre"

Return ONLY the paragraph. No title, no explanation, no quotes around it. Use the words in ALL CAPS exactly as provided.
```

**Fallback:** if the edge function errors, use a pre-baked passage. Ship 8–10 fallback passages in app.

#### Flashcard Tab
- Progress bar (one segment per card)
- Large flip card — front: word in gold; back: italic definition in Lora
- Tap to flip (rotateY 180deg, 400ms; use Reanimated `withTiming`)
- After flip, "😕 Still Learning" / "✓ Got it!" buttons appear
- Results screen after all cards: percentage, retry button

#### Quiz Tab
- 4 multiple-choice questions
- Word shown large in gold, 4 options with A/B/C/D prefix
- Green/red feedback, auto-advance after 1000ms
- Final score screen with percentage emoji

**React Native notes:**
- Flip card: two `Animated.View`s with `backfaceVisibility: 'hidden'` stacked on top of each other; rotate one to 180deg, the other to 0deg, transition together
- The highlighted-word render in Story tab: split the passage on whitespace, render each token as either `Text` or `Pressable<Text>` based on whether it matches a vocab word

---

### 6. Passage Writing Screen
**Reference:** `screens/Passage Writing.html`
**Route:** `app/(tabs)/write.tsx`
**Purpose:** Students write a passage; AI grades it.

**Layout:**
1. Header with teacher name + "Class Competition" badge
2. Instruction card explaining scoring criteria
3. **Target words row** — 5 word chips, turn green with ✓ as player types each word
4. **Writing textarea** — dark bg, Lora serif 16px, gold caret, decorative quote mark, word count + live hints
5. **Example hint** — faded example passage, tap to fill
6. **Score preview chips** — Accuracy / Conciseness / Creativity estimates (update live)
7. **Submit button** — locked until ≥1 word used + ≥20 chars, then activates with `glowPulse`

**Grading phase (4-step progress animation, ~4 seconds):**
1. Checking word accuracy…
2. Measuring conciseness…
3. Evaluating creativity…
4. Compiling your score…

**Results phase:**
- Grade emoji + overall score (large)
- 3 animated score rings: Accuracy (blue) / Conciseness (green) / Creativity (amber). Count up from 0 with cubic ease-out, staggered delays
- AI feedback paragraph (specific to the passage)
- Word-by-word breakdown: ✅ used correctly / ⚠️ used incorrectly / ○ not used
- Class rank banner + expandable leaderboard

**Claude grading prompt (in `supabase/functions/grade-passage/index.ts`):**
```
You are grading a high school student's vocabulary passage.
They were given these SAT words: {wordList with definitions}.
Their passage: "{passage}"

Grade on three dimensions (0-100 each):
1. ACCURACY: Does each word reflect its correct meaning? Be strict but fair.
2. CONCISENESS: How efficiently are words used? Reward tight, punchy writing. Penalize padding.
3. CREATIVITY: How interesting, memorable, or entertaining is the passage? Reward originality, humor, and unexpected scenarios.

Return ONLY a valid JSON object, nothing else:
{
  "accuracy": <number>,
  "conciseness": <number>,
  "creativity": <number>,
  "feedback": "<2-3 sentences of specific, encouraging feedback>",
  "wordFeedback": [
    {"word": "<WORD>", "used": <bool>, "correct": <bool>, "note": "<one short sentence>"}
  ]
}
```

The edge function should validate JSON parsability and retry once before falling back. On total failure, use the local scoring heuristic in the HTML prototype (word count detection + length penalty).

**React Native notes:**
- Score rings: SVG circle with animated `strokeDashoffset`. Drive both the displayed number and the arc fill from the same `useSharedValue`.
- `TextInput multiline numberOfLines={undefined}` with `textAlignVertical: 'top'`. iOS-specific: set `contentInsetAdjustmentBehavior: 'never'`.

---

## Navigation Flow

```
Onboarding (first launch only)
    └─► Home Screen ◄────────┐
            ├─► Crossword Puzzle (full-screen, no tab bar)
            │       └─► (word collected toast) — stays on screen
            ├─► Word Collection ─► Word Detail (bottom sheet)
            ├─► Review Mode (Story / Flashcard / Quiz tabs)
            └─► Passage Writing ─► Grading → Results
                    └─► (Write Another) ────┐
                                            ▼
                              back to Passage Writing form
```

Bottom nav tabs: Home / Puzzles / Collection / Review / Profile. Selected tab has yellow icon + yellow label.

The Crossword Puzzle screen is **full-screen** and hides the bottom tab bar (use `unmountOnBlur` and `tabBarStyle: { display: 'none' }` in expo-router).

---

## Puzzle Pipeline

**Critical: Puzzles are generated offline, not at runtime.** The app fetches a static JSON file per day.

### Daily flow

```
GitHub Action (nightly, 00:00 UTC)
    │
    ├─► word_selector.py  — picks 5-7 SAT words (90-day cooldown)
    ├─► grid_builder.py   — backtracking constructor, fills with clean_fill + edu_proper
    ├─► clue_writer.py    — Claude API writes all clues, flags dated fillers
    │
    └─► uploads puzzles/2026-05-13.json to Supabase Storage (public bucket)

App on launch:
    └─► fetch https://{supabase}/storage/v1/object/public/puzzles/2026-05-13.json
        └─► cache in AsyncStorage; serve from cache if offline
```

### Grid constraints

- 10×10 standard
- Rotational symmetry (NYT convention)
- No words under 3 letters
- No proper nouns outside `edu_proper.json`
- No word repeated across last 90 puzzles

With 1,500 SAT words on a 90-day cooldown: **4+ years of unique daily puzzles** before repeating a feature word.

### Bootstrapping

Before the first scheduled run, generate **30 days of puzzles** locally and upload to the bucket. This buys time to debug the pipeline and ensures users never see "no puzzle today".

---

## Backend (Supabase)

### Schema (`supabase/migrations/001_init.sql`)

```sql
-- Auth tables are provided by Supabase

create table profiles (
  id uuid references auth.users on delete cascade primary key,
  username text not null unique,
  avatar text not null check (avatar in ('owl','fox','lion','shark','wolf','eagle')),
  goal text not null check (goal in ('1200+','1400+','1500+','1600')),
  test_date text not null,
  level text not null,
  streak int default 0 not null,
  class_id uuid references classes(id),
  created_at timestamptz default now() not null
);

create table classes (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  teacher_id uuid references auth.users not null,
  join_code text not null unique,
  created_at timestamptz default now() not null
);

create table collected_words (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles on delete cascade not null,
  word_id int not null,
  word text not null,
  definition text not null,
  mastery text not null default 'new',
  retention int not null default 100 check (retention between 0 and 100),
  review_count int not null default 0,
  collected_at timestamptz default now() not null,
  last_review_at timestamptz,
  puzzle_date date not null,
  unique(user_id, word_id)
);
create index on collected_words(user_id, mastery);
create index on collected_words(user_id, last_review_at);

create table puzzle_completions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles on delete cascade not null,
  puzzle_date date not null,
  duration_seconds int not null,
  words_collected int not null,
  completed_at timestamptz default now() not null,
  unique(user_id, puzzle_date)
);

create table passage_submissions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references profiles on delete cascade not null,
  class_id uuid references classes(id),
  target_words text[] not null,
  passage text not null,
  accuracy int not null,
  conciseness int not null,
  creativity int not null,
  overall int generated always as ((accuracy + conciseness + creativity) / 3) stored,
  feedback text not null,
  word_feedback jsonb not null,
  submitted_at timestamptz default now() not null
);
create index on passage_submissions(class_id, overall desc);

-- Row-Level Security
alter table profiles enable row level security;
alter table collected_words enable row level security;
alter table puzzle_completions enable row level security;
alter table passage_submissions enable row level security;

create policy "Users read own profile" on profiles for select using (auth.uid() = id);
create policy "Users update own profile" on profiles for update using (auth.uid() = id);
create policy "Users read own collected_words" on collected_words for all using (auth.uid() = user_id);
create policy "Users read own completions" on puzzle_completions for all using (auth.uid() = user_id);
create policy "Users insert own submissions" on passage_submissions for insert with check (auth.uid() = user_id);
create policy "Classmates read class submissions" on passage_submissions for select using (
  class_id in (select class_id from profiles where id = auth.uid())
);
```

### Edge Functions

Two functions, both proxy to Claude with the prompts shown in the screen specs:
- `supabase/functions/generate-passage/index.ts` — Story tab
- `supabase/functions/grade-passage/index.ts` — Passage Writing

Set `ANTHROPIC_API_KEY` as a Supabase secret. Never expose it to the app.

Add rate limiting per user (3 generations per minute) via Supabase's `vault` + a simple counter table.

---

## AI Integration Summary

| Where | Model | Purpose | Latency budget |
|---|---|---|---|
| `generate-passage` edge function | claude-haiku-4-5 | Write context story for Story tab | < 3s, fallback to pre-baked |
| `grade-passage` edge function | claude-haiku-4-5 | Grade passage, return JSON | < 5s, fallback to local heuristic |
| `puzzle-pipeline/clue_writer.py` | claude-haiku-4-5 (or sonnet for higher quality clues) | Write all crossword clues + flag dated fillers | offline, no latency constraint |
| Future: AI word selection | claude-haiku-4-5 | Tailor review queue based on forgetting curve | < 1s, prefetched on login |

The app never calls Anthropic directly — all calls route through Supabase Edge Functions.

---

## Animation Inventory

Catalog of every animation in the design — implement these as reusable Reanimated hooks.

| Name | Where | Effect | Duration | Easing |
|---|---|---|---|---|
| `letterPop` | Crossword cell on keystroke | scale 0.4 → 1.18 → 0.96 → 1 | 280ms | cubic-bezier(0.22,1,0.36,1) |
| `wordRipple` | Crossword cells on word complete | bg flash left → right | 500ms per cell, 50ms stagger | ease |
| `toastPop` | Collection toast appear | translateY 100% → -4px → 0 | 450ms | cubic-bezier(0.22,1,0.36,1) |
| `floatStar` | Stars in collection toast | translateY 0 → -50px, scale 1 → 0.5, fade out | 1000ms | ease |
| `slideUp` | Card enters viewport | translateY 20px → 0, fade in | 400ms | ease |
| `shimmer` | Mastered word cards | gradient sweep left → right, infinite | 3000ms | linear |
| `retentionPulse` | Slipping word retention % | opacity 1 → 0.4 → 1 | 1800ms | ease |
| `glowRing` | Daily puzzle play button | box-shadow 0 → 8px → 0 | 2500ms | ease |
| `streakBounce` | Streak icon | scale 1 → 1.18 → 1 | 2000ms | ease |
| `wrongShake` | Onboarding wrong answer | translateX shake | 400ms | ease |
| `cardFlip` | Flashcard | rotateY 0 → 180 | 400ms | cubic-bezier(0.4,0,0.2,1) |
| `ringFill` | Score rings on results | strokeDashoffset 283 → target | 900ms | ease-out-cubic |
| `wordDrift` / `wordFloat` | Background floating words | translateY + fade in/out, infinite | 9-15s, staggered | ease-in-out |
| `cardFlyIn` | Onboarding word chips | translate + scale + rotate from staggered origins | 500ms | cubic-bezier(0.22,1,0.36,1) |
| `starBurst` | Word reveal in Onboarding | scale 0 → 1.4 → 1, rotate -30 → 5 → 0 | 500ms | cubic-bezier |
| `dotBounce` | Typing dots indicator | translateY 0 → -6 → 0, staggered | 1200ms loop | ease |

All durations and easings are sourced from the HTML prototypes — see the `@keyframes` definitions at the top of each file.

---

## Build Phases (Suggested Order)

### Phase 1: Foundation (Week 1)
- [ ] `npx create-expo-app lexicon -t expo-template-blank-typescript`
- [ ] Set up expo-router, Supabase client, design tokens, fonts (Nunito, Space Grotesk, Lora)
- [ ] Build reusable primitives: `Button`, `WordChip`, `RetentionArc`, `StatusBar`, `MeshBg`, `FloatingWords`
- [ ] Auth flow: Sign in with Apple + Google + email (Supabase Auth)

### Phase 2: Crossword (Weeks 2–3)
- [ ] `Cell`, `Grid`, `Keyboard`, `ClueBar` components
- [ ] Game state machine (selection, direction, completion detection)
- [ ] Animations: letterPop, wordRipple
- [ ] `CollectionToast` with floating stars
- [ ] Puzzle fetching + caching
- [ ] Hardcode one puzzle for testing; add pipeline output later

### Phase 3: Home + Collection (Week 4)
- [ ] Home screen with all sections
- [ ] Collection screen with grid + horizontal scrolls + tabs
- [ ] Word detail bottom sheet
- [ ] Retention algorithm + Focus Queue sorting

### Phase 4: Review + Write (Weeks 5–6)
- [ ] Review screen with all three tabs
- [ ] Supabase Edge Function: `generate-passage`
- [ ] Passage Writing form + grading animation + results
- [ ] Supabase Edge Function: `grade-passage`
- [ ] Class leaderboard

### Phase 5: Onboarding + Polish (Week 7)
- [ ] 6-step onboarding flow with all animations
- [ ] Profile screen (still un-designed — see "Not Yet Built")
- [ ] Push notifications for daily puzzle (expo-notifications)
- [ ] Settings, account deletion (required by App Store)

### Phase 6: Pipeline + Launch (Week 8)
- [ ] Python pipeline (word_selector, grid_builder, clue_writer)
- [ ] Generate 30 puzzles, upload to Supabase Storage
- [ ] GitHub Actions nightly workflow
- [ ] Privacy policy, terms of service URLs
- [ ] App Store + Play Store assets (screenshots, app icon at all sizes)
- [ ] **EAS Build** → submit to TestFlight + Play Console internal testing
- [ ] App Store review + launch

---

## App Store Requirements Checklist

### Apple (iOS)
- [ ] **Sign in with Apple** — required if any social login is offered (mandatory)
- [ ] Privacy policy URL on a public web page
- [ ] App Privacy "nutrition label" — disclose data collected (email, username, learning progress)
- [ ] Age rating **12+** — content is for 14–18, but rating must reflect AI-generated content (Apple flags this)
- [ ] Account deletion flow inside the app (mandatory since 2022)
- [ ] Screenshots at 6.7" and 6.1" sizes
- [ ] Native app — Apple rejects WKWebView wrappers. React Native compiles to native, so this is fine.
- [ ] Apple Developer account ($99/yr)

### Google Play
- [ ] Privacy policy URL
- [ ] Data safety form
- [ ] Target API level 34+ (current as of May 2026)
- [ ] Google Play Developer account ($25 one-time)

### Both
- [ ] Real production push notification certificates (`expo prebuild` handles this on EAS)
- [ ] Crash reporting (Sentry is the easy choice for Expo apps)
- [ ] Analytics — be careful: anything tracking minors needs explicit COPPA/GDPR-K compliance. **Recommend: server-side analytics only** (count events in Postgres), no third-party SDKs that fingerprint users.

---

## What's Not Yet Built

These screens are mentioned in the design but **do not have HTML mockups**. Build them after Phase 5:

- **Profile / Stats screen** — personal mastery history, achievement badges, settings, account deletion
- **Teacher Dashboard** — separate web app (not mobile); assign writing challenges, view class progress, export to gradebook
- **Full Leaderboard screen** — expanded class rankings with player profiles (the Passage Writing screen has an inline preview)
- **Puzzle archive** — browse past puzzles by date/difficulty

When implementing these, follow the design tokens and component patterns established by the 6 designed screens.

---

## Key Reminders

1. **The HTML files are references, not source code.** Open them in a browser, mirror them in React Native, do not embed or eval them.
2. **Every color, radius, and spacing value is a design token.** Pull from `src/theme/tokens.ts`. Do not hardcode hex values in screen components.
3. **The puzzle pipeline runs offline.** The app never generates puzzles at runtime — it fetches JSON.
4. **All Claude calls go through Supabase Edge Functions.** Never put `ANTHROPIC_API_KEY` in the app binary.
5. **Auto-collection is the whole pitch.** When a SAT word completes in the crossword, the toast and database write must happen with no user friction — no "Tap to collect" button.
6. **Sign in with Apple is mandatory** for App Store approval if you have any social auth. Build it from day one.

---

## Questions to Resolve Before Starting

These weren't specified in the original brief — ask the product owner before Phase 1:

1. **Pricing model** — free, freemium, school licenses, or one-time purchase? Affects payment integration scope.
2. **Class join flow** — students enter a 6-char code from the teacher? Or QR scan?
3. **Push notification cadence** — daily puzzle reminder time (per-user setting?) and review nudges?
4. **Offline mode** — must the crossword be playable offline? (Recommend: yes for the last fetched puzzle; word collection sync on reconnect)
5. **Multiple devices per user** — sync across phone + tablet? (Yes if shipping on iPad)
6. **Streak rules** — does playing the puzzle preserve the streak, or only solving it? Grace days for missed days?

---

*Generated from design files dated April 27 – May 13, 2026.*
