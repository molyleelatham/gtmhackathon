import { Routes, Route } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Events } from "./pages/Events";
import { PreMeet } from "./pages/PreMeet";
import { Connections } from "./pages/Connections";
import { ConnectionDetail } from "./pages/ConnectionDetail";
import { SignIn } from "./pages/SignIn";
import { useAuth } from "./lib/auth";

export default function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-sm text-gray-500">
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
      </Route>
    </Routes>
  );
}
