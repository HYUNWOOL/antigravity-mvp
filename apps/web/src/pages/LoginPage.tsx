import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { supabase } from "../lib/supabase";

export function LoginPage() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSignIn() {
    setLoading(true);
    setError("");
    const { error: signInError } = await supabase.auth.signInWithPassword({ email, password });
    setLoading(false);

    if (signInError) {
      setError(signInError.message);
      return;
    }

    void navigate("/products");
  }

  async function handleSignUp() {
    setLoading(true);
    setError("");
    const { error: signUpError } = await supabase.auth.signUp({ email, password });
    setLoading(false);

    if (signUpError) {
      setError(signUpError.message);
      return;
    }

    void navigate("/products");
  }

  return (
    <div className="page">
      <div className="card">
        <h1>Antigravity Login</h1>
        <p>Sign in or create an account to buy products.</p>

        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="you@example.com"
        />

        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="At least 6 characters"
        />

        {error ? <p className="error">{error}</p> : null}

        <div className="button-row">
          <button type="button" disabled={loading || !email || !password} onClick={handleSignIn}>
            {loading ? "Working..." : "Sign In"}
          </button>
          <button type="button" disabled={loading || !email || !password} onClick={handleSignUp}>
            {loading ? "Working..." : "Sign Up"}
          </button>
        </div>
      </div>
    </div>
  );
}
