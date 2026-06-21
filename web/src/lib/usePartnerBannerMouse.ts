import { useCallback, useRef, useState } from "react";

export function usePartnerBannerMouse() {
  const ref = useRef<HTMLDivElement>(null);
  const [hovering, setHovering] = useState(false);

  const onMouseMove = useCallback((event: React.MouseEvent<HTMLDivElement>) => {
    const element = ref.current;
    if (!element) return;

    const { left, top } = element.getBoundingClientRect();
    element.style.setProperty("--mouse-x", `${event.clientX - left}px`);
    element.style.setProperty("--mouse-y", `${event.clientY - top}px`);
  }, []);

  return {
    ref,
    hovering,
    onMouseEnter: () => setHovering(true),
    onMouseLeave: () => setHovering(false),
    onMouseMove,
  };
}
