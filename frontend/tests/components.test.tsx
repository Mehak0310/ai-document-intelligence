import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from '../src/App';
import { AnswerCard } from '../src/AnswerCard';
import { DocumentPanel } from '../src/DocumentPanel';
import { createRequest, errorMessage, downloadSource, request, REQUEST_TIMEOUT } from '../src/api';
import type { Answer } from '../src/types';

const id = 'a'.repeat(64);
const doc = { id, file_name: 'synthetic.pdf', num_chunks: 2, created_at: '2026-10-10' };
const answer: Answer = { answer: '**20 days** [S1]', evidence: [{ id: 'S1', document_id: id, chunk_id: `${id}:0`, file_name: doc.file_name, page: 1, excerpt: 'Employees receive 20 days.', score: .8, url: `/documents/${id}/source#page=1` }], citations: ['S1'], sources: [doc.file_name], latency: .12, model: 'mock', retrieved_chunks: 1, insufficient_evidence: false };

afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); vi.useRealTimers(); localStorage.clear(); });

describe('evidence and documents', () => {
  it('renders evidence with page links and sanitizes generated HTML', async () => {
    const source = vi.fn();
    const { container } = render(<AnswerCard result={{ ...answer, answer: '<img src=x onerror="alert(1)"><script>alert(1)</script>**safe**' }} onSource={source} disabled={false} />);
    expect(container.querySelector('script')).toBeNull();
    expect(container.querySelector('img')).toBeNull();
    expect(screen.getByText('safe')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Download source PDF · page 1' }));
    expect(source).toHaveBeenCalledWith(`/documents/${id}/source#page=1`);
    expect(screen.getByText('Employees receive 20 days.')).toBeInTheDocument();
  });

  it('supports selection and controlled archive actions', async () => {
    const select = vi.fn(), archive = vi.fn(), reset = vi.fn();
    render(<DocumentPanel documents={[doc]} selected={[]} busy={false} onSelect={select} onArchive={archive} onReset={reset} />);
    await userEvent.click(screen.getByRole('checkbox'));
    await userEvent.click(screen.getByRole('button', { name: 'Archive synthetic.pdf' }));
    await userEvent.click(screen.getByRole('button', { name: 'Archive all documents' }));
    expect(select).toHaveBeenCalledWith(id); expect(archive).toHaveBeenCalledWith(id); expect(reset).toHaveBeenCalledOnce();
  });
});

describe('application lifecycle', () => {
  it('uploads a synthetic PDF and refreshes documents', async () => {
    let uploaded = false;
    vi.stubGlobal('fetch', vi.fn(async (_url: string, options?: RequestInit) => {
      if (options?.method === 'POST') { uploaded = true; return new Response(JSON.stringify({ ...doc, duplicate: false })); }
      return new Response(JSON.stringify({ documents: uploaded ? [doc] : [] }));
    }));
    render(<App />);
    await screen.findByText('Backend ready. Upload a PDF to get started.');
    await userEvent.upload(screen.getByLabelText('Text-based PDF'), new File(['synthetic'], 'synthetic.pdf', { type: 'application/pdf' }));
    await userEvent.click(screen.getByRole('button', { name: 'Upload PDF' }));
    expect(await screen.findByText('Indexed synthetic.pdf · 2 chunks.')).toBeInTheDocument();
    expect(screen.getByRole('checkbox')).toBeInTheDocument();
  });

  it('guards overlapping form submissions, scopes queries and supports cancellation', async () => {
    let pendingSignal: AbortSignal | undefined;
    const fetchMock = vi.fn((url: string, options?: RequestInit) => {
      if (url.endsWith('/documents')) return Promise.resolve(new Response(JSON.stringify({ documents: [doc] })));
      pendingSignal = options?.signal as AbortSignal;
      return new Promise<Response>((resolve, reject) => pendingSignal?.addEventListener('abort', () => reject(new DOMException('cancelled', 'AbortError'))));
    });
    vi.stubGlobal('fetch', fetchMock);
    const { container } = render(<App />);
    await screen.findByText('Ready to explore your documents.');
    await userEvent.click(screen.getByRole('checkbox'));
    await userEvent.type(screen.getByLabelText('Your question'), 'annual leave');
    fireEvent.submit(container.querySelector('form')!);
    fireEvent.submit(container.querySelector('form')!);
    expect(fetchMock.mock.calls.filter(call => call[0].endsWith('/query'))).toHaveLength(1);
    const payload = JSON.parse(fetchMock.mock.calls.at(-1)![1]!.body as string);
    expect(payload.document_ids).toEqual([id]);
    await userEvent.click(screen.getByRole('button', { name: 'Cancel request' }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('cancelled or timed out'));
    expect(pendingSignal!.aborted).toBe(true);
  });

  it('renders answers and persists the theme only', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => new Response(JSON.stringify(url.endsWith('/documents') ? { documents: [doc] } : answer))));
    render(<App />);
    await screen.findByText('Ready to explore your documents.');
    await userEvent.type(screen.getByLabelText('Your question'), 'annual leave');
    await userEvent.click(screen.getByRole('button', { name: 'Ask question' }));
    expect(await screen.findByText('20 days')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Toggle dark mode' }));
    expect(localStorage.getItem('theme')).toBe('dark');
    expect(localStorage.length).toBe(1);
  });

  it('shows sanitized API errors without crashing', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ detail: 'Valid API token required.' }), { status: 401 })));
    render(<App />);
    expect(await screen.findByText('Valid API token required.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Ask question' })).toBeDisabled();
  });
});

describe('request boundaries', () => {
  it('aborts at the client deadline and clears timers', () => {
    vi.useFakeTimers(); const job = createRequest();
    vi.advanceTimersByTime(REQUEST_TIMEOUT);
    expect(job.controller.signal.aborted).toBe(true); job.finish();
    expect(errorMessage(new DOMException('x', 'AbortError'))).toContain('cancelled');
    expect(errorMessage('unknown')).toContain('Check the local backend');
  });

  it('sends token only in the header and handles invalid error bodies', async () => {
    const mock = vi.fn(async () => new Response('not JSON', { status: 503 }));
    vi.stubGlobal('fetch', mock);
    await expect(request('/documents', 'ephemeral-token')).rejects.toThrow('503');
    expect((mock.mock.calls[0] as unknown as [string, RequestInit])[1].headers).toBeInstanceOf(Headers);
  });

  it('rejects external or malformed source routes', async () => {
    await expect(downloadSource('https://example.com', '', new AbortController().signal)).rejects.toThrow('Invalid source');
  });
});
