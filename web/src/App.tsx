import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { RequireAuth } from "./components/RequireAuth";
import { Dashboard } from "./pages/Dashboard";
import { Events } from "./pages/Events";
import { PreMeet } from "./pages/PreMeet";
import { Connections } from "./pages/Connections";
import { ConnectionDetail } from "./pages/ConnectionDetail";
import { Community } from "./pages/Community";
import { Settings } from "./pages/Settings";
import { Leads } from "./pages/Leads";
import { Pipeline } from "./pages/Pipeline";
import { SignIn } from "./pages/SignIn";
import { Landing } from "./pages/Landing";
import { useAuth } from "./lib/auth";
import { BackgroundMouseGlow } from "./components/BackgroundMouseGlow";

export default function App() {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div className="relative min-h-screen">
        <BackgroundMouseGlow />
        <div className="relative z-[1] flex min-h-screen items-center justify-center text-sm text-ink-faint">
          Loading…
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen">
      <BackgroundMouseGlow />
      <div className="relative z-[1]">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/sign-in" element={<SignIn />} />
          <Route element={<RequireAuth />}>
            <Route path="/app" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="events" element={<Events />} />
              <Route path="events/:eventId" element={<PreMeet />} />
              <Route path="connections" element={<Connections />} />
              <Route path="connections/:connectionId" element={<ConnectionDetail />} />
              <Route path="leads" element={<Leads />} />
              <Route path="pipeline" element={<Pipeline />} />
              <Route path="community" element={<Community />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Route>
        </Routes>
      </div>
    </div>
  );
}
