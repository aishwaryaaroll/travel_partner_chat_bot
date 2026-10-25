import { useEffect, useRef } from 'react';
import { MAX_MESSAGE_LENGTH } from '../hooks/useChat';
import { Button, RichText, Spinner } from './ui';

export function ChatBubble({ role, content, itineraryVersion }) {
  return (
    <div className={`bubble bubble--${role}`}>
      <span className="bubble__who">{role === 'user' ? 'You' : 'Travel Partner'}</span>
      <div className="bubble__body">
        <RichText text={content} />
        {itineraryVersion && <p className="bubble__tag">📌 Itinerary updated (version {itineraryVersion})</p>}
      </div>
    </div>
  );
}

export function ChatLog({ messages, loading, loadingLabel }) {
  const logRef = useRef(null);
  // Scroll only the log box (scrollIntoView would also scroll the whole window).
  useEffect(() => {
    const el = logRef.current;
    el?.scrollTo?.({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages.length, loading]);

  return (
    <div className="chat-log" aria-live="polite" ref={logRef}>
      {messages.map((m) => (
        <ChatBubble key={m.id} {...m} />
      ))}
      {loading && <Spinner label={loadingLabel} />}
    </div>
  );
}

export function ChatInput({ value, onChange, onSubmit, disabled, placeholder }) {
  const tooLong = value.length > MAX_MESSAGE_LENGTH;
  const send = (e) => {
    e.preventDefault();
    onSubmit();
  };
  return (
    <form className="chat-input" onSubmit={send}>
      <label htmlFor="chat-text" className="sr-only">
        Message
      </label>
      <textarea
        id="chat-text"
        rows={2}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) send(e);
        }}
        aria-invalid={tooLong}
      />
      <div className="chat-input__row">
        <span className={`counter ${tooLong ? 'counter--over' : ''}`}>
          {value.length}/{MAX_MESSAGE_LENGTH}
        </span>
        <Button type="submit" disabled={disabled || !value.trim() || tooLong}>
          Send
        </Button>
      </div>
    </form>
  );
}
