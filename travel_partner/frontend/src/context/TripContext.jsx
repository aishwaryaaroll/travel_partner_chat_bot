import { createContext, useCallback, useContext, useMemo, useReducer, useRef } from 'react';
import { api } from '../services/api';

// Trip state lives only in memory. Refreshing the page starts a new trip, so no
// conversation text is ever written to browser storage.

const TripContext = createContext(null);

export const initialState = {
  sessionId: null,
  messages: [],
  question: null,
  preferences: {},
  stage: 'idle', // idle | gathering | drafting | confirmed
  itinerary: null,
  version: null,
  confirmedVersion: null,
  notice: null,
  error: null,
  loading: false,
  messagesRemaining: null,
  openCoreQuestions: null,
  readyToGenerate: false,
  awaitingDestinationChoice: false,
  pendingAnswer: null, // question key the in-flight message answers or skips
};

let nextId = 1;
const msg = (role, content, extra = {}) => ({ id: nextId++, role, content, ...extra });

function applyServerState(state, data) {
  return {
    ...state,
    question: data.question ?? null,
    preferences: data.preferences ?? {},
    stage: data.stage ?? state.stage,
    itinerary: data.itinerary?.itinerary ?? null,
    version: data.itinerary?.version ?? null,
    confirmedVersion: data.itinerary?.confirmed_version ?? null,
    notice: data.notice ?? null,
    messagesRemaining: data.messages_remaining ?? state.messagesRemaining,
    openCoreQuestions: data.open_core_questions ?? state.openCoreQuestions,
    readyToGenerate: Boolean(data.ready_to_generate),
    awaitingDestinationChoice: Boolean(data.awaiting_destination_choice),
    pendingAnswer: null,
  };
}

export function tripReducer(state, action) {
  switch (action.type) {
    case 'loading':
      return { ...state, loading: true, error: null };
    case 'started':
      return {
        ...applyServerState(initialState, action.data),
        sessionId: action.data.session_id,
        messages: action.data.reply ? [msg('assistant', action.data.reply)] : [],
      };
    case 'user_message':
      return {
        ...state,
        messages: [...state.messages, msg('user', action.text)],
        question: null,
        pendingAnswer: action.questionKey ?? null,
      };
    case 'reply': {
      const prevVersion = state.version;
      const next = applyServerState(state, action.data);
      const updated = next.version && next.version !== prevVersion;
      const reply = msg('assistant', action.data.reply || '', { itineraryVersion: updated ? next.version : null });
      return { ...next, loading: false, messages: [...state.messages, reply] };
    }
    case 'state':
      return { ...applyServerState(state, action.data), loading: false };
    case 'error':
      return { ...state, loading: false, error: action.message, pendingAnswer: null };
    case 'expired':
      return { ...initialState, error: action.message };
    case 'clear_error':
      return { ...state, error: null, notice: null };
    case 'reset':
      return initialState;
    default:
      return state;
  }
}

export function TripProvider({ children, client = api }) {
  const [state, dispatch] = useReducer(tripReducer, initialState);
  const sessionRef = useRef(null);
  sessionRef.current = state.sessionId;

  const fail = useCallback((err) => {
    if (err?.code === 'session_not_found') dispatch({ type: 'expired', message: err.message });
    else dispatch({ type: 'error', message: err?.message || 'Something went wrong.' });
  }, []);

  const startTrip = useCallback(async () => {
    dispatch({ type: 'loading' });
    try {
      if (sessionRef.current) client.deleteSession(sessionRef.current).catch(() => {});
      dispatch({ type: 'started', data: await client.createSession() });
    } catch (err) {
      fail(err);
    }
  }, [client, fail]);

  const sendMessage = useCallback(
    async (text, { skipQuestion = null, answering = null } = {}) => {
      const message = text.trim();
      if (!message || !sessionRef.current) return;
      dispatch({ type: 'user_message', text: message, questionKey: skipQuestion || answering });
      dispatch({ type: 'loading' });
      try {
        const data = await client.sendMessage(sessionRef.current, message, { skipQuestion, answering });
        dispatch({ type: 'reply', data });
      } catch (err) {
        fail(err);
      }
    },
    [client, fail],
  );

  const confirm = useCallback(async (version) => {
    dispatch({ type: 'loading' });
    try {
      dispatch({ type: 'state', data: await client.confirmItinerary(sessionRef.current, version) });
    } catch (err) {
      fail(err);
    }
  }, [client, fail]);

  const downloadPdf = useCallback(async () => {
    try {
      return await client.downloadPdf(sessionRef.current);
    } catch (err) {
      fail(err);
      return null;
    }
  }, [client, fail]);

  const clearError = useCallback(() => dispatch({ type: 'clear_error' }), []);

  const value = useMemo(
    () => ({ state, startTrip, sendMessage, confirm, downloadPdf, clearError }),
    [state, startTrip, sendMessage, confirm, downloadPdf, clearError],
  );
  return <TripContext.Provider value={value}>{children}</TripContext.Provider>;
}

export function useTrip() {
  const ctx = useContext(TripContext);
  if (!ctx) throw new Error('useTrip must be used inside <TripProvider>');
  return ctx;
}
