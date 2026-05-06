import { useEffect, useRef, useState } from 'react';

/**
 * Animate number toward target (ease-out).
 * @param {number} target
 * @param {number} [durationMs]
 */
export function useCountUp(target, durationMs = 600) {
  const valueRef = useRef(target);
  const [value, setValue] = useState(target);

  useEffect(() => {
    const from = valueRef.current;
    const start = performance.now();
    const delta = target - from;
    let raf = 0;
    const tick = (now) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - (1 - t) ** 2;
      const next = from + delta * eased;
      valueRef.current = next;
      setValue(next);
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs]);

  return value;
}
