import { useEffect, useState } from "react";
import { avatarImageUrl, avatarPalette, personInitials } from "../lib/avatars";

export function Avatar({
  name,
  photoURL,
  size = "md",
  className = "",
}: {
  name: string;
  photoURL?: string | null;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}) {
  const sizes = {
    sm: "h-9 w-9 text-[11px]",
    md: "h-11 w-11 text-xs",
    lg: "h-14 w-14 text-sm",
    xl: "h-20 w-20 text-base",
  };
  const [failed, setFailed] = useState(false);
  const src = photoURL && !failed ? photoURL : avatarImageUrl(name, size);

  useEffect(() => {
    setFailed(false);
  }, [name, photoURL]);

  if ((photoURL && failed) || (!photoURL && failed)) {
    const [from, to] = avatarPalette(name);
    const initials = personInitials(name);
    return (
      <div
        className={`grid shrink-0 place-items-center rounded-full font-semibold tracking-tight text-white ring-1 ring-subtle ${sizes[size]} ${className}`}
        style={{ background: `linear-gradient(145deg, ${from} 0%, ${to} 100%)` }}
        aria-hidden
      >
        {initials}
      </div>
    );
  }

  return (
    <img
      src={src}
      alt=""
      width={size === "sm" ? 36 : size === "md" ? 44 : size === "lg" ? 56 : 80}
      height={size === "sm" ? 36 : size === "md" ? 44 : size === "lg" ? 56 : 80}
      className={`shrink-0 rounded-full object-cover ring-1 ring-subtle ${sizes[size]} ${className}`}
      onError={() => setFailed(true)}
      aria-hidden
    />
  );
}
