import { WarmthLogo } from "../WarmthLogo";

function ChromeMark({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <img
      src="/logos/chrome.png"
      alt=""
      className={`${className} object-contain`}
      aria-hidden="true"
    />
  );
}

function AppleMark({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M16.8 12.7c-.03-2.9 2.4-4.3 2.5-4.4-1.4-2-3.5-2.3-4.2-2.3-1.8-.2-3.5 1.1-4.4 1.1-.9 0-2.3-1.1-3.8-1.1-1.9.03-3.7 1.1-4.7 2.8-2 3.5-.5 8.7 1.4 11.5 1 1.4 2.1 3 3.6 2.9 1.4-.1 2-1 3.7-1 1.7 0 2.2 1 3.7.9 1.5-.1 2.5-1.4 3.4-2.8 1.1-1.5 1.5-3 1.5-3.1-.03-.01-3-1.2-3-4.5Z" />
      <path d="M14.5 4.8c.8-1 1.3-2.3 1.1-3.7-1.1.1-2.4.7-3.2 1.6-.7.8-1.4 2.1-1.2 3.3 1.3.1 2.6-.6 3.3-1.2Z" />
    </svg>
  );
}

interface PlatformAppMarkProps {
  platform: "web" | "ios";
}

export function PlatformAppMark({ platform }: PlatformAppMarkProps) {
  const PlatformIcon = platform === "web" ? ChromeMark : AppleMark;

  return (
    <div className="relative mx-auto w-fit">
      <WarmthLogo size="md" className="shadow-glass-lg" />
      <span
        className="absolute -bottom-1 -right-1 flex h-8 w-8 items-center justify-center rounded-full border border-white/90 bg-white/95 text-ink-900 shadow-glass"
        aria-hidden="true"
      >
        <PlatformIcon className={platform === "web" ? "h-5 w-5" : "h-4 w-4"} />
      </span>
    </div>
  );
}
