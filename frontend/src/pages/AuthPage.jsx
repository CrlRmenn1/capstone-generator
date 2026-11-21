import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router";
import { api } from "../api";
import { useApp } from "../app-context";
import { Alert, Button } from "../components/ui";

export default function AuthPage({ mode }) {
  const isRegister = mode === "register";
  const { user, meta, applySession, toast } = useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const next = location.state?.next || "/";
  const [form, setForm] = useState({ name: "", email: "", password: "", program: "BSIT" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to={next} replace />;
  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await api.post(isRegister ? "/auth/register" : "/auth/login", form);
      applySession(data);
      toast(isRegister ? "Account created." : `Welcome back, ${data.user.name.split(" ")[0]}.`);
      navigate(next, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-[26rem]">
      <h1 className="font-serif text-[2.1rem] leading-tight font-semibold tracking-[-0.01em]">{isRegister ? "Create your account" : "Log in"}</h1>
      <p className="mt-2 text-[15px] text-ink-soft">
        {isRegister ? "Your account keeps your saved titles and Chapter 1 drafts in one place." : "Continue where your team left off."}
      </p>
      <form onSubmit={submit} className="mt-8 space-y-5">
        {error && <Alert tone="error">{error}</Alert>}
        {isRegister && (
          <label className="block">
            <span className="label">Full name</span>
            <input className="input" value={form.name} onChange={set("name")} required autoComplete="name" />
          </label>
        )}
        <label className="block">
          <span className="label">Email</span>
          <input className="input" type="email" value={form.email} onChange={set("email")} required autoComplete="email" />
        </label>
        <label className="block">
          <span className="label">Password</span>
          <input className="input" type="password" value={form.password} onChange={set("password")} required minLength={isRegister ? 8 : undefined} autoComplete={isRegister ? "new-password" : "current-password"} />
          {isRegister && <span className="mt-1.5 block text-[13px] text-ink-faint">At least 8 characters.</span>}
        </label>
        {isRegister && meta && (
          <label className="block">
            <span className="label">Program</span>
            <select className="input" value={form.program} onChange={set("program")}>
              {meta.programs.map((p) => <option key={p.key} value={p.key}>{p.key}, {p.label}</option>)}
            </select>
          </label>
        )}
        <Button type="submit" className="w-full" size="lg" loading={loading}>{isRegister ? "Create account" : "Log in"}</Button>
      </form>
      <p className="mt-6 border-t border-rule pt-5 text-sm text-ink-soft">
        {isRegister ? "Already have an account? " : "New to CapSense? "}
        <Link to={isRegister ? "/login" : "/register"} state={{ next }} className="font-medium text-binding underline-offset-2 hover:underline">
          {isRegister ? "Log in" : "Create an account"}
        </Link>
      </p>
    </div>
  );
}
