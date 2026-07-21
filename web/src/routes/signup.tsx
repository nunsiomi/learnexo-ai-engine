import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, type FormEvent } from "react";

import { supabase } from "@/lib/supabase";
import { useAuth } from "@/lib/auth-context";

export const Route = createFileRoute("/signup")({
  head: () => ({
    meta: [{ title: "Sign up · LearNEXO" }],
  }),
  component: SignupPage,
});

const CLASS_LEVELS = ["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"] as const;

function SignupPage() {
  const navigate = useNavigate();
  const { refreshProfile } = useAuth();

  const [firstName, setFirstName] = useState("");
  const [surname, setSurname] = useState("");
  const [classLevel, setClassLevel] = useState<string>("JSS1");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checkEmail, setCheckEmail] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (firstName.trim().length < 2) {
      setError("Please enter your first name.");
      return;
    }
    if (surname.trim().length < 2) {
      setError("Please enter your surname.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters.");
      return;
    }

    setLoading(true);
    const { data, error: signUpError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          first_name: firstName.trim(),
          full_name: `${firstName.trim()} ${surname.trim()}`,
          default_class_level: classLevel,
        },
      },
    });
    if (signUpError) {
      setError(signUpError.message);
      setLoading(false);
      return;
    }

    setLoading(false);

    if (data.session) {
      // No email confirmation required — session exists now, so the profile
      // row can be created immediately (auth-context does this on load).
      await refreshProfile();
      navigate({ to: "/" });
    } else {
      // Email confirmation required — no session yet, so the profile row
      // will be created once the user confirms and actually signs in.
      setCheckEmail(true);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-5 py-10">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-8 flex items-center justify-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-navy text-navy-foreground font-bold text-lg">
            L
          </div>
          <span className="text-xl font-bold tracking-tight text-foreground">
            Lear<span className="text-accent">NEXO</span>
          </span>
        </Link>

        <div className="rounded-3xl border border-border bg-card p-6 shadow-card sm:p-8 space-y-5">
          {checkEmail ? (
            <div className="text-center space-y-2 py-4">
              <h1 className="text-xl font-bold text-foreground">Check your email</h1>
              <p className="text-sm text-muted-foreground">
                We sent a confirmation link to <span className="font-semibold text-foreground">{email}</span>.
                Confirm your email, then come back and sign in.
              </p>
              <Link to="/login" className="inline-block mt-2 font-semibold text-accent hover:underline">
                Go to sign in
              </Link>
            </div>
          ) : (
          <>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Create your account</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Tell us a bit about yourself to get a personalized learning path.
            </p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="field-label" htmlFor="firstName">First name</label>
                <input
                  id="firstName"
                  type="text"
                  className="field-input"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  placeholder="e.g. Chioma"
                  required
                />
              </div>
              <div>
                <label className="field-label" htmlFor="surname">Surname</label>
                <input
                  id="surname"
                  type="text"
                  className="field-input"
                  value={surname}
                  onChange={(e) => setSurname(e.target.value)}
                  placeholder="e.g. Okafor"
                  required
                />
              </div>
            </div>
            <div>
              <label className="field-label" htmlFor="classLevel">Class level</label>
              <select
                id="classLevel"
                className="field-input"
                value={classLevel}
                onChange={(e) => setClassLevel(e.target.value)}
              >
                {CLASS_LEVELS.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="field-label" htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                className="field-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="field-label" htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                className="field-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={6}
                required
              />
            </div>

            {error && (
              <p className="text-sm text-destructive" role="alert">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-pill btn-pill-accent w-full justify-center disabled:opacity-60"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-accent hover:underline">
              Sign in
            </Link>
          </p>
          </>
          )}
        </div>
      </div>
    </div>
  );
}
