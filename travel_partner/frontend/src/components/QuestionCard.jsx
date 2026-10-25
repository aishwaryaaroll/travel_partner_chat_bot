import { useState } from 'react';
import { ChipSelect } from './ChipSelect';
import { Button, PaperCard } from './ui';

/** The agent's current question, with options, free-text fallback (via chat) and skip. */
export function QuestionCard({ question, onAnswer, onSkip, disabled }) {
  const [picked, setPicked] = useState([]);
  if (!question) return null;
  const multi = question.multi_select;

  return (
    <PaperCard className="question-card" tiltDeg="-0.6deg" aria-label="Current question">
      <p className="question-card__text">{question.text}</p>
      {question.options?.length > 0 && (
        <ChipSelect
          label={question.text}
          options={question.options}
          multi={multi}
          value={multi ? picked : null}
          disabled={disabled}
          onChange={(v) => (multi ? setPicked(v) : onAnswer(v))}
        />
      )}
      <div className="question-card__actions">
        {multi && (
          <Button size="sm" disabled={disabled || picked.length === 0} onClick={() => onAnswer(picked)}>
            Use these ({picked.length})
          </Button>
        )}
        {question.optional !== false && (
          <Button variant="ghost" size="sm" disabled={disabled} onClick={() => onSkip(question.key)}>
            Skip this
          </Button>
        )}
        <span className="hint">…or type your own answer below</span>
      </div>
    </PaperCard>
  );
}
