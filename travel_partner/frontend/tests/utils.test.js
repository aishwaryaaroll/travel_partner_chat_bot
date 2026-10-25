import { describe, expect, it } from 'vitest';
import { tripReducer, initialState } from '../src/context/TripContext';
import { safeUrl } from '../src/utils/safeUrl';
import { toBlocks } from '../src/utils/text';
import { serverState, itinerary } from './fixtures';

describe('safeUrl', () => {
  it.each(['https://www.nps.gov/zion/', 'http://example.com/a?b=c'])('allows %s', (u) => {
    expect(safeUrl(u)).toBe(new URL(u).href);
  });

  it.each([
    'javascript:alert(1)',
    'JaVaScRiPt:alert(1)',
    ' javascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'vbscript:msgbox',
    'file:///etc/passwd',
    '//evil.example/x',
    '/relative/path',
    'https://user:pass@example.com',
    '',
    null,
    42,
    'https://' + 'a'.repeat(3000) + '.com',
  ])('rejects %s', (u) => {
    expect(safeUrl(u)).toBeNull();
  });
});

describe('toBlocks', () => {
  it('splits paragraphs and bullet lists without interpreting HTML', () => {
    const blocks = toBlocks('Hello <b>there</b>\n\n- one\n- **two**\nBye');
    expect(blocks).toEqual([
      { type: 'p', text: 'Hello <b>there</b>' },
      { type: 'ul', items: ['one', 'two'] },
      { type: 'p', text: 'Bye' },
    ]);
  });
});

describe('tripReducer', () => {
  it('tags a reply that introduced a new itinerary version', () => {
    const started = tripReducer(initialState, { type: 'started', data: serverState({ session_id: 's' }) });
    const next = tripReducer(started, {
      type: 'reply',
      data: serverState({ stage: 'drafting', itinerary: { itinerary: itinerary(), version: 1, confirmed_version: null } }),
    });
    expect(next.version).toBe(1);
    expect(next.messages.at(-1).itineraryVersion).toBe(1);
  });

  it('clears the session when it expires', () => {
    const state = tripReducer({ ...initialState, sessionId: 's' }, { type: 'expired', message: 'expired' });
    expect(state.sessionId).toBeNull();
    expect(state.error).toBe('expired');
  });
});
