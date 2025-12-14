import { useState } from 'react';

import type { Meta, StoryObj } from '@storybook/react';

import { Button, Field, TextArea, TextInput } from '@shared/ui/components';

const meta = {
  title: 'Components/Field',
  component: Field,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof Field>;

export default meta;

type Story = StoryObj<typeof meta>;

export const FormExample: Story = {
  args: {
    label: 'Crew ID',
    children: null,
  },
  render: function Render() {
    const [crewId, setCrewId] = useState('spec_to_tasks');
    const [prompt, setPrompt] = useState('');

    return (
      <form
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-md)',
          minWidth: '360px',
        }}
        onSubmit={(event) => {
          event.preventDefault();
        }}
      >
        <Field label="Crew ID" helpText="Registered orchestrator crew slug.">
          <TextInput value={crewId} onChange={(event) => setCrewId(event.target.value)} />
        </Field>
        <Field
          label="Prompt"
          helpText="Describe the task or scenario the agent should execute."
        >
          <TextArea
            rows={4}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Design a workflow for real-time KPI anomaly detection."
          />
        </Field>
        <Button type="submit">Submit</Button>
      </form>
    );
  },
};
