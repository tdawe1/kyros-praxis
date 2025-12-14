'use client';

import { createContext, useContext, useEffect, useMemo } from 'react';
import type { ReactNode } from 'react';

import { factoryDarkTheme, tokensToCssVars } from '../tokens';
import type { ThemeDefinition } from '../tokens';

type ThemeProviderProps = {
  theme?: ThemeDefinition;
  children: ReactNode;
};

const ThemeContext = createContext<ThemeDefinition>(factoryDarkTheme);

const applyCssVariables = (cssVars: Record<string, string>, themeName: string) => {
  const root = document.documentElement;
  root.dataset.theme = themeName;
  Object.entries(cssVars).forEach(([key, value]) => {
    root.style.setProperty(key, value);
  });
};

const clearCssVariables = (cssVars: Record<string, string>) => {
  const root = document.documentElement;
  Object.keys(cssVars).forEach((key) => {
    root.style.removeProperty(key);
  });
  delete root.dataset.theme;
};

export function ThemeProvider({ theme = factoryDarkTheme, children }: ThemeProviderProps) {
  const cssVars = useMemo(() => tokensToCssVars(theme.tokens), [theme]);

  useEffect(() => {
    applyCssVariables(cssVars, theme.name);
    return () => {
      clearCssVariables(cssVars);
    };
  }, [cssVars, theme.name]);

  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => {
  const theme = useContext(ThemeContext);
  return theme;
};

export { ThemeContext };
