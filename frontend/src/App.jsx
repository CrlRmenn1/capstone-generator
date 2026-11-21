import { Compass } from "lucide-react";
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from "react-router";
import { AppProvider, useApp } from "./app-context";
import Layout from "./components/Layout";
import { EmptyState, Spinner } from "./components/ui";
import AuthPage from "./pages/AuthPage";
import GeneratePage from "./pages/GeneratePage";
import GuidePage from "./pages/GuidePage";
import OutlineEditorPage from "./pages/OutlineEditorPage";
import OutlinesPage from "./pages/OutlinesPage";
import SavedPage from "./pages/SavedPage";
import SettingsPage from "./pages/SettingsPage";

function RequireAuth({ children }) {
  const { user, ready } = useApp();
  const location = useLocation();
  if (!ready) return <Spinner />;
  if (!user) return <Navigate to="/login" replace state={{ next: location.pathname }} />;
  return children;
}

function Routed() {
  const { ready } = useApp();
  if (!ready) return <Spinner label="Starting CapSense…" />;
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<GeneratePage />} />
        <Route path="login" element={<AuthPage mode="login" />} />
        <Route path="register" element={<AuthPage mode="register" />} />
        <Route path="saved" element={<RequireAuth><SavedPage /></RequireAuth>} />
        <Route path="outlines" element={<RequireAuth><OutlinesPage /></RequireAuth>} />
        <Route path="outlines/:id" element={<RequireAuth><OutlineEditorPage /></RequireAuth>} />
        <Route path="settings" element={<RequireAuth><SettingsPage /></RequireAuth>} />
        <Route path="guide" element={<GuidePage />} />
        <Route
          path="*"
          element={
            <EmptyState icon={Compass} title="Page not found" action={<Link to="/" className="font-semibold text-brand-600">Go home</Link>}>
              The page you're looking for doesn't exist.
            </EmptyState>
          }
        />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Routed />
      </AppProvider>
    </BrowserRouter>
  );
}
