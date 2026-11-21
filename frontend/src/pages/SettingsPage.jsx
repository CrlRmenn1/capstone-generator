import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { api } from "../api";
import { useApp } from "../app-context";
import { Alert, Button, cx, PageHeader } from "../components/ui";

export default function SettingsPage() {
  const { meta, ai, setAi, toast } = useApp();
  const providers = meta?.providers || [];
  const [provider, setProvider] = useState(ai?.provider || "claude");
  const info = providers.find((p) => p.key === provider);
  const [model, setModel] = useState(ai?.model || info?.default_model || "");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [remember, setRemember] = useState(ai?.remember ?? false);
  const [busy, setBusy] = useState(null);
  const [result, setResult] = useState(null);
  const sameProvider = ai && ai.provider === provider;

  function chooseProvider(key) {
    setProvider(key);
    setModel(ai?.provider === key ? ai.model : providers.find((p) => p.key === key)?.default_model || "");
    setResult(null);
  }

  async function saveSettings(e) {
    e.preventDefault();
    setBusy("save");
    setResult(null);
    try {
      const data = await api.put("/settings/ai", { provider, model, api_key: apiKey, remember });
      setAi(data.ai);
      setApiKey("");
      toast("AI settings saved.");
      setResult({ tone: "info", message: "Saved. Press Test connection to check that the key works." });
    } catch (err) {
      setResult({ tone: "error", message: err.message });
    } finally {
      setBusy(null);
    }
  }

  async function test() {
    setBusy("test");
    setResult(null);
    try {
      setResult({ tone: "success", message: (await api.post("/settings/ai/test")).message });
    } catch (err) {
      setResult({ tone: "error", message: err.message });
    } finally {
      setBusy(null);
    }
  }

  async function remove() {
    if (!window.confirm("Remove your API key from CapSense?")) return;
    setBusy("remove");
    try {
      await api.del("/settings/ai");
      setAi(null);
      setResult(null);
      toast("API key removed. CapSense now uses the built-in engine.");
    } catch (err) {
      toast(err.message, "error");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="max-w-2xl">
      <PageHeader
        title="AI settings"
        description="CapSense works without AI. If you want more varied titles and fuller Chapter 1 drafts, connect your own API key. Requests are billed to your account with that provider, never to anyone else's."
      />

      {ai && (
        <div className="mb-10 flex flex-wrap items-center gap-x-6 gap-y-3 border-y border-rule py-4">
          <div className="min-w-0 flex-1 text-sm">
            <p className="font-medium">Connected to {providers.find((p) => p.key === ai.provider)?.label}</p>
            <p className="mt-0.5 text-ink-soft">
              Model {ai.model}, key ending {ai.masked_key.slice(-4)}, {ai.remember ? "remembered on the server (encrypted)" : "kept until you log out"}.
            </p>
          </div>
          <div className="flex gap-1">
            <Button variant="secondary" size="sm" loading={busy === "test"} onClick={test}>Test connection</Button>
            <Button variant="danger" size="sm" loading={busy === "remove"} onClick={remove}>Remove key</Button>
          </div>
        </div>
      )}

      <form onSubmit={saveSettings} className="space-y-8">
        <fieldset>
          <legend className="label">Provider</legend>
          <div className="divide-y divide-rule rounded-md border border-rule bg-paper">
            {providers.map((p) => (
              <label key={p.key} className="flex cursor-pointer items-center gap-3 px-4 py-3">
                <input type="radio" name="provider" className="size-4 accent-[var(--binding)]" checked={provider === p.key} onChange={() => chooseProvider(p.key)} />
                <span className="flex-1 text-[15px]">{p.label}</span>
                {ai?.provider === p.key && <span className="text-xs text-binding">In use</span>}
              </label>
            ))}
          </div>
        </fieldset>

        <label className="block">
          <span className="label">Model</span>
          <input className="input" value={model} onChange={(e) => setModel(e.target.value)} placeholder={info?.default_model} spellCheck={false} />
          <span className="mt-1.5 block text-[13px] text-ink-faint">Leave as {info?.default_model}, or enter any model your key can use.</span>
        </label>

        <label className="block">
          <span className="label">API key</span>
          <div className="relative">
            <input
              className="input pr-10"
              type={showKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={sameProvider ? "Saved. Leave blank to keep the current key." : `Starts with ${info?.key_hint?.replace("...", "")}`}
              autoComplete="off"
              spellCheck={false}
            />
            <button type="button" onClick={() => setShowKey(!showKey)} className="absolute inset-y-0 right-0 px-3 text-ink-faint hover:text-ink" aria-label={showKey ? "Hide key" : "Show key"}>
              {showKey ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
            </button>
          </div>
          {info?.key_url && (
            <a href={info.key_url} target="_blank" rel="noreferrer" className="mt-1.5 inline-block text-[13px] text-binding underline-offset-2 hover:underline">
              Get an API key from {info.label}
            </a>
          )}
        </label>

        <label className="flex cursor-pointer items-start gap-3">
          <input type="checkbox" className="mt-1 size-4 accent-[var(--binding)]" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          <span className="text-sm">
            <span className="font-medium">Remember my key on this server</span>
            <span className="mt-0.5 block text-ink-soft">It's stored encrypted so you don't have to paste it again. Unchecked, the key is forgotten when you log out.</span>
          </span>
        </label>

        {result && <Alert tone={result.tone}>{result.message}</Alert>}

        <div className={cx("flex border-t border-rule pt-6", "justify-end")}>
          <Button type="submit" loading={busy === "save"}>{ai ? "Save changes" : "Connect AI"}</Button>
        </div>
      </form>
    </div>
  );
}
