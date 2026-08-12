# LEXICON — SAT Vocabulary Crossword

A mobile-first vocabulary game for SAT prep. Play a daily crossword where the
featured answers are SAT words, collect those words like a Pokédex, review them
with AI-generated passages and quizzes, and write your own AI-graded passages.

Built with **Expo (React Native) + TypeScript + expo-router** from the design
handoff in [`design/HANDOFF.md`](design/HANDOFF.md).

## Getting started

```bash
npm install
npm start          # then press i / a, or scan with Expo Go
```

The app runs fully offline out of the box: it ships with demo collection data
and local fallbacks for every AI feature. To enable the real backend, copy
`.env.example` to `.env` and fill in your Supabase credentials.

For building and shipping on iOS and Android — EAS profiles, icon generation,
and the Android-specific behaviour the code deliberately handles — see
[`docs/MOBILE.md`](docs/MOBILE.md).

```bash
npm run typecheck  # tsc --noEmit
```

## Project layout

```
app/                       expo-router screens
  (auth)/onboarding.tsx     6-step onboarding flow
  (tabs)/                   Home · Puzzles · Collection · Review · Profile
  (tabs)/write.tsx          Passage Writing (hidden from tab bar)
  puzzle/[date].tsx         Full-screen crossword game
src/
  components/               UI primitives, crossword pieces, backgrounds
  theme/                    Design tokens, typography, animation curves
  data/                     Puzzle data, retention algorithm, AI client
  stores/                   AppStore — global state with AsyncStorage
  types/                    Shared TypeScript models
supabase/
  migrations/               Postgres schema + Row-Level Security
  functions/                Edge Functions (Claude proxy for AI features)
design/                     Original design handoff + HTML references
```

## What's implemented

- **Crossword game** — interactive 10×10 grid, custom keyboard, letter-pop and
  word-ripple animations, automatic word collection with a star-burst toast.
- **Home hub** — daily puzzle card, stats, AI slipping-words notice, quick
  actions, class challenge, live activity ticker.
- **Collection** — Pokédex grid, AI Focus Queue sorted by an urgency score,
  retention arcs, word detail bottom sheet.
- **Review** — Story (AI passages), Flashcards (flip animation), Quiz tabs.
- **Passage Writing** — live score estimates, animated grading, score rings,
  word-by-word breakdown, class leaderboard.
- **Onboarding / Profile / Puzzle archive** — full flows.
- **Post-solve summary** — celebration, solve stats, and a definition recap
  of the puzzle's SAT words that routes into review.
- **Supabase** — schema with RLS and two Claude-proxy edge functions.

## Notes for production

- All AI calls route through Supabase Edge Functions; `ANTHROPIC_API_KEY` is
  never bundled into the app.
- Puzzles are generated offline and served as static JSON — see the Puzzle
  Pipeline section of `design/HANDOFF.md`.
- `AppStore` currently seeds demo data; swap its actions for Supabase queries
  when wiring the backend.
