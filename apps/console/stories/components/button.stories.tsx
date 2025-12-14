import type { Meta, StoryObj } from '@storybook/react';

import { Button } from '@shared/ui/components';

const meta = {
  title: 'Components/Button',
  component: Button,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
  argTypes: {
    onClick: { action: 'clicked' },
    variant: {
      control: 'inline-radio',
      options: ['solid', 'ghost', 'danger'],
    },
  },
  args: {
    children: 'Click me',
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Solid: Story = {};

export const Ghost: Story = {
  args: {
    variant: 'ghost',
  },
};

export const Danger: Story = {
  args: {
    variant: 'danger',
  },
};

export const Loading: Story = {
  args: {
    loading: true,
  },
};
