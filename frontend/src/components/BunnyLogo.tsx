export function BunnyLogo({ size = 56 }: { size?: number }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 100 130"
      width={size}
      height={size * 1.3}
      aria-label="Bunny logo"
    >
      {/* ── Left ear (long floppy) ── */}
      <ellipse cx="34" cy="30" rx="11" ry="30" fill="white" stroke="black" strokeWidth="2"
        transform="rotate(-12 34 30)" />
      <ellipse cx="34" cy="30" rx="6"  ry="23" fill="#e0e0e0"
        transform="rotate(-12 34 30)" />

      {/* ── Right ear (long floppy) ── */}
      <ellipse cx="66" cy="30" rx="11" ry="30" fill="white" stroke="black" strokeWidth="2"
        transform="rotate(12 66 30)" />
      <ellipse cx="66" cy="30" rx="6"  ry="23" fill="#e0e0e0"
        transform="rotate(12 66 30)" />

      {/* ── Head ── */}
      <ellipse cx="50" cy="85" rx="37" ry="34" fill="white" stroke="black" strokeWidth="2" />

      {/* ── Eyes ── */}
      <circle cx="38" cy="79" r="5"   fill="black" />
      <circle cx="62" cy="79" r="5"   fill="black" />
      {/* shine */}
      <circle cx="40" cy="77" r="1.8" fill="white" />
      <circle cx="64" cy="77" r="1.8" fill="white" />

      {/* ── Blush (subtle gray) ── */}
      <ellipse cx="28" cy="89" rx="8" ry="5" fill="#c0c0c0" opacity="0.5" />
      <ellipse cx="72" cy="89" rx="8" ry="5" fill="#c0c0c0" opacity="0.5" />

      {/* ── Nose ── */}
      <ellipse cx="50" cy="91" rx="4" ry="3" fill="#555" />

      {/* ── Mouth ── */}
      <path d="M44 96 Q50 103 56 96"
        stroke="#333" strokeWidth="1.8" fill="none" strokeLinecap="round" />

      {/* ── Tiny front paws peeking at bottom ── */}
      <ellipse cx="38" cy="118" rx="10" ry="7" fill="white" stroke="black" strokeWidth="2" />
      <ellipse cx="62" cy="118" rx="10" ry="7" fill="white" stroke="black" strokeWidth="2" />
    </svg>
  );
}
