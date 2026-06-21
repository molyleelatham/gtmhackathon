import { useEffect, useRef } from "react";

/** Soft cursor-following glow that sits behind all page content. */
export function BackgroundMouseGlow() {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const onMove = (event: MouseEvent) => {
      ref.current?.style.setProperty("--mouse-x", `${event.clientX}px`);
      ref.current?.style.setProperty("--mouse-y", `${event.clientY}px`);
    };

    window.addEventListener("mousemove", onMove, { passive: true });
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  return <div ref={ref} className="background-mouse-glow" aria-hidden="true" />;
}
