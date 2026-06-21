import { afterEach, describe, expect, it, vi } from "vitest";
import { setAuthTokenGetter } from "./api";

describe("api client", () => {
  afterEach(() => {
    setAuthTokenGetter(null);
    vi.restoreAllMocks();
  });

  it("calls dashboard endpoint with auth header when token getter set", async () => {
    setAuthTokenGetter(async () => "test-token");
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ events: 1, connections: 2 }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { api } = await import("./api");
    const summary = await api.dashboard();
    expect(summary.events).toBe(1);
    expect(fetchMock).toHaveBeenCalled();
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/api/v1/dashboard");
    expect(init?.headers?.Authorization).toBe("Bearer test-token");
  });

  it("throws on non-ok responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500, text: async () => "fail" }));
    const { api } = await import("./api");
    await expect(api.health()).rejects.toThrow();
  });
});
