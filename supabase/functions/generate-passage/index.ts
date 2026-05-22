// Supabase Edge Function: generate-passage
// Proxies the Story-tab passage generation to Claude. The ANTHROPIC_API_KEY
// stays server-side and never ships in the app binary.

const ANTHROPIC_API_KEY = Deno.env.get('ANTHROPIC_API_KEY')!;
const MODEL = 'claude-haiku-4-5';

const ABSURDITY_INSTRUCTION: Record<string, string> = {
  low: 'Keep it slightly quirky but mostly realistic.',
  medium:
    'Make it entertainingly absurd — ridiculous scenarios are fine as long as words are used correctly.',
  high: 'Make it maximally unhinged and bizarre.',
};

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, content-type',
};

Deno.serve(async (req: Request) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { words, absurdity } = await req.json();
    if (!Array.isArray(words) || words.length === 0) {
      return json({ error: 'words required' }, 400);
    }

    const instruction =
      ABSURDITY_INSTRUCTION[absurdity] ?? ABSURDITY_INSTRUCTION.medium;

    const prompt = `You are a vocabulary teacher creating memorable study passages for SAT students.

Generate a single short paragraph (2-4 sentences, max 80 words) that:
1. Uses as many of these words as possible IN CONTEXT: ${words.join(', ')}
2. Uses each word grammatically correctly with its real meaning
3. ${instruction}
4. Is a single coherent (if ridiculous) story or scenario

Return ONLY the paragraph. No title, no explanation, no quotes around it. Use the words in ALL CAPS exactly as provided.`;

    const res = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-api-key': ANTHROPIC_API_KEY,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: MODEL,
        max_tokens: 300,
        messages: [{ role: 'user', content: prompt }],
      }),
    });

    if (!res.ok) {
      return json({ error: `claude ${res.status}` }, 502);
    }

    const data = await res.json();
    const passage: string = data.content?.[0]?.text?.trim() ?? '';
    if (!passage) return json({ error: 'empty response' }, 502);

    return json({ passage });
  } catch (err) {
    return json({ error: String(err) }, 500);
  }
});

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...corsHeaders, 'content-type': 'application/json' },
  });
}
