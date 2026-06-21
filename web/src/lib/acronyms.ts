export const ACRONYMS = {
  ICP: { full: "Ideal Customer Profile" },
  GTM: { full: "Go-To-Market" },
  CRM: { full: "Customer Relationship Management" },
  MCP: { full: "Model Context Protocol" },
  NLP: { full: "Natural Language Processing" },
  ML: { full: "Machine Learning" },
} as const;

export type AcronymKey = keyof typeof ACRONYMS;

const keys = Object.keys(ACRONYMS).sort((a, b) => b.length - a.length);

export const ACRONYM_PATTERN = new RegExp(
  `(${keys.map((key) => key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
  "g",
);
