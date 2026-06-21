import { describe, expect, it } from "vitest";
import { safeGmailComposeUrl } from "./safeUrl";

describe("safeGmailComposeUrl", () => {
  it("accepts valid Gmail compose URLs", () => {
    const url = safeGmailComposeUrl(
      "https://mail.google.com/mail/u/0/?view=cm&fs=1&to=test@example.com",
    );
    expect(url).toContain("mail.google.com");
  });

  it("rejects javascript URLs", () => {
    expect(safeGmailComposeUrl("javascript:alert(1)")).toBeNull();
  });

  it("rejects non-Gmail hosts", () => {
    expect(safeGmailComposeUrl("https://evil.com/phish")).toBeNull();
  });

  it("rejects http scheme", () => {
    expect(safeGmailComposeUrl("http://mail.google.com/mail")).toBeNull();
  });
});
