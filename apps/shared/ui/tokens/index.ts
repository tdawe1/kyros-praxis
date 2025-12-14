export type TokenLeafValue = string | number;

export interface TokenRecord {
  [key: string]: TokenLeafValue | TokenRecord;
}

export type DesignTokens = {
  colors: TokenRecord;
  spacing: Record<string, string>;
  radius: Record<string, string>;
  motion: {
    duration: Record<string, string>;
    easing: Record<string, string>;
  };
  typography: {
    fontFamily: Record<string, string>;
    weight: Record<string, string>;
    size: Record<string, string>;
    letterSpacing: Record<string, string>;
    lineHeight: Record<string, string>;
  };
  elevation: Record<string, string>;
};

const colors = {
  background: '#030406',
  surface: '#090f15',
  surfaceMuted: 'rgba(15, 19, 27, 0.92)',
  surfaceRaised: '#101823',
  primary: '#1fb6d5',
  primaryMuted: '#0f6070',
  primaryOn: '#031418',
  accent: '#f6b756',
  accentSoft: '#fdd59c',
  accentBorder: 'rgba(246, 183, 86, 0.42)',
  outline: 'rgba(120, 131, 152, 0.42)',
  border: 'rgba(86, 96, 115, 0.38)',
  divider: 'rgba(86, 96, 115, 0.24)',
  layers: {
    soft: 'rgba(11, 16, 24, 0.92)',
    elevated: 'rgba(14, 21, 32, 0.94)',
    deep: 'rgba(6, 10, 17, 0.96)',
  },
  text: {
    primary: '#f3f5f7',
    secondary: '#b8c1cd',
    muted: 'rgba(152, 165, 183, 0.72)',
    inverted: '#020305',
    accent: '#7ddfff',
  },
  status: {
    success: '#44d49b',
    warning: '#f6b756',
    danger: '#f9816e',
    info: '#6bc0ff',
  },
  glass: {
    background: 'rgba(14, 19, 28, 0.85)',
    stroke: 'rgba(120, 131, 152, 0.32)',
    blur: '10px',
  },
} as const satisfies TokenRecord;

const spacing = {
  '3xs': '0.125rem',
  '2xs': '0.25rem',
  xs: '0.5rem',
  sm: '0.75rem',
  md: '1rem',
  lg: '1.5rem',
  xl: '2rem',
  '2xl': '2.5rem',
  '3xl': '3.5rem',
  gutter: '4rem',
} as const;

const radius = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '18px',
  xl: '24px',
  pill: '999px',
} as const;

const motion = {
  duration: {
    shortest: '120ms',
    short: '180ms',
    medium: '250ms',
    long: '400ms',
    linger: '600ms',
  },
  easing: {
    standard: 'cubic-bezier(0.4, 0, 0.2, 1)',
    emphasized: 'cubic-bezier(0.4, 0, 0.3, 1)',
    entrance: 'cubic-bezier(0.3, 0, 0.2, 1)',
    exit: 'cubic-bezier(0.4, 0.14, 0.3, 1)',
    spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  },
} as const;

const typography = {
  fontFamily: {
    sans: "'Inter', 'Poppins', 'Segoe UI', 'Helvetica Neue', sans-serif",
    mono: "'Fira Code', 'SFMono-Regular', Consolas, 'Liberation Mono', monospace",
  },
  weight: {
    regular: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  size: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.5rem',
    display: '2.75rem',
    metric: '3.5rem',
  },
  letterSpacing: {
    tight: '-0.01em',
    normal: '0',
    loose: '0.04em',
    caps: '0.12em',
  },
  lineHeight: {
    tight: '1.2',
    snug: '1.35',
    normal: '1.5',
    relaxed: '1.72',
  },
} as const;

const elevation = {
  low: '0 12px 24px -18px rgba(20, 148, 196, 0.28)',
  medium: '0 18px 32px -20px rgba(17, 24, 39, 0.5)',
  high: '0 32px 48px -20px rgba(20, 148, 196, 0.32)',
  focus: '0 0 0 2px rgba(125, 223, 255, 0.45)',
} as const;

export const factoryDarkTheme = {
  name: 'factory-dark',
  tokens: {
    colors,
    spacing,
    radius,
    motion,
    typography,
    elevation,
  } satisfies DesignTokens,
} as const;

export type ThemeDefinition = typeof factoryDarkTheme;

type FlattenTokens = Record<string, string>;

const buildVarKey = (path: string[]) => `--${path.join('-')}`;

const traverseTokens = (record: TokenRecord, path: string[]): FlattenTokens => {
  return Object.entries(record).reduce<FlattenTokens>((acc, [key, value]) => {
    const nextPath = [...path, key.replace(/[A-Z]/g, (char) => `-${char.toLowerCase()}`)];
    if (typeof value === 'string' || typeof value === 'number') {
      acc[buildVarKey(nextPath)] = String(value);
      return acc;
    }
    acc = { ...acc, ...traverseTokens(value as TokenRecord, nextPath) };
    return acc;
  }, {});
};

export const tokensToCssVars = (tokens: DesignTokens): FlattenTokens => {
  const result: FlattenTokens = {};

  result['--font-sans'] = tokens.typography.fontFamily.sans;
  result['--font-mono'] = tokens.typography.fontFamily.mono;

  Object.assign(result, traverseTokens(tokens.colors, ['color']));

  Object.entries(tokens.spacing).forEach(([key, value]) => {
    result[`--space-${key}`] = value;
  });

  Object.entries(tokens.radius).forEach(([key, value]) => {
    result[`--radius-${key}`] = value;
  });

  Object.entries(tokens.motion.duration).forEach(([key, value]) => {
    result[`--motion-duration-${key}`] = value;
  });

  Object.entries(tokens.motion.easing).forEach(([key, value]) => {
    result[`--motion-easing-${key}`] = value;
  });

  Object.entries(tokens.typography.weight).forEach(([key, value]) => {
    result[`--font-weight-${key}`] = value;
  });

  Object.entries(tokens.typography.size).forEach(([key, value]) => {
    result[`--font-size-${key}`] = value;
  });

  Object.entries(tokens.typography.letterSpacing).forEach(([key, value]) => {
    result[`--font-tracking-${key}`] = value;
  });

  Object.entries(tokens.typography.lineHeight).forEach(([key, value]) => {
    result[`--font-leading-${key}`] = value;
  });

  Object.entries(tokens.elevation).forEach(([key, value]) => {
    result[`--elevation-${key}`] = value;
  });

  return result;
};
