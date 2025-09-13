'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Form,
  TextInput,
  TextArea,
  Select,
  SelectItem,
  Button,
  ProgressIndicator,
  ProgressStep,
  InlineNotification,
  Tag,
  NumberInput,
  Toggle,
  Tile,
  Layer,
  Checkbox,
  CheckboxGroup,
  Modal,
} from '@carbon/react';
import { ArrowLeft, ArrowRight, Save, Chemistry } from '@carbon/icons-react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { AgentFormData, AgentFormBasicsSchema } from '../../../lib/schemas/agent';
import { useCreateAgent } from '../../../hooks/useAgents';
import { usePersistedState } from '../../../hooks/usePersistedState';
import toast from 'react-hot-toast';

const WIZARD_STEPS = [
  { label: 'Basics', key: 'basics' },
  { label: 'Capabilities', key: 'capabilities' },
  { label: 'Policies', key: 'policies' },
  { label: 'Connectors', key: 'connectors' },
  { label: 'Scheduling', key: 'scheduling' },
  { label: 'Review', key: 'review' },
];

export default function CreateAgentPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [formDraft, setFormDraft] = usePersistedState<Partial<AgentFormData>>('agent-draft', {});
  const [showExitModal, setShowExitModal] = useState(false);
  
  const createAgent = useCreateAgent();

  const {
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isValid },
    trigger,
  } = useForm<AgentFormData>({
    resolver: zodResolver(AgentFormBasicsSchema),
    defaultValues: formDraft,
    mode: 'onChange',
  });

  const formValues = watch();

  // Auto-save draft
  useEffect(() => {
    const timeout = setTimeout(() => {
      setFormDraft(formValues);
    }, 1000);
    return () => clearTimeout(timeout);
  }, [formValues, setFormDraft]);

  const handleNext = async () => {
    // Validate current step
    const isStepValid = await trigger();
    if (!isStepValid && currentStep !== 5) {
      toast.error('Please fix the errors before proceeding');
      return;
    }

    if (currentStep < WIZARD_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepClick = async (index: number) => {
    if (index < currentStep) {
      setCurrentStep(index);
    } else if (index === currentStep + 1) {
      await handleNext();
    }
  };

  const onSubmit = async (data: AgentFormData) => {
    try {
      await createAgent.mutateAsync(data);
      // Clear draft on success
      setFormDraft({});
      toast.success('Agent created successfully!');
      router.push('/agents');
    } catch (error) {
      toast.error('Failed to create agent');
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0: // Basics
        return (
          <div className="step-content">
            <h3>Basic Information</h3>
            <p className="step-description">Configure the fundamental settings for your agent.</p>
            
            <Controller
              name="name"
              control={control}
              render={({ field, fieldState }) => (
                <TextInput
                  {...field}
                  id="agent-name"
                  labelText="Agent Name"
                  placeholder="e.g., Customer Support Agent"
                  invalid={!!fieldState.error}
                  invalidText={fieldState.error?.message}
                  maxLength={100}
                />
              )}
            />

            <Controller
              name="description"
              control={control}
              render={({ field }) => (
                <TextArea
                  {...field}
                  labelText="Description"
                  placeholder="Describe what this agent does..."
                  rows={4}
                  maxLength={500}
                />
              )}
            />

            <Controller
              name="model"
              control={control}
              render={({ field }) => (
                <Select
                  {...field}
                  id="model-select"
                  labelText="AI Model"
                  defaultValue="gpt-4-turbo"
                >
                  <SelectItem value="gpt-4-turbo" text="GPT-4 Turbo" />
                  <SelectItem value="gpt-3.5-turbo" text="GPT-3.5 Turbo" />
                  <SelectItem value="claude-3-opus" text="Claude 3 Opus" />
                  <SelectItem value="claude-3-sonnet" text="Claude 3 Sonnet" />
                  <SelectItem value="gemini-pro" text="Gemini Pro" />
                  <SelectItem value="custom" text="Custom Model" />
                </Select>
              )}
            />

            <Controller
              name="temperature"
              control={control}
              defaultValue={0.7}
              render={({ field }) => (
                <NumberInput
                  {...field}
                  id="temperature"
                  label="Temperature (0-2)"
                  helperText="Controls randomness. Lower is more focused, higher is more creative."
                  min={0}
                  max={2}
                  step={0.1}
                  value={field.value}
                />
              )}
            />

            <Controller
              name="maxTokens"
              control={control}
              defaultValue={4096}
              render={({ field }) => (
                <NumberInput
                  {...field}
                  id="max-tokens"
                  label="Max Tokens"
                  helperText="Maximum number of tokens to generate"
                  min={1}
                  max={128000}
                  step={1000}
                  value={field.value}
                />
              )}
            />

            <Controller
              name="systemPrompt"
              control={control}
              render={({ field }) => (
                <TextArea
                  {...field}
                  labelText="System Prompt (Optional)"
                  placeholder="You are a helpful assistant..."
                  rows={6}
                />
              )}
            />
          </div>
        );

      case 1: // Capabilities
        return (
          <div className="step-content">
            <h3>Agent Capabilities</h3>
            <p className="step-description">Select the tools and functions this agent can use.</p>
            
            <CheckboxGroup legendText="Available Capabilities">
              <Checkbox labelText="Email Handler" id="cap-email" />
              <Checkbox labelText="Database Query" id="cap-database" />
              <Checkbox labelText="Web Search" id="cap-search" />
              <Checkbox labelText="File Management" id="cap-files" />
              <Checkbox labelText="API Integration" id="cap-api" />
              <Checkbox labelText="Data Analysis" id="cap-analysis" />
              <Checkbox labelText="Report Generation" id="cap-reports" />
              <Checkbox labelText="Calendar Management" id="cap-calendar" />
            </CheckboxGroup>

            <InlineNotification
              kind="info"
              title="Capability Dependencies"
              subtitle="Some capabilities may require additional configuration in the Connectors step."
              hideCloseButton
            />
          </div>
        );

      case 2: // Policies
        return (
          <div className="step-content">
            <h3>Security Policies & Guardrails</h3>
            <p className="step-description">Configure safety and compliance settings.</p>
            
            <CheckboxGroup legendText="Security Policies">
              <Checkbox labelText="PII Protection" id="policy-pii" defaultChecked />
              <Checkbox labelText="Content Filtering" id="policy-content" defaultChecked />
              <Checkbox labelText="Rate Limiting" id="policy-rate" defaultChecked />
              <Checkbox labelText="Domain Restrictions" id="policy-domain" />
              <Checkbox labelText="Data Retention Limits" id="policy-retention" />
            </CheckboxGroup>

            <div style={{ marginTop: '2rem' }}>
              <h4>Custom Rules</h4>
              <TextArea
                labelText="Additional Policies (JSON)"
                placeholder='{"rules": []}'
                rows={6}
              />
            </div>
          </div>
        );

      case 3: // Connectors
        return (
          <div className="step-content">
            <h3>External Connectors</h3>
            <p className="step-description">Configure integrations with external services.</p>
            
            <CheckboxGroup legendText="Available Connectors">
              <Checkbox labelText="PostgreSQL Database" id="conn-postgres" />
              <Checkbox labelText="Redis Cache" id="conn-redis" />
              <Checkbox labelText="AWS S3" id="conn-s3" />
              <Checkbox labelText="Slack" id="conn-slack" />
              <Checkbox labelText="Gmail" id="conn-gmail" />
              <Checkbox labelText="GitHub" id="conn-github" />
            </CheckboxGroup>

            <Button kind="tertiary" size="sm" style={{ marginTop: '1rem' }}>
              Configure Secrets
            </Button>
          </div>
        );

      case 4: // Scheduling
        return (
          <div className="step-content">
            <h3>Scheduling</h3>
            <p className="step-description">Set up automated execution schedules.</p>
            
            <Toggle
              id="schedule-enabled"
              labelText="Enable Scheduled Runs"
              labelA="Disabled"
              labelB="Enabled"
            />

            <Select
              id="schedule-type"
              labelText="Schedule Type"
              disabled={!formValues.scheduleEnabled}
            >
              <SelectItem value="once" text="One Time" />
              <SelectItem value="interval" text="Interval" />
              <SelectItem value="cron" text="CRON Expression" />
            </Select>

            <TextInput
              id="schedule-expression"
              labelText="Schedule Expression"
              placeholder="0 9 * * MON-FRI"
              helperText="Enter CRON expression or interval"
              disabled={!formValues.scheduleEnabled}
            />
          </div>
        );

      case 5: // Review
        return (
          <div className="step-content">
            <h3>Review Configuration</h3>
            <p className="step-description">Review your agent configuration before creating.</p>
            
            <Layer>
              <Tile>
                <h4>Basic Information</h4>
                <dl>
                  <dt>Name:</dt>
                  <dd>{formValues.name || 'Not set'}</dd>
                  <dt>Description:</dt>
                  <dd>{formValues.description || 'Not set'}</dd>
                  <dt>Model:</dt>
                  <dd>{formValues.model || 'Not set'}</dd>
                  <dt>Temperature:</dt>
                  <dd>{formValues.temperature}</dd>
                  <dt>Max Tokens:</dt>
                  <dd>{formValues.maxTokens}</dd>
                </dl>
              </Tile>
            </Layer>

            <Layer style={{ marginTop: '1rem' }}>
              <Tile>
                <h4>Configuration Summary</h4>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <Tag type="blue">3 Capabilities</Tag>
                  <Tag type="green">5 Policies</Tag>
                  <Tag type="purple">2 Connectors</Tag>
                  {formValues.scheduleEnabled && <Tag type="teal">Scheduled</Tag>}
                </div>
              </Tile>
            </Layer>

            {Object.keys(errors).length > 0 && (
              <InlineNotification
                kind="error"
                title="Validation Errors"
                subtitle="Please fix the errors in previous steps before creating the agent."
              />
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="agent-wizard">
      <div className="wizard-header">
        <Button
          kind="ghost"
          renderIcon={ArrowLeft}
          onClick={() => setShowExitModal(true)}
        >
          Cancel
        </Button>
        <h1>Create New Agent</h1>
      </div>

      <ProgressIndicator currentIndex={currentStep} spaceEqually>
        {WIZARD_STEPS.map((step, index) => (
          <ProgressStep
            key={step.key}
            label={step.label}
            onClick={() => handleStepClick(index)}
          />
        ))}
      </ProgressIndicator>

      <form onSubmit={handleSubmit(onSubmit)} className="wizard-form">
        {renderStepContent()}

        <div className="wizard-actions">
          <Button
            kind="secondary"
            onClick={handleBack}
            disabled={currentStep === 0}
            renderIcon={ArrowLeft}
          >
            Back
          </Button>

          {currentStep < WIZARD_STEPS.length - 1 ? (
            <Button
              kind="primary"
              onClick={handleNext}
              renderIcon={ArrowRight}
              iconDescription="Next"
            >
              Next
            </Button>
          ) : (
            <Button
              kind="primary"
              type="submit"
              renderIcon={Save}
              disabled={createAgent.isPending || Object.keys(errors).length > 0}
            >
              {createAgent.isPending ? 'Creating...' : 'Create Agent'}
            </Button>
          )}
        </div>
      </form>

      <Modal
        open={showExitModal}
        modalHeading="Discard Changes?"
        modalLabel="Confirmation"
        primaryButtonText="Discard"
        secondaryButtonText="Continue Editing"
        onRequestClose={() => setShowExitModal(false)}
        onRequestSubmit={() => {
          setFormDraft({});
          router.push('/agents');
        }}
        danger
      >
        <p>
          You have unsaved changes. Your draft will be saved and you can continue later.
          Are you sure you want to leave?
        </p>
      </Modal>

      <style jsx>{`
        .agent-wizard {
          padding: 2rem;
          max-width: 800px;
          margin: 0 auto;
        }
        .wizard-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 2rem;
        }
        .wizard-form {
          margin-top: 2rem;
        }
        .step-content {
          min-height: 400px;
          padding: 2rem 0;
        }
        .step-content > * + * {
          margin-top: 1.5rem;
        }
        .step-description {
          color: var(--cds-text-secondary);
          margin-bottom: 2rem;
        }
        .wizard-actions {
          display: flex;
          justify-content: space-between;
          margin-top: 2rem;
          padding-top: 2rem;
          border-top: 1px solid var(--cds-border-subtle);
        }
        dl {
          display: grid;
          grid-template-columns: 120px 1fr;
          gap: 0.5rem;
        }
        dt {
          font-weight: 600;
        }
        dd {
          color: var(--cds-text-secondary);
        }
      `}</style>
    </div>
  );
}