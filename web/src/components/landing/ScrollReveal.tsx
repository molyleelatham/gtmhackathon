import type { CSSProperties, ElementType, ReactNode } from "react";
import { useScrollReveal } from "../../lib/useScrollReveal";

export type ScrollRevealVariant = "up" | "fade" | "scale" | "blur" | "up-scale";

const variantClass: Record<ScrollRevealVariant, string> = {
  up: "scroll-reveal-up",
  fade: "scroll-reveal-fade",
  scale: "scroll-reveal-scale",
  blur: "scroll-reveal-blur",
  "up-scale": "scroll-reveal-up-scale",
};

interface ScrollRevealProps {
  children: ReactNode;
  className?: string;
  /** Stagger delay in ms */
  delay?: number;
  variant?: ScrollRevealVariant;
  eager?: boolean;
  as?: ElementType;
  style?: CSSProperties;
}

export function ScrollReveal({
  children,
  className = "",
  delay = 0,
  variant = "up",
  eager = false,
  as: Tag = "div",
  style,
}: ScrollRevealProps) {
  const { ref, visible } = useScrollReveal<HTMLElement>({ eager });

  return (
    <Tag
      ref={ref}
      className={`scroll-reveal ${variantClass[variant]} ${visible ? "scroll-reveal-visible" : ""} ${className}`}
      style={{ ...style, transitionDelay: `${delay}ms` }}
    >
      {children}
    </Tag>
  );
}
