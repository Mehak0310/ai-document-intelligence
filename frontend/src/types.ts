export interface DocumentInfo { id: string; file_name: string; num_chunks: number; created_at: string }
export interface Evidence { id: string; document_id: string; chunk_id: string; file_name: string; page: number; excerpt: string; score: number; url: string }
export interface Answer { answer: string; evidence: Evidence[]; citations: string[]; sources: string[]; latency: number; model: string; retrieved_chunks: number; insufficient_evidence: boolean }
export type Style = 'simple' | 'bullet' | 'detailed' | 'analytical';
export interface Message { id: number; question: string; result?: Answer; error?: string }
