import { useState } from "react";
import { companyColor, companyInitials, companyLogoUrl } from "../lib/avatars";

export function CompanyLogo({
  company,
  size = "sm",
}: {
  company: string;
  size?: "sm" | "md";
}) {
  const [err, setErr] = useState(false);
  const url = companyLogoUrl(company);
  const dim = size === "md" ? "h-8 w-8 text-xs" : "h-6 w-6 text-[10px]";

  if (!url || err) {
    return (
      <div
        className={`grid shrink-0 place-items-center rounded-lg font-bold text-white ${dim}`}
        style={{ backgroundColor: companyColor(company) }}
        title={company}
      >
        {companyInitials(company)}
      </div>
    );
  }

  return (
    <img
      src={url}
      alt={`${company} logo`}
      onError={() => setErr(true)}
      className={`shrink-0 rounded-lg object-contain bg-white p-0.5 ring-1 ring-black/10 ${dim}`}
      title={company}
    />
  );
}
