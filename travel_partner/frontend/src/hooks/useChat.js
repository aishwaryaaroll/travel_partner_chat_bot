import { useCallback, useState } from 'react';
import { useTrip } from '../context/TripContext';

export const MAX_MESSAGE_LENGTH = 2000;

/** Chat input state plus the actions the chat UI needs. */
export function useChat() {
  const { state, sendMessage, clearError } = useTrip();
  const [draft, setDraft] = useState('');
  // Whatever the traveler sends while a question card is showing counts as answering it.
  const currentKey = state.question?.key ?? null;

  const submit = useCallback(
    (text = draft) => {
      const value = text.trim();
      if (!value || state.loading || value.length > MAX_MESSAGE_LENGTH) return false;
      sendMessage(value, { answering: currentKey });
      setDraft('');
      return true;
    },
    [draft, state.loading, sendMessage, currentKey],
  );

  const answer = useCallback(
    (values) => {
      const list = Array.isArray(values) ? values : [values];
      if (list.length) sendMessage(list.join(', '), { answering: currentKey });
    },
    [sendMessage, currentKey],
  );

  const skip = useCallback(
    (questionKey) =>
      sendMessage("I'd like to skip this one. Please assume something sensible.", { skipQuestion: questionKey }),
    [sendMessage],
  );

  return {
    messages: state.messages,
    question: state.question,
    loading: state.loading,
    error: state.error,
    notice: state.notice,
    stage: state.stage,
    messagesRemaining: state.messagesRemaining,
    draft,
    setDraft,
    submit,
    answer,
    skip,
    clearError,
  };
}
