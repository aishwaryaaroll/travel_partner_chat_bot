// All backend calls live here. The browser never holds API keys: it only has an
// anonymous session token issued by our backend.

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const TIMEOUT_MS = 270_000; // a little longer than the backend's agent timeout

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function request(path, { method = 'GET', body, sessionId, expect = 'json' } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (sessionId) headers['X-Session-Id'] = sessionId;

  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
      credentials: 'omit',
      referrerPolicy: 'no-referrer',
    });
  } catch (err) {
    const timedOut = err?.name === 'AbortError';
    throw new ApiError(0, timedOut ? 'timeout' : 'network', timedOut
      ? 'That took too long. Please try again.'
      : "Can't reach the travel planner. Is the backend running?");
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    let code = 'http_error';
    let message = 'Something went wrong. Please try again.';
    try {
      const data = await res.json();
      if (typeof data?.error?.message === 'string') message = data.error.message;
      if (typeof data?.error?.code === 'string') code = data.error.code;
    } catch {
      /* non-JSON error body: keep the generic message */
    }
    throw new ApiError(res.status, code, message);
  }
  if (res.status === 204) return null;
  return expect === 'blob' ? res.blob() : res.json();
}

export const api = {
  createSession: () => request('/api/sessions', { method: 'POST' }),
  getSession: (sessionId) => request('/api/session', { sessionId }),
  deleteSession: (sessionId) => request('/api/session', { method: 'DELETE', sessionId }),
  sendMessage: (sessionId, message, { skipQuestion = null, answering = null } = {}) => {
    const body = { message };
    if (skipQuestion) body.skip_question = skipQuestion;
    else if (answering) body.answering = answering;
    return request('/api/chat', { method: 'POST', sessionId, body });
  },
  confirmItinerary: (sessionId, version) =>
    request('/api/itinerary/confirm', { method: 'POST', sessionId, body: { version } }),
  downloadPdf: (sessionId) => request('/api/itinerary/pdf', { sessionId, expect: 'blob' }),
};

/** Triggers a browser download for a Blob without touching the DOM beyond a temporary link. */
export function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.rel = 'noopener';
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
