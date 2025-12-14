import type { PromptDraft, PromptSectionConfig, PromptSectionKey, PromptValidationMap } from './types';

export const SECTION_CONFIGS: PromptSectionConfig[] = [
  {
    key: 'purpose',
    title: 'Purpose',
    description: 'Describe the outcome you want. Focus on audience, value, and success criteria.',
    placeholder: 'What are you building? Who is it for? What problem does it solve?',
    hint: 'Give the planner the north star. Mention the user persona and success indicators.',
    minChars: 30,
    maxChars: 600,
    rows: 4,
  },
  {
    key: 'features',
    title: 'Features',
    description: 'List the capabilities, user stories, or flows the solution must support.',
    placeholder: '• Authentication with...\n• Dashboard summarising...\n• Alerts when...',
    hint: 'Bullet points work great. Prioritise must-haves over nice-to-haves.',
    minChars: 40,
    maxChars: 800,
    rows: 6,
  },
  {
    key: 'techStack',
    title: 'Tech Stack',
    description: 'Capture technical preferences, integrations, or constraints to honour.',
    placeholder: 'Frontend: Next.js + Tailwind\nBackend: FastAPI\nDatabase: Postgres\nOther: ...',
    hint: 'Call out frameworks, hosting preferences, compliance, and integration requirements.',
    minChars: 10,
    maxChars: 500,
    rows: 4,
  },
];

export const SECTION_LOOKUP: Record<PromptSectionKey, PromptSectionConfig> = SECTION_CONFIGS.reduce(
  (acc, config) => {
    acc[config.key] = config;
    return acc;
  },
  {} as Record<PromptSectionKey, PromptSectionConfig>,
);

export const EMPTY_DRAFT: PromptDraft = {
  purpose: '',
  features: '',
  techStack: '',
};

export function computeValidation(value: string, config: PromptSectionConfig) {
  const rawLength = value.length;
  const trimmedLength = value.trim().length;
  const remaining = config.maxChars ? Math.max(0, config.maxChars - rawLength) : undefined;

  if (rawLength === 0) {
    return {
      status: 'idle' as const,
      remaining,
    };
  }

  if (config.maxChars && rawLength > config.maxChars) {
    const over = rawLength - config.maxChars;
    return {
      status: 'error' as const,
      message: `Trim ${over} character${over === 1 ? '' : 's'} to stay within the limit.`,
      remaining: 0,
    };
  }

  if (trimmedLength < config.minChars) {
    const missing = config.minChars - trimmedLength;
    return {
      status: 'error' as const,
      message: `Add ${missing} more character${missing === 1 ? '' : 's'} for clarity.`,
      remaining,
    };
  }

  return {
    status: 'valid' as const,
    message: 'Looks good.',
    remaining,
  };
}

export function buildValidationMap(draft: PromptDraft): PromptValidationMap {
  return {
    purpose: computeValidation(draft.purpose, SECTION_LOOKUP.purpose),
    features: computeValidation(draft.features, SECTION_LOOKUP.features),
    techStack: computeValidation(draft.techStack, SECTION_LOOKUP.techStack),
  };
}

export function isDraftReady(draft: PromptDraft, validation: PromptValidationMap) {
  return SECTION_CONFIGS.every((config) => {
    const value = draft[config.key].trim();
    const result = validation[config.key];
    return value.length >= config.minChars && result.status === 'valid';
  });
}

