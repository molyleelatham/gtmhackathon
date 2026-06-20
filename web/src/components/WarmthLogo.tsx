const LOGO_SRC = "/brand/warmth-app-icon.png";

const sizeClasses = {
  sm: "h-9 w-9 rounded-xl",
  md: "h-14 w-14 rounded-2xl",
  lg: "h-16 w-16 rounded-2xl",
  xl: "h-20 w-20 rounded-3xl",
} as const;

interface WarmthLogoProps {
  size?: keyof typeof sizeClasses;
  className?: string;
  alt?: string;
}

/** Warmth app mark — same asset as the iOS App Icon. */
export function WarmthLogo({ size = "sm", className = "", alt = "Warmth" }: WarmthLogoProps) {
  return (
    <img
      src={LOGO_SRC}
      alt={alt}
      className={`object-cover shadow-glass ${sizeClasses[size]} ${className}`}
    />
  );
}
