import { useEffect, useRef, useState, type RefObject } from "react";

interface UseScrollRevealOptions {
  /** Reveal immediately on mount (hero, nav). */
  eager?: boolean;
  threshold?: number;
  rootMargin?: string;
}

export function useScrollReveal<T extends HTMLElement = HTMLDivElement>(
  options: UseScrollRevealOptions = {},
): { ref: RefObject<T>; visible: boolean } {
  const { eager = false, threshold = 0.12, rootMargin = "0px 0px -6% 0px" } = options;
  const ref = useRef<T>(null);
  const [visible, setVisible] = useState(eager);

  useEffect(() => {
    if (eager) {
      setVisible(true);
      return;
    }

    const el = ref.current;
    if (!el) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setVisible(true);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold, rootMargin },
    );

    observer.observe(el);
    return () => observer.disconnect();
  }, [eager, threshold, rootMargin]);

  return { ref, visible };
}

/** Subtle parallax offset for hero elements (very light Apple-style depth). */
export function useScrollParallax(factor = 0.08): { ref: RefObject<HTMLDivElement>; offset: number } {
  const ref = useRef<HTMLDivElement>(null);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const el = ref.current;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const center = rect.top + rect.height / 2;
        const viewCenter = window.innerHeight / 2;
        setOffset((center - viewCenter) * factor);
      });
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
    };
  }, [factor]);

  return { ref, offset };
}
