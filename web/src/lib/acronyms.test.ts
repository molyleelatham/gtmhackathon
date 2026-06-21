import { describe, expect, it } from "vitest";
import { ACRONYM_PATTERN, ACRONYMS } from "./acronyms";

describe("acronyms", () => {
  it("defines expected acronym keys", () => {
    expect(ACRONYMS.ICP.full).toBe("Ideal Customer Profile");
    expect(ACRONYMS.GTM.full).toBe("Go-To-Market");
  });

  it("pattern matches acronym tokens in text", () => {
    const matches = "Our ICP and GTM stack".match(ACRONYM_PATTERN);
    expect(matches).toContain("ICP");
    expect(matches).toContain("GTM");
  });
});
