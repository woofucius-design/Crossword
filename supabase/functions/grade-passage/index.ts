// Supabase Edge Function: grade-passage
// Proxies passage grading to Claude and returns structured JSON scores.
// Validates JSON parsability and retries once before surfacing an error so
// the app can fall back to its local heuristic.

const ANTHROPIC_API_KEY = Deno.env.get('ANTHROPIC_API_KEY')!;
const MODEL = 'claude-haiku-4-5';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, content-type',
};

interface GradeResult {
  scores: {
    accuracy: number;
    conciseness: number;
    creativity: number;
    overall: number;
  };
  feedback: string;
  wordFeedback: Array<{
    word: string;
    used: boolean;
    correct: boolean;
    note: string;
  }>;
}

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { passage, words } = await req.json();
    if (typeof passage !== 'string' || !Array.isArray(words)) {
      return json({ error: 'passage and words required' }, 400);
    }

    const prompt = `You are grading a high school student's vocabulary passage.
They were given these SAT words: ${words.join(', ')}.
Their passage: "${passage}"

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
}`;

    const parsed = (await callClaude(prompt)) ?? (await callClaude(prompt));
    if (!parsed) return json({ error: 'grading failed' }, 502);

    const result: GradeResult = {
      scores: {
        accuracy: clamp(parsed.accuracy),
        conciseness: clamp(parsed.conciseness),
        creativity: clamp(parsed.creativity),
        overall: clamp(
          Math.round(
            (Number(parsed.accuracy) +
              Number(parsed.conciseness) +
              Number(parsed.creativity)) /
              3,
          ),
        ),
      },
      feedback: String(parsed.feedback ?? ''),
      wordFeedback: Array.isArray(parsed.wordFeedback) ? parsed.wordFeedback : [],
    };

    return json(result);
  } catch (err) {
    return json({ error: String(err) }, 500);
  }
});

async function callClaude(prompt: string): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 700,
        messages: [{ role: 'user', content: prompt }],
      }),
    });
    if (!res.ok) return null;
    const data = await res.json();
    const text: string = data.content?.[0]?.text ?? '';
    const match = text.match(/\{[\s\S]*\}/);
    if (!match) return null;
    return JSON.parse(match[0]);
  } catch {
    return null;
  }
}

function clamp(n: unknown): number {
  const num = Number(n);
  if (Number.isNaN(num)) return 0;
  return Math.max(0, Math.min(100, Math.round(num)));
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, 'content-type': 'application/json' },
  });
}
