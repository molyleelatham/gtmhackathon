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

/** Portrait photo URL (Dicebear — stable per name). */
export function avatarUrl(name: string, size = 128): string {
  const seed = encodeURIComponent(name.replace(/\s+/g, ""));
  return `https://api.dicebear.com/7.x/avataaars/png?seed=${seed}&size=${size}&backgroundColor=f97316,fb923c,fff7ed`;
}

/** Company logo via Clearbit with initials fallback handled in component. */
export function companyLogoUrl(company: string): string | null {
  const domain = COMPANY_DOMAINS[company];
  return domain ? `https://logo.clearbit.com/${domain}` : null;
}

export function companyColor(company: string): string {
  return COMPANY_COLORS[company] ?? "#f97316";
}

export function companyInitials(company: string): string {
  return company
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}
