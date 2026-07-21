import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string | undefined;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as
  | string
  | undefined;

if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  throw new Error(
    "VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY must be set. Copy web/.env.example to web/.env and fill in your Supabase project's values.",
  );
}

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

export type Profile = {
  id: string;
  full_name: string;
  default_class_level: string | null;
  created_at: string;
};

export type TopicProgress = {
  id: string;
  user_id: string;
  subject: string;
  topic_slug: string;
  completed_at: string;
};
