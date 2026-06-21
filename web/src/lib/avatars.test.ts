import { describe, expect, it } from "vitest";
import {
  avatarImageUrl,
  avatarPalette,
  companyInitials,
  companyLogoUrl,
  personInitials,
} from "./avatars";

describe("avatars", () => {
  it("generates deterministic initials", () => {
    expect(personInitials("Maya Chen")).toBe("MC");
    expect(personInitials("Alex")).toBe("AL");
  });

  it("builds dicebear avatar URLs", () => {
    const url = avatarImageUrl("Jane Doe", 64);
    expect(url).toContain("dicebear.com");
    expect(url).toContain("Jane");
  });

  it("returns company logo for known companies", () => {
    expect(companyLogoUrl("RevLoop")).toContain("revloop.com");
    expect(companyLogoUrl("Unknown Co")).toBeNull();
  });

  it("derives company initials", () => {
    expect(companyInitials("North Wind Labs")).toBe("NW");
  });

  it("returns stable palette for a name", () => {
    const a = avatarPalette("Maya");
    const b = avatarPalette("Maya");
    expect(a).toEqual(b);
  });
});
