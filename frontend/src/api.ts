export const BASE_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');
export const REQUEST_TIMEOUT = 135_000;

export function createRequest() {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
  return { controller, finish: () => clearTimeout(timer) };
}

export async function request<T>(path: string, token: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}).`);
  }
  return response.json();
}

export function errorMessage(error: unknown) {
  if (error instanceof DOMException && error.name === 'AbortError') return 'Request cancelled or timed out. The server may still finish processing.';
  return error instanceof Error ? error.message : 'Request failed. Check the local backend.';
}

export async function downloadSource(path: string, token: string, signal: AbortSignal) {
  const [source] = path.split('#');
  // Only app-generated local source routes are permitted.
  if (!/^\/documents\/[a-f0-9]{64}\/source$/.test(source)) throw new Error('Invalid source reference.');
  const response = await fetch(`${BASE_URL}${source}`, { signal, headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!response.ok) throw new Error('Source is unavailable. It may have been archived.');
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = 'source.pdf';
  link.rel = 'noopener noreferrer';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
