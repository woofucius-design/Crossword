import type { Puzzle } from '@/types/models';

// 10x10 NYT-style daily mini. '#' = black square.
// Mirrors design/screens/Crossword Puzzle.html — the implementation reference.
const SOLUTION: string[][] = [
  ['#', '#', '#', '#', 'L', 'U', 'C', 'I', 'D', '#'],
  ['#', '#', '#', '#', '#', '#', 'A', 'R', 'E', '#'],
  ['#', 'O', 'P', 'U', 'L', 'E', 'N', 'T', '#', '#'],
  ['#', '#', '#', 'B', 'O', 'N', 'D', '#', '#', 'D'],
  ['S', 'T', 'O', 'I', 'C', '#', 'O', 'D', 'E', 'A'],
  ['#', '#', 'N', '#', '#', '#', 'R', 'A', 'N', 'T'],
  ['#', '#', 'C', 'O', 'T', '#', '#', '#', '#', 'E'],
  ['#', 'V', 'E', 'R', 'B', 'O', 'S', 'E', '#', 'S'],
  ['#', '#', '#', '#', 'T', 'E', 'R', 'S', 'E', '#'],
  ['#', '#', '#', '#', '#', '#', '#', '#', '#', '#'],
];

const CELL_NUMS: Record<string, number> = {
  '0,4': 1,
  '0,6': 2,
  '1,6': 3,
  '2,1': 4,
  '3,3': 5,
  '3,9': 6,
  '4,0': 7,
  '4,2': 8,
  '4,6': 9,
  '5,6': 10,
  '6,2': 11,
  '7,1': 12,
  '8,4': 13,
};

// Pre-filled cells simulate an in-progress puzzle (matches the prototype).
const PRE_FILLED: Record<string, string> = {};
['O', 'P', 'U', 'L', 'E'].forEach((l, i) => {
  PRE_FILLED[`2,${1 + i}`] = l;
});
['V', 'E', 'R', 'B'].forEach((l, i) => {
  PRE_FILLED[`7,${1 + i}`] = l;
});
['C', 'A', 'N'].forEach((l, i) => {
  PRE_FILLED[`${i},6`] = l;
});
['B', 'O', 'N', 'D'].forEach((l, i) => {
  PRE_FILLED[`3,${3 + i}`] = l;
});
PRE_FILLED['4,2'] = 'O';
PRE_FILLED['5,2'] = 'N';

const cells: Puzzle['cells'] = {};
for (let r = 0; r < 10; r++) {
  for (let c = 0; c < 10; c++) {
    const key = `${r},${c}`;
    const number = CELL_NUMS[key];
    const preFilled = PRE_FILLED[key];
    if (number !== undefined || preFilled !== undefined) {
      cells[key] = { number, preFilled };
    }
  }
}

export const samplePuzzle: Puzzle = {
  date: '2026-05-22',
  number: 48,
  size: { rows: 10, cols: 10 },
  solution: SOLUTION,
  cells,
  words: [
    {
      id: '1A',
      number: 1,
      direction: 'across',
      row: 0,
      col: 4,
      length: 5,
      answer: 'LUCID',
      clue: 'Clearly expressed; easy to understand',
      isSATVocab: true,
      definition: 'adjective — clear, coherent; easy to understand; mentally sound',
    },
    {
      id: '2D',
      number: 2,
      direction: 'down',
      row: 0,
      col: 6,
      length: 6,
      answer: 'CANDOR',
      clue: 'Frankness and honesty in expression',
      isSATVocab: true,
      definition: 'noun — the quality of being open, honest, and direct',
    },
    {
      id: '4A',
      number: 4,
      direction: 'across',
      row: 2,
      col: 1,
      length: 7,
      answer: 'OPULENT',
      clue: 'Ostentatiously rich and luxurious',
      isSATVocab: true,
      definition: 'adjective — showing great wealth; lavish; exhibiting luxury',
    },
    {
      id: '7A',
      number: 7,
      direction: 'across',
      row: 4,
      col: 0,
      length: 5,
      answer: 'STOIC',
      clue: 'Enduring hardship without showing feelings',
      isSATVocab: true,
      definition: 'adjective — enduring pain or difficulty without complaint or emotion',
    },
    {
      id: '12A',
      number: 12,
      direction: 'across',
      row: 7,
      col: 1,
      length: 7,
      answer: 'VERBOSE',
      clue: 'Using more words than needed',
      isSATVocab: true,
      definition: 'adjective — using or expressed in more words than are needed; wordy',
    },
    {
      id: '13A',
      number: 13,
      direction: 'across',
      row: 8,
      col: 4,
      length: 5,
      answer: 'TERSE',
      clue: 'Sparing in words; brief to the point of rudeness',
      isSATVocab: true,
      definition: 'adjective — briefly and cleanly expressed; curt',
    },
    {
      id: '3A',
      number: 3,
      direction: 'across',
      row: 1,
      col: 6,
      length: 3,
      answer: 'ARE',
      clue: 'To exist (plural present tense)',
      isSATVocab: false,
    },
    {
      id: '5A',
      number: 5,
      direction: 'across',
      row: 3,
      col: 3,
      length: 4,
      answer: 'BOND',
      clue: 'A tie or connection',
      isSATVocab: false,
    },
    {
      id: '9A',
      number: 9,
      direction: 'across',
      row: 4,
      col: 6,
      length: 4,
      answer: 'ODEA',
      clue: 'Small ancient theaters for music',
      isSATVocab: false,
    },
    {
      id: '10A',
      number: 10,
      direction: 'across',
      row: 5,
      col: 6,
      length: 4,
      answer: 'RANT',
      clue: 'To speak or shout at length in anger',
      isSATVocab: false,
    },
    {
      id: '11A',
      number: 11,
      direction: 'across',
      row: 6,
      col: 2,
      length: 3,
      answer: 'COT',
      clue: 'A small, narrow bed',
      isSATVocab: false,
    },
    {
      id: '6D',
      number: 6,
      direction: 'down',
      row: 3,
      col: 9,
      length: 5,
      answer: 'DATES',
      clue: 'Calendar days; romantic outings',
      isSATVocab: false,
    },
    {
      id: '8D',
      number: 8,
      direction: 'down',
      row: 4,
      col: 2,
      length: 4,
      answer: 'ONCE',
      clue: 'One single time',
      isSATVocab: false,
    },
  ],
};
