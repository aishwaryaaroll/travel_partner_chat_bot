/**
 * Returns a normalized URL string if it is an absolute http(s) URL, otherwise null.
 * Use for every link that comes from the API or the model.
 */
export function safeUrl(value) {
  if (typeof value !== 'string' || value.length > 2000) return null;
  try {
    const url = new URL(value.trim());
    if (url.protocol !== 'https:' && url.protocol !== 'http:') return null;
    if (url.username || url.password) return null;
    return url.href;
  } catch {
    return null;
  }
}
