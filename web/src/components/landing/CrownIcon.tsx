export function CrownIcon({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M3 18h18v2H3v-2zm1.5-3 2.2-6.5 3.3 4 3-5.5 3 5.5 3.3-4L19.5 15H4.5z"
        fill="url(#crown-gradient)"
        stroke="#c2410c"
        strokeWidth="0.75"
        strokeLinejoin="round"
      />
      <circle cx="5.5" cy="8" r="1.1" fill="#f59e0b" />
      <circle cx="12" cy="5.5" r="1.2" fill="#f59e0b" />
      <circle cx="18.5" cy="8" r="1.1" fill="#f59e0b" />
      <defs>
        <linearGradient id="crown-gradient" x1="3" y1="6" x2="21" y2="18" gradientUnits="userSpaceOnUse">
          <stop stopColor="#fbbf24" />
          <stop offset="0.5" stopColor="#f59e0b" />
          <stop offset="1" stopColor="#ea580c" />
        </linearGradient>
      </defs>
    </svg>
  );
}
