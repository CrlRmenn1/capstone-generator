// Browser storage helpers. Storage can be unavailable (private mode, blocked cookies),
// so every access is wrapped and the app works without it.

export function load(key, fallback, store = "local") {
  try {
    const raw = (store === "session" ? sessionStorage : localStorage).getItem(key);
    return raw === null ? fallback : JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function save(key, value, store = "local") {
  try {
    (store === "session" ? sessionStorage : localStorage).setItem(key, JSON.stringify(value));
  } catch {
    /* ignore */
  }
}
