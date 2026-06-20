import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Events } from "./pages/Events";
import { PreMeet } from "./pages/PreMeet";
import { Connections } from "./pages/Connections";
import { ConnectionDetail } from "./pages/ConnectionDetail";
import { Community } from "./pages/Community";
import { Settings } from "./pages/Settings";
import { SignIn } from "./pages/SignIn";
import { useAuth } from "./lib/auth";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-ink-faint">
        Loading…
      </div>
    );
  }

  if (!user) {
    return <SignIn />;
  }

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="events" element={<Events />} />
        <Route path="events/:eventId" element={<PreMeet />} />
        <Route path="connections" element={<Connections />} />
        <Route path="connections/:connectionId" element={<ConnectionDetail />} />
        <Route path="community" element={<Community />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
