import { useState } from "react";
import { companyColor, companyLogoUrl } from "../lib/avatars";

/** Small company mark — shows logo image or full company name (not cryptic initials). */
export function CompanyLogo({
  company,
  size = "sm",
}: {
  company: string;
  size?: "sm" | "md";
}) {
  const [err, setErr] = useState(false);
  const url = companyLogoUrl(company);
  const imgDim = size === "md" ? "h-7 w-7" : "h-5 w-5";

  if (url && !err) {
    return (
      <img
        src={url}
        alt={`${company} logo`}
        onError={() => setErr(true)}
        className={`shrink-0 rounded object-contain ${imgDim}`}
        title={company}
      />
    );
  }

  return (
    <span
      className={`truncate font-medium text-ink-muted ${size === "md" ? "text-sm" : "text-[11px]"}`}
      title={company}
      style={{ color: companyColor(company) }}
    >
      {company}
    </span>
  );
}
