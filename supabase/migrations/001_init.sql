-- LEXICON initial schema. Auth tables are provided by Supabase.

create table classes (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  teacher_id uuid references auth.users not null,
  join_code text not null unique,
  created_at timestamptz default now() not null
);

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
create policy "Users insert own profile" on profiles for insert with check (auth.uid() = id);
create policy "Users manage own collected_words" on collected_words for all using (auth.uid() = user_id);
create policy "Users manage own completions" on puzzle_completions for all using (auth.uid() = user_id);
create policy "Users insert own submissions" on passage_submissions for insert with check (auth.uid() = user_id);
create policy "Classmates read class submissions" on passage_submissions for select using (
  class_id in (select class_id from profiles where id = auth.uid())
);
