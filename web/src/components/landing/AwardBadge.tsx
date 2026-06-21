type AwardBadgeSize = "sm" | "md" | "lg";

const sizeClasses: Record<AwardBadgeSize, string> = {
  sm: "gap-1.5 px-3 py-1.5 text-xs",
  md: "gap-2 px-4 py-2 text-sm sm:text-base",
  lg: "gap-2.5 px-5 py-2.5 text-base font-bold sm:px-6 sm:py-3 sm:text-lg",
};

export function AwardBadge({
  label,
  size = "sm",
  featured = false,
}: {
  label: string;
  size?: AwardBadgeSize;
  featured?: boolean;
}) {
  return (
    <span
      className={`glass-pill inline-flex items-center border-orange/25 bg-orange/10 font-semibold text-ember ${sizeClasses[size]} ${
        featured ? "border-2 border-flame/40 bg-gradient-to-r from-orange/15 to-flame/10 shadow-glass" : ""
      }`}
    >
      <span className={size === "lg" ? "text-xl sm:text-2xl" : size === "md" ? "text-base" : ""} aria-hidden="true">
        🏆
      </span>
      {label}
    </span>
  );
}
