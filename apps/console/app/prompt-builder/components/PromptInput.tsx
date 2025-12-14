'use client';

import { Field, TextArea } from '@shared/ui/components';
import type { ChangeEvent } from 'react';

import type {
  PromptDraft,
  PromptSectionConfig,
  PromptSectionKey,
  PromptValidationMap,
} from '../types';
import { PromptSection } from './PromptSection';
import { ValidationFeedback } from './ValidationFeedback';

type PromptInputProps = {
  sections: PromptSectionConfig[];
  values: PromptDraft;
  validation: PromptValidationMap;
  onChange: (key: PromptSectionKey, value: string) => void;
};

export function PromptInput({ sections, values, validation, onChange }: PromptInputProps) {
  const handleChange =
    (key: PromptSectionKey) =>
    (event: ChangeEvent<HTMLTextAreaElement>) => {
      onChange(key, event.target.value);
    };

  return (
    <div className="flex flex-col gap-6">
      {sections.map((section) => {
        const value = values[section.key];
        const validationResult = validation[section.key];
        const currentLength = value.length;

        return (
          <PromptSection
            key={section.key}
            title={section.title}
            description={section.description}
            action={
              section.maxChars ? (
                <span className="text-xs font-mono text-neutral-500">
                  Min {section.minChars} • Max {section.maxChars} chars
                </span>
              ) : (
                <span className="text-xs font-mono text-neutral-500">
                  Min {section.minChars} chars
                </span>
              )
            }
          >
            <Field label={section.title} helpText={section.hint} htmlFor={`prompt-${section.key}`}>
              <TextArea
                id={`prompt-${section.key}`}
                placeholder={section.placeholder}
                value={value}
                onChange={handleChange(section.key)}
                rows={section.rows ?? 4}
                spellCheck
                invalid={validationResult.status === 'error'}
                className="font-mono text-sm leading-6"
              />
            </Field>
            <ValidationFeedback
              result={validationResult}
              minChars={section.minChars}
              maxChars={section.maxChars}
              currentLength={currentLength}
            />
          </PromptSection>
        );
      })}
    </div>
  );
}

