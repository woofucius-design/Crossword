# Shipping LEXICON on iOS and Android

One Expo (React Native) codebase targets iOS, Android and web. There are no
per-platform forks — differences are handled inline via `src/theme/platform.ts`
and `src/hooks/useAndroidBack.ts`. This document covers what is done, what a
release still needs, and the Android-specific traps already paid for once.

## Current state

| | iOS | Android | Web |
|---|---|---|---|
| Bundles | yes | yes (`expo export --platform android`) | configured, unpolished |
| Icons / splash | yes | yes, incl. adaptive + monochrome | favicon |
| Build config | `eas.json` | `eas.json` | `expo export` |
| Platform fixes | baseline | done (see below) | not started |
| Store assets | not started | not started | n/a |

## Build and run

```bash
npm install
npm start                 # press i / a, or scan with Expo Go

npx expo export --platform android   # verify the bundle compiles
npm run typecheck
```

Icons regenerate from a single script — edit the mark there, not the PNGs:

```bash
python3 scripts/gen_assets.py
```

Native `ios/` and `android/` directories are intentionally absent and
gitignored. The project uses Continuous Native Generation: `expo prebuild`
derives them from `app.json`, so **native settings belong in `app.json`**, never
in a checked-in native file.

### EAS profiles

| Profile | Android artifact | Use |
|---|---|---|
| `development` | debug APK + dev client | day-to-day on a device |
| `preview` | release APK | share a build without the Play Store |
| `production` | AAB | Play Store upload (`submit` targets the internal track as a draft) |

```bash
eas build --profile preview --platform android
eas build --profile production --platform all
```

## Android differences already handled

These are the ones that actually bit, kept here so they don't get
"simplified" back out.

**Hardware back.** Android has a back button; iOS does not. Every screen
holding unsaved state registers `useAndroidBack`. Without it, back pops the
route: mid-puzzle it discarded the grid, and in onboarding it landed on
`app/index.tsx`, which redirects to onboarding step 0 — silently erasing
everything the student had entered.

**Elevation is not `shadowColor`.** Android draws shadows from `elevation`,
which ignores `shadowColor` below API 28 and derives its shape from the view
*outline*. A shadow on a view with no `borderRadius` casts a square, even when
a rounded child fills it. Coloured glows need `glowFallback()`.

**Children outside the parent box are clipped.** `overflow: 'visible'` is
unreliable on Android. Anything overhanging — a badge dot, particles animating
upward — needs real space in the parent, not negative offsets.

**Fonts.** Setting `fontStyle: 'italic'` (or `fontWeight`) on top of an
already-styled family makes Android synthesise the style a *second* time on
top of the real glyphs. Always select the correctly-cut family. Android also
adds vertical glyph padding that iOS doesn't; spread `tightText` wherever
`lineHeight` sits close to `fontSize`.

**Symbols are not icons.** Unicode glyphs render from whatever the device font
stack has. Geometric Shapes Extended (U+2B00–U+2BFF) and several Technical
symbols are missing on some OEM skins and render as tofu. Anything load-bearing
uses `@expo/vector-icons`, which bundles its own font.

**The keyboard resizes the window.** With `softwareKeyboardLayoutMode:
"resize"`, `useWindowDimensions()` *shrinks* when the soft keyboard opens.
Deriving memoised layout from `height` therefore recomputes on every focus —
this restarted all 24 background animations when a student tapped a text field.
Also why `KeyboardAvoidingView` uses `behavior="padding"` on iOS only: Android
has already compensated, and padding double-counts it.

**Ripples.** Android users read a missing ripple as an unresponsive control.
Use `ripple()` from `src/theme/platform.ts`; it returns `undefined` on iOS,
where the existing opacity press styles are the convention.

## Before a store release

Roughly in order.

1. **Real puzzle content.** `getPuzzle()` in `src/data/puzzles.ts` still
   returns the bundled 10×10 sample for every date, while `puzzle-pipeline/`
   holds ~340 generated puzzles. Needs a publish step, a fetch-and-cache layer,
   and UI for the pipeline's `featured[]` / `isMarquee` / `altClues` fields.
   A 15×15 grid also needs zoom or pan on a phone.
2. **Backend.** `AppStore` seeds demo data; swap its actions for Supabase
   queries. Schema, RLS and the two Claude-proxy edge functions already exist.
   Sync matters here: solving on web at school and on a phone at home is the
   actual use case.
3. **Store requirements.** Privacy policy URL, Apple privacy nutrition labels,
   Google Data Safety form, screenshots per device class. If under-13 students
   are in scope, COPPA/FERPA obligations change what may be collected — decide
   before writing the forms. Apple requires Sign in with Apple if any other
   social login ships; the account-deletion path is already built.
4. **Device testing.** Everything above was verified by typecheck and bundle,
   not on hardware. Specifically unverified on a real device: `MaskedView`
   (the LEXICON wordmark) under the new architecture, radial-gradient banding
   in `MeshBg`, Reanimated layout animations in onboarding, and `Intl` date
   formatting under Hermes.
5. **Notifications.** `expo-notifications` for the daily-puzzle habit loop;
   the Android notification silhouette is already generated.
6. **CI.** No tests exist. The highest-value first check is `tsc --noEmit`
   plus a puzzle-JSON schema validator — that schema is the contract between
   the pipeline and the app, and nothing currently enforces it.
7. **OTA updates.** `expo-updates` / EAS Update lets clue-quality fixes ship
   without store review, which matches how the word bank actually iterates.
