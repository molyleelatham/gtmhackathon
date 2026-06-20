import { useState } from "react";
import { avatarUrl } from "../lib/avatars";

export function Avatar({
  name,
  size = "md",
  className = "",
}: {
  name: string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}) {
  const [err, setErr] = useState(false);
  const sizes = {
    sm: "h-9 w-9 text-xs",
    md: "h-12 w-12 text-sm",
    lg: "h-16 w-16 text-base",
    xl: "h-24 w-24 text-xl",
  };
  const px = { sm: 36, md: 48, lg: 64, xl: 96 }[size];
  const initial = name.charAt(0).toUpperCase();

  if (err) {
    return (
      <div
        className={`grid shrink-0 place-items-center rounded-full bg-gradient-to-br from-orange to-red-brand font-bold text-white ring-2 ring-white ${sizes[size]} ${className}`}
      >
        {initial}
      </div>
    );
  }

  return (
    <img
      src={avatarUrl(name, px * 2)}
      alt={name}
      onError={() => setErr(true)}
      className={`shrink-0 rounded-full object-cover ring-2 ring-white shadow-sm ${sizes[size]} ${className}`}
    />
  );
}
