export function CortaLogo({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="relative inline-flex h-8 w-8 items-center justify-center flex-shrink-0">
        {/* Blue circle with white crescent cutout on the right - creates C shape */}
        <svg
          width="32"
          height="32"
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-8 w-8"
        >
          {/* Blue circle background */}
          <circle cx="16" cy="16" r="16" fill="#2563eb" />
          {/* White crescent cutout on the right side */}
          <path
            d="M 32 16 A 16 16 0 0 0 32 0 L 32 32 Z"
            fill="white"
          />
          <circle cx="20" cy="16" r="10" fill="#2563eb" />
        </svg>
      </div>
      <span className="text-lg font-bold text-slate-900">CORTA</span>
    </div>
  );
}

