import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import { load, save } from "./storage";

const AppContext = createContext(null);

/** Session (user + AI key status), form options, the chosen engine, and toasts. */
export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ai, setAi] = useState(null); // {provider, model, masked_key, remember} | null
  const [progress, setProgress] = useState(null); // onboarding checklist + tour state
  const [meta, setMeta] = useState(null);
  const [ready, setReady] = useState(false);
  const [preferAi, setPreferAi] = useState(() => load("capsense.preferAi", true));
  const [toasts, setToasts] = useState([]);

  const applySession = useCallback((data) => {
    setUser(data.user ?? null);
    setAi(data.ai ?? null);
    setProgress(data.progress ?? null);
  }, []);

  const refresh = useCallback(async () => {
    try {
      applySession(await api.get("/auth/me"));
    } catch {
      /* keep current state */
    }
  }, [applySession]);

  /** Record an onboarding action: tour_seen, tour_reset, dismiss_checklist, restore_checklist. */
  const recordProgress = useCallback(async (action) => {
    try {
      setProgress((await api.post("/progress", { action })).progress);
    } catch {
      /* not critical */
    }
  }, []);

  useEffect(() => {
    Promise.all([api.get("/auth/me"), api.get("/meta")])
      .then(([session, metaData]) => {
        applySession(session);
        setMeta(metaData);
      })
      .catch(() => setMeta(null))
      .finally(() => setReady(true));
  }, [applySession]);

  const toast = useCallback((message, tone = "success") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((list) => [...list, { id, message, tone }]);
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), 3500);
  }, []);

  const setEnginePreference = useCallback((value) => {
    setPreferAi(value);
    save("capsense.preferAi", value);
  }, []);

  // The engine requests should use: AI only when the user has a key and wants it.
  const engine = ai && preferAi ? "ai" : "template";

  const value = useMemo(
    () => ({ user, ai, progress, meta, ready, engine, preferAi, setEnginePreference, refresh, recordProgress, applySession, setAi, toast, toasts }),
    [user, ai, progress, meta, ready, engine, preferAi, setEnginePreference, refresh, recordProgress, applySession, toast, toasts],
  );
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  return useContext(AppContext);
}
