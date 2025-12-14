import path from 'node:path';

import type { StorybookConfig } from '@storybook/react-webpack5';

const config: StorybookConfig = {
  stories: ['../stories/**/*.stories.@(ts|tsx)'],
  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-links',
    '@storybook/addon-interactions',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/react-webpack5',
  },
  docs: {
    autodocs: true,
  },
  typescript: {
    reactDocgen: 'react-docgen-typescript',
    tsconfigPath: './tsconfig.json',
  },
  webpackFinal: async (config) => {
    if (!config.resolve) {
      config.resolve = {};
    }

    config.resolve.alias = {
      ...(config.resolve.alias ?? {}),
      '@shared': path.resolve(__dirname, '../..', 'shared'),
    };

    config.resolve.extensions = Array.from(
      new Set([...(config.resolve.extensions ?? ['.js', '.jsx', '.json']), '.ts', '.tsx']),
    );

    if (!config.module) {
      config.module = { rules: [] };
    }

    config.module.rules = config.module.rules ?? [];

    config.module.rules.push({
      test: /\.tsx?$/,
      exclude: /node_modules/,
      use: [
        {
          loader: require.resolve('babel-loader'),
          options: {
            presets: [
              [
                require.resolve('@babel/preset-env'),
                {
                  targets: '> 0.25%, not dead',
                },
              ],
              [
                require.resolve('@babel/preset-react'),
                {
                  runtime: 'automatic',
                  development: process.env.NODE_ENV !== 'production',
                },
              ],
              require.resolve('@babel/preset-typescript'),
            ],
            cacheDirectory: true,
          },
        },
      ],
    });

    config.stats = {
      ...(config.stats ?? {}),
      children: true,
    };

    return config;
  },
};

export default config;
