import type { Meta, StoryObj } from '@storybook/react';

import { Button, Card } from '@shared/ui/components';

const meta = {
  title: 'Components/Card',
  component: Card,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
  args: {
    header: 'Command Center',
    children: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
        <p style={{ margin: 0, color: 'var(--color-text-secondary)' }}>
          Use cards to cluster related telemetry and actions into focused panels that align with the
          factory.ai glass aesthetic.
        </p>
        <Button>Primary Action</Button>
      </div>
    ),
  },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {};

export const Muted: Story = {
  args: {
    variant: 'muted',
    header: 'Muted Card',
    density: 'compact',
  },
};

export const WithAccessory: Story = {
  args: {
    accessory: (
      <span style={{ color: 'var(--color-text-accent)', fontWeight: 600 }}>Live · Normal</span>
    ),
  },
};
