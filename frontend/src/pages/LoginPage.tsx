
import { useState, type FormEvent } from "react";
import { ApiError, login, saveToken } from "../api/client";

interface Props {
  onLoginSuccess: () => void;
}

export default function LoginPage({ onLoginSuccess }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    if (!username.trim() || !password) {
      setError("Please enter your username and password.");
      return;
    }

    setLoading(true);

    try {
      const result = await login(username.trim(), password);
      saveToken(result.access_token);
      onLoginSuccess();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          setError("Invalid username or password.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-container">
      <section className="login-card">
        <p className="eyebrow">PROJECT 3</p>
        <h1>Absence &amp; Capacity</h1>
        <h2>Sign in</h2>
        <p>Enter your account details to continue.</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Enter your username"
            autoComplete="username"
            required
          />

          <label htmlFor="password">Password</label>
          <div className="password-input">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter your password"
              autoComplete="current-password"
              required
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? "Hide" : "Show"}
            </button>
          </div>

          {error && <p className="login-error" role="alert">{error}</p>}

          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
