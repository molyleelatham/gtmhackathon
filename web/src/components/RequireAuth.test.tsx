import { describe, expect, it, vi } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { render, screen } from "@testing-library/react";
import { RequireAuth } from "../components/RequireAuth";

vi.mock("../lib/auth", () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from "../lib/auth";

describe("RequireAuth", () => {
  it("redirects unauthenticated users to sign-in", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: null,
      loading: false,
      signInWithGoogle: vi.fn(),
      signOut: vi.fn(),
      getIdToken: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <Routes>
          <Route element={<RequireAuth />}>
            <Route path="/app" element={<div>Protected</div>} />
          </Route>
          <Route path="/sign-in" element={<div>Sign In Page</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Sign In Page")).toBeInTheDocument();
  });

  it("renders outlet when authenticated", () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { uid: "u1", displayName: "Test", email: "t@test.com", photoURL: null },
      loading: false,
      signInWithGoogle: vi.fn(),
      signOut: vi.fn(),
      getIdToken: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={["/app"]}>
        <Routes>
          <Route element={<RequireAuth />}>
            <Route path="/app" element={<div>Protected</div>} />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("Protected")).toBeInTheDocument();
  });
});
