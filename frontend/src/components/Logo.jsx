import React from 'react';

export const Logo = ({ size = 'default', variant = 'full' }) => {
  const sizes = {
    small: { width: 32, height: 32, fontSize: '14px' },
    default: { width: 40, height: 40, fontSize: '18px' },
    large: { width: 60, height: 60, fontSize: '24px' }
  };

  const { width, height, fontSize } = sizes[size];

  if (variant === 'icon') {
    return (
      <svg
        width={width}
        height={height}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="logo-icon"
      >
        {/* Background circle */}
        <circle cx="20" cy="20" r="18" fill="hsl(217, 18%, 10%)" />
        
        {/* M shape formed by network nodes */}
        <path
          d="M10 25 L10 15 L15 20 L20 15 L25 20 L30 15 L30 25"
          stroke="url(#gradient1)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        
        {/* Network nodes */}
        <circle cx="10" cy="15" r="2.5" fill="hsl(188, 94%, 43%)" />
        <circle cx="15" cy="20" r="2.5" fill="hsl(188, 94%, 43%)" />
        <circle cx="20" cy="15" r="2.5" fill="hsl(174, 100%, 48%)" className="animate-pulse" />
        <circle cx="25" cy="20" r="2.5" fill="hsl(188, 94%, 43%)" />
        <circle cx="30" cy="15" r="2.5" fill="hsl(188, 94%, 43%)" />
        
        {/* Connecting lines */}
        <line x1="10" y1="15" x2="15" y2="20" stroke="hsl(188, 94%, 43%)" strokeWidth="1" opacity="0.6" />
        <line x1="15" y1="20" x2="20" y2="15" stroke="hsl(188, 94%, 43%)" strokeWidth="1" opacity="0.6" />
        <line x1="20" y1="15" x2="25" y2="20" stroke="hsl(174, 100%, 48%)" strokeWidth="1" opacity="0.6" />
        <line x1="25" y1="20" x2="30" y2="15" stroke="hsl(188, 94%, 43%)" strokeWidth="1" opacity="0.6" />
        
        <defs>
          <linearGradient id="gradient1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="hsl(188, 94%, 43%)" />
            <stop offset="100%" stopColor="hsl(174, 100%, 48%)" />
          </linearGradient>
        </defs>
      </svg>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <svg
        width={width}
        height={height}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle cx="20" cy="20" r="18" fill="hsl(217, 18%, 10%)" />
        <path
          d="M10 25 L10 15 L15 20 L20 15 L25 20 L30 15 L30 25"
          stroke="url(#gradient2)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <circle cx="10" cy="15" r="2.5" fill="hsl(188, 94%, 43%)" />
        <circle cx="15" cy="20" r="2.5" fill="hsl(188, 94%, 43%)" />
        <circle cx="20" cy="15" r="2.5" fill="hsl(174, 100%, 48%)" className="animate-pulse" />
        <circle cx="25" cy="20" r="2.5" fill="hsl(188, 94%, 43%)" />
        <circle cx="30" cy="15" r="2.5" fill="hsl(188, 94%, 43%)" />
        <line x1="10" y1="15" x2="15" y2="20" stroke="hsl(188, 94%, 43%)" strokeWidth="1" opacity="0.6" />
        <line x1="15" y1="20" x2="20" y2="15" stroke="hsl(188, 94%, 43%)" strokeWidth="1" opacity="0.6" />
        <line x1="20" y1="15" x2="25" y2="20" stroke="hsl(174, 100%, 48%)" strokeWidth="1" opacity="0.6" />
        <line x1="25" y1="20" x2="30" y2="15" stroke="hsl(188, 94%, 43%)" strokeWidth="1" opacity="0.6" />
        <defs>
          <linearGradient id="gradient2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="hsl(188, 94%, 43%)" />
            <stop offset="100%" stopColor="hsl(174, 100%, 48%)" />
          </linearGradient>
        </defs>
      </svg>
      <span 
        className="font-bold tracking-tight gradient-text"
        style={{ fontSize }}
      >
        MONAS
      </span>
    </div>
  );
};

export default Logo;