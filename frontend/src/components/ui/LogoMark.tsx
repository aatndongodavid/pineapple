// frontend/src/components/ui/LogoMark.tsx

import React from 'react';

interface LogoMarkProps {
  size?: number;
  className?: string;
  variant?: 'color' | 'monochrome';
}

export const LogoMark: React.FC<LogoMarkProps> = ({
  size = 32,
  className = '',
  variant = 'color',
}) => {
  const isMonochrome = variant === 'monochrome';

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Logo Pineapple"
    >
      {/* Crown / Leaves */}
      <path
        d="M50 8C46 18 42 28 40 38C45 35 50 32 50 32C50 32 55 35 60 38C58 28 54 18 50 8Z"
        fill={isMonochrome ? 'currentColor' : '#16A34A'}
      />
      <path
        d="M36 15C34 24 34 34 36 42C40 38 45 36 45 36C42 28 39 20 36 15Z"
        fill={isMonochrome ? 'currentColor' : '#15803D'}
      />
      <path
        d="M64 15C66 24 66 34 64 42C60 38 55 36 55 36C58 28 61 20 64 15Z"
        fill={isMonochrome ? 'currentColor' : '#15803D'}
      />

      {/* Pineapple Body (Diamond / Geometric shape with smooth corners) */}
      <path
        d="M50 34C32 34 22 48 22 65C22 82 34 94 50 94C66 94 78 82 78 65C78 48 68 34 50 34Z"
        fill={isMonochrome ? 'currentColor' : '#F97316'}
      />

      {/* Facet / Reflet clair */}
      <path
        d="M50 34C38 34 28 44 24 58C30 52 40 46 50 46C60 46 70 52 76 58C72 44 62 34 50 34Z"
        fill={isMonochrome ? 'currentColor' : '#FDBA74'}
        opacity={isMonochrome ? 0.3 : 0.85}
      />
    </svg>
  );
};
