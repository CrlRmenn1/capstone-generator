import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { api } from "./api";
import { useApp } from "./app-context";

/** Saving titles and developing them into a Chapter 1 draft, shared by the results and Saved pages. */
export default function useTitleActions() {
  const { user, engine, toast, refresh } = useApp();
  const navigate = useNavigate();
  const [bookmarks, setBookmarks] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const [developing, setDeveloping] = useState(null); // title being developed

  const reload = useCallback(async () => {
    try {
      setBookmarks(user ? (await api.get("/bookmarks")).bookmarks : []);
    } catch {
      /* ignore */
    } finally {
      setLoaded(true);
    }
  }, [user]);

  useEffect(() => {
    reload();
  }, [reload]);

  const requireLogin = (what) => {
    toast(`Log in to ${what}.`);
    navigate("/login", { state: { next: window.location.pathname } });
  };

  const bookmarkFor = (title) => bookmarks.find((b) => b.title === title);

  async function toggleSave(item) {
    if (!user) return requireLogin("save titles");
    const existing = bookmarkFor(item.title);
    try {
      if (existing) {
        await api.del(`/bookmarks/${existing.id}`);
        setBookmarks((list) => list.filter((b) => b.id !== existing.id));
        toast("Removed from saved titles.");
      } else {
        const { bookmark } = await api.post("/bookmarks", { title: item.title, source: item.source, payload: item });
        setBookmarks((list) => [bookmark, ...list]);
        toast("Title saved.");
        refresh(); // updates the getting-started checklist
      }
    } catch (err) {
      toast(err.message, "error");
    }
  }

  async function develop(item, engineOverride) {
    if (!user) return requireLogin("develop a Chapter 1 draft");
    const useEngine = engineOverride || engine;
    const context = item.context && Object.keys(item.context).length ? item.context : { domain: item.domain, area: item.area };
    setDeveloping(item.title);
    try {
      const { outline } = await api.post("/outlines", {
        title: item.title,
        system_name: item.system_name || "",
        context,
        engine: useEngine,
      });
      toast("Chapter 1 draft created.");
      refresh();
      navigate(`/outlines/${outline.id}`);
    } catch (err) {
      if (err.fallback && useEngine === "ai" && window.confirm(`${err.message}\n\nWrite the draft with default mode instead?`)) {
        return develop(item, "template");
      }
      toast(err.message, "error");
    } finally {
      setDeveloping(null);
    }
  }

  return { bookmarks, loaded, setBookmarks, isSaved: (t) => Boolean(bookmarkFor(t)), toggleSave, develop, developing, reload };
}
