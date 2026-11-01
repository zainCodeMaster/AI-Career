import { apiClient } from './client';

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

export interface CareerBrainAnswerSource {
  id: string;
  source_type: string;
  title: string | null;
  score: number;
}

export interface CareerBrainAnswerRequest {
  query: string;
  top_k: number;
}

export interface CareerBrainAnswerResponse {
  query: string;
  answer: string;
  sources: CareerBrainAnswerSource[];
  model: string;
  confidence: 'high' | 'medium' | 'low';
  warning: string | null;
}

export const CareerBrainApi = {
  search(query: string, top_k = 5) {
    return apiClient.post<CareerBrainSearchResponse, { query: string; top_k: number }>('/career-brain/search', { query, top_k });
  },
  context(query: string, top_k = 5) {
    return apiClient.post<CareerBrainContextResponse, { query: string; top_k: number }>('/career-brain/context', { query, top_k });
  },
  index() {
    return apiClient.post<CareerBrainIndexResponse, {}>('/career-brain/index', {});
  },
  answer(query: string, top_k = 5) {
    return apiClient.post<CareerBrainAnswerResponse, { query: string; top_k: number }>('/career-brain/answer', { query, top_k });
  },
};
