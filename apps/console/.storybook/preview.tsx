import type { Preview } from '@storybook/react';

import '../app/globals.css';

import { ThemeProvider } from '@shared/ui/theme';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    layout: 'centered',
  },
  decorators: [
    (Story) => (
      <ThemeProvider>
        <div style={{ minWidth: '320px', maxWidth: '960px' }}>
          <Story />
        </div>
      </ThemeProvider>
    ),
  ],
};

export default preview;
