export type PromptSectionKey = 'purpose' | 'features' | 'techStack';

export type PromptDraft = Record<PromptSectionKey, string>;

export type PromptSectionConfig = {
  key: PromptSectionKey;
  title: string;
  description: string;
  placeholder: string;
  hint?: string;
  minChars: number;
  maxChars?: number;
  rows?: number;
};

export type PromptValidationResult = {
  status: 'idle' | 'valid' | 'error';
  message?: string;
  remaining?: number;
};

export type PromptValidationMap = Record<PromptSectionKey, PromptValidationResult>;

export type PromptTemplate = {
  id: string;
  name: string;
  description: string;
  prompt: string;
  sections: Partial<Record<PromptSectionKey, string>>;
};
