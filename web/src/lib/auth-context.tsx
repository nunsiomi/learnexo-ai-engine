import type { Session, User } from "@supabase/supabase-js";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { supabase, type Profile } from "./supabase";

type AuthContextValue = {
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  loading: boolean;
  refreshProfile: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);

  // Loads the signed-in user's profile row, creating it on first authenticated
  // load if it doesn't exist yet. Profile creation can't happen at signup time
  // when email confirmation is required — there's no session yet, so an insert
  // would fail RLS (auth.uid() is null until the user actually has a session).
  // Doing it here instead means it works whether or not confirmation is on.
  const loadProfile = async (user: User) => {
    const { data } = await supabase
      .from("profiles")
      .select("*")
      .eq("id", user.id)
      .maybeSingle();

    if (data) {
      setProfile(data);
      return;
    }

    const meta = user.user_metadata as {
      full_name?: string;
      default_class_level?: string;
    };
    const { data: created } = await supabase
      .from("profiles")
      .insert({
        id: user.id,
        full_name: meta.full_name ?? user.email ?? "Student",
        default_class_level: meta.default_class_level ?? null,
      })
      .select("*")
      .single();
    setProfile(created ?? null);
  };

  const refreshProfile = async () => {
    if (session?.user) await loadProfile(session.user);
  };

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session?.user) loadProfile(session.user).finally(() => setLoading(false));
      else setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session?.user) loadProfile(session.user);
      else setProfile(null);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user: session?.user ?? null,
        session,
        profile,
        loading,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
