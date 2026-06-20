/** Deterministic avatar + company logo helpers for demo data. */

const COMPANY_DOMAINS: Record<string, string> = {
  RevLoop: "revloop.com",
  Payflow: "payflow.io",
  Stackframe: "stackframe.dev",
  "Northstar SaaS": "northstarsaas.com",
  "Bright Funnel": "brightfunnel.com",
  Cohorted: "cohorted.com",
  Ledgerly: "ledgerly.com",
  Cloudmint: "cloudmint.io",
  Dataweave: "dataweave.com",
  Quotient: "quotient.co",
  Gridline: "gridline.io",
  Stitchwork: "stitchwork.com",
  Pulsegrid: "pulsegrid.com",
  Vela: "vela.com",
  Glide: "glide.com",
  Lumen: "lumen.dev",
  Cordial: "cordial.com",
  Northwind: "northwind.com",
};

const COMPANY_COLORS: Record<string, string> = {
  RevLoop: "#ea580c",
  Payflow: "#dc2626",
  Stackframe: "#2563eb",
  "Northstar SaaS": "#7c3aed",
  Ledgerly: "#059669",
  Cloudmint: "#0891b2",
  Dataweave: "#d97706",
};

const AVATAR_PALETTES = [
  ["#1c1109", "#ea580c"],
  ["#292524", "#dc2626"],
  ["#44403c", "#f97316"],
  ["#1c1917", "#c2410c"],
  ["#292524", "#d97706"],
];

/** Dicebear 7.x professional headshot style — deterministic from name. */
export const AVATAR_STYLE = "personas";

const AVATAR_PX: Record<"sm" | "md" | "lg" | "xl", number> = {
  sm: 36,
  md: 44,
  lg: 56,
  xl: 80,
};

export function avatarImageUrl(
  name: string,
  size: keyof typeof AVATAR_PX | number = 128,
): string {
  const px = typeof size === "number" ? size : AVATAR_PX[size];
  const seed = encodeURIComponent(name.trim());
  return `https://api.dicebear.com/7.x/${AVATAR_STYLE}/png?seed=${seed}&size=${px * 2}&backgroundColor=2a1c12`;
}

/** Two-letter initials for a professional conference look. */
export function personInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

export function avatarPalette(name: string): [string, string] {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  const palette = AVATAR_PALETTES[Math.abs(hash) % AVATAR_PALETTES.length];
  return [palette[0], palette[1]];
}

/** Company logo via Clearbit with initials fallback handled in component. */
export function companyLogoUrl(company: string): string | null {
  const domain = COMPANY_DOMAINS[company];
  return domain ? `https://logo.clearbit.com/${domain}` : null;
}

export function companyColor(company: string): string {
  return COMPANY_COLORS[company] ?? "#78716c";
}

export function companyInitials(company: string): string {
  return company
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}
