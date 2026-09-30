export interface CareerBrainSearchResult {
  id: string;
  source_type: string;
  source_id: string;
  title: string | null;
  content: string;
  score: number;
}

export interface CareerBrainSearchResponse {
  query: string;
  results: CareerBrainSearchResult[];
}

export interface CareerBrainContextResponse extends CareerBrainSearchResponse {
  context: string;
}

export interface CareerBrainIndexResponse {
  documents_processed: number;
  chunks_created: number;
  embeddings_created: number;
  embeddings_reused: number;
  embedding_model: string;
}

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('careeros_token');
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
  });
  if (!response.ok) throw new Error(`API ${response.status}: ${await response.text()}`);
  return (await response.json()) as T;
}

export const CareerBrainApi = {
  search(query: string, top_k = 5) {
    return request<CareerBrainSearchResponse>('/career-brain/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k }),
    });
  },
  context(query: string, top_k = 5) {
    return request<CareerBrainContextResponse>('/career-brain/context', {
      method: 'POST',
      body: JSON.stringify({ query, top_k }),
    });
  },
  index() {
    return request<CareerBrainIndexResponse>('/career-brain/index', { method: 'POST' });
  },
};
