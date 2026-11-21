import { LogOut, Menu, X } from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router";
import { api } from "../api";
import { useApp } from "../app-context";
import { cx } from "./ui";
import WelcomeTour from "./WelcomeTour";

const NAV = [
  { to: "/", label: "Find titles", end: true },
  { to: "/saved", label: "Saved", auth: true },
  { to: "/outlines", label: "Chapter 1 drafts", auth: true },
  { to: "/settings", label: "AI settings", auth: true },
  { to: "/guide", label: "Guide" },
];

function EngineSwitch() {
  const { ai, preferAi, setEnginePreference, user, meta } = useApp();
  if (!user || !ai) return null;
  const provider = meta?.providers?.find((p) => p.key === ai.provider)?.label || ai.provider;
  return (
    <div className="hidden items-center rounded-md border border-rule p-0.5 text-[13px] md:flex" role="group" aria-label="Writing engine">
      {[
        [false, "Built-in", "Use the built-in engine (free, no API calls)"],
        [true, "AI", `Use your ${provider} key (${ai.model})`],
      ].map(([value, label, title]) => (
        <button
          key={label}
          onClick={() => setEnginePreference(value)}
          aria-pressed={preferAi === value}
          title={title}
          className={cx("rounded px-2.5 py-1 transition-colors", preferAi === value ? "bg-binding text-binding-ink" : "text-ink-soft hover:text-ink")}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

export default function Layout() {
  const { user, progress, recordProgress, applySession, toast, toasts } = useApp();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const showTour = Boolean(user && progress && !progress.tour_seen);

  async function logout() {
    applySession(await api.post("/auth/logout"));
    toast("Logged out.");
    navigate("/");
  }

  const links = NAV.filter((n) => !n.auth || user);
  const linkCls = ({ isActive }) =>
    cx(
      "relative py-1 text-[14px] transition-colors",
      isActive ? "font-medium text-ink after:absolute after:inset-x-0 after:-bottom-[19px] after:h-0.5 after:bg-binding" : "text-ink-soft hover:text-ink",
    );
  const mobileCls = ({ isActive }) => cx("block rounded-md px-3 py-2.5 text-[15px]", isActive ? "bg-binding-wash font-medium text-binding" : "text-ink-soft");

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-rule bg-desk/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-8 px-4 sm:px-6">
          <Link to="/" className="font-serif text-[21px] font-semibold tracking-[-0.01em]">
            CapSense
          </Link>
          <nav className="hidden items-center gap-6 lg:flex">
            {links.map(({ to, label, end }) => (
              <NavLink key={to} to={to} end={end} className={linkCls}>
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-4">
            <EngineSwitch />
            {user ? (
              <div className="hidden items-center gap-3 text-[14px] lg:flex">
                <span className="text-ink-soft">{user.name}</span>
                <button onClick={logout} className="text-ink-soft hover:text-ink" title="Log out" aria-label="Log out">
                  <LogOut className="size-4" />
                </button>
              </div>
            ) : (
              <div className="hidden items-center gap-4 text-[14px] lg:flex">
                <Link to="/login" className="text-ink-soft hover:text-ink">Log in</Link>
                <Link to="/register" className="rounded-md bg-binding px-3 py-1.5 font-medium text-binding-ink hover:bg-binding-strong">Create account</Link>
              </div>
            )}
            <button className="-mr-2 p-2 lg:hidden" onClick={() => setOpen(!open)} aria-label="Menu" aria-expanded={open}>
              {open ? <X className="size-5" /> : <Menu className="size-5" />}
            </button>
          </div>
        </div>
        {open && (
          <nav className="border-t border-rule px-4 py-3 lg:hidden" onClick={() => setOpen(false)}>
            {links.map(({ to, label, end }) => (
              <NavLink key={to} to={to} end={end} className={mobileCls}>{label}</NavLink>
            ))}
            {user ? (
              <button onClick={logout} className="block w-full rounded-md px-3 py-2.5 text-left text-[15px] text-ink-soft">Log out</button>
            ) : (
              <NavLink to="/login" className={mobileCls}>Log in or create an account</NavLink>
            )}
          </nav>
        )}
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 sm:py-14">
        <Outlet />
      </main>

      <footer className="mx-auto w-full max-w-6xl border-t border-rule px-4 py-6 text-[13px] text-ink-faint sm:px-6">
        CapSense gives you a starting point. Your adviser and panel have the final say on your title and manuscript.
      </footer>

      {showTour && <WelcomeTour onClose={() => recordProgress("tour_seen")} />}

      <div className="pointer-events-none fixed inset-x-0 bottom-5 z-50 flex flex-col items-center gap-2 px-4" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={cx("rise pointer-events-auto rounded-md px-4 py-2.5 text-sm shadow-lg", t.tone === "error" ? "bg-redpen text-white" : "bg-ink text-paper")}>
            {t.message}
          </div>
        ))}
      </div>
    </div>
  );
}
