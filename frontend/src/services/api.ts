import axios, { AxiosError, AxiosInstance } from 'axios';

// Use relative URL so the app works behind nginx proxy regardless of hostname/IP.
// Falls back to absolute URL only for local `npm run dev` (Vite dev server proxies /api).
const API_BASE = import.meta.env.DEV
  ? ((import.meta.env.VITE_API_URL as string | undefined) || 'http://localhost:8000')
  : '';
const API_V1 = `${API_BASE}/api/v1`;

const HEALTH_TIMEOUT_MS = 8000;
const DEFAULT_TIMEOUT_MS = 30000;
const CHAT_TIMEOUT_MS = 300000;
const UPLOAD_TIMEOUT_MS = 180000;

export interface Citation {
  source_id: string;
  source_name: string | null;
  chunk_id: string | null;
  score: number | null;
  snippet: string | null;
  section?: string | null;
  page?: number | null;
  file_path?: string | null;
}

export interface ChatHistoryEntry {
  id: string;
  question: string;
  answer: string;
  timestamp: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  model: string;
  latency_ms: number;
  conversation_id: string | null;
  mode?: string;
  confidence?: string;
  metadata?: Record<string, unknown>;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
}

export interface IngestStatusData {
  ingest_id: string;
  status: 'pending' | 'processing' | 'done' | 'failed';
  message?: string;
  created_at: string;
  completed_at?: string;
  document_names?: string[];
}

export interface IngestHistoryResponse {
  items: IngestStatusData[];
}

export interface DocumentsResponse {
  files: string[];
}

export interface SystemDataSourcesResponse {
  vector_store: {
    backend: string;
    index_storage_path: string;
    index_db_path: string;
    qdrant_path: string;
    qdrant_collection: string;
  };
  documents: {
    path: string;
    file_count: number;
    files: string[];
  };
  models: {
    generation_model: string;
    reranker_model: string;
    embedding_model: string;
    llm_reranker_enabled: boolean;
  };
  index: {
    ready: boolean;
    built_at: string | null;
    chunk_count: number;
    source_count: number;
    embedding_backend: string;
    chunker_version: string;
    schema_version: number;
    manifest: Record<string, unknown>;
  };
  ingest_store: {
    mode: string;
    count: number;
    sqlite: {
      enabled: boolean;
      path: string;
      count: number;
    };
  };
  chat_store: {
    mode: string;
    count: number;
    sqlite: {
      enabled: boolean;
      path: string;
      count: number;
    };
  };
  index_tables: {
    sources: number;
    chunks: number;
    runs: number;
  };
}

export interface NormalizedApiError {
  status?: number;
  code?: string;
  message: string;
  raw: unknown;
}

export interface StreamEvent {
  token?: string;
  done?: boolean;
  ping?: { ts?: number };
  meta?: Record<string, unknown>;
  error?: { code?: string; message?: string; hint?: string };
}

export interface StreamCallbacks {
  onEvent?: (event: StreamEvent) => void;
  onToken?: (token: string) => void;
}

function buildHeaders(): Record<string, string> {
  const apiKey = (import.meta.env.VITE_API_KEY as string | undefined) || '';
  return apiKey ? { 'Content-Type': 'application/json', 'X-API-Key': apiKey } : { 'Content-Type': 'application/json' };
}

function createClient(timeout: number): AxiosInstance {
  return axios.create({
    baseURL: API_BASE,
    timeout,
    headers: buildHeaders(),
  });
}

export function normalizeApiError(error: unknown): NormalizedApiError {
  const axiosError = error as AxiosError<{ detail?: unknown; error?: { message?: string; code?: string } }>;
  const status = axiosError.response?.status;

  if (axiosError.code === 'ECONNABORTED') {
    return {
      status,
      code: axiosError.code,
      message: 'Yêu cầu quá lâu, có thể backend đang sync index hoặc model phản hồi chậm.',
      raw: error,
    };
  }

  if (!axiosError.response) {
    const fallbackMessage = error instanceof Error ? error.message : 'Không kết nối được tới backend.';
    return {
      code: axiosError.code,
      message: fallbackMessage,
      raw: error,
    };
  }

  const detail = axiosError.response.data?.detail;
  const detailMsg = typeof detail === 'string' ? detail : undefined;
  return {
    status,
    code: axiosError.response.data?.error?.code || axiosError.code,
    message:
      detailMsg ||
      axiosError.response.data?.error?.message ||
      axiosError.message ||
      'Đã xảy ra lỗi không xác định.',
    raw: error,
  };
}

class APIClient {
  private healthClient = createClient(HEALTH_TIMEOUT_MS);
  private defaultClient = createClient(DEFAULT_TIMEOUT_MS);
  private chatClient = createClient(CHAT_TIMEOUT_MS);
  private uploadClient = createClient(UPLOAD_TIMEOUT_MS);

  async healthCheck() {
    const response = await this.healthClient.get('/health');
    return response.data;
  }

  async chat(question: string, topK: number = 5, includeCitations: boolean = true) {
    const response = await this.chatClient.post<ChatResponse>(`${API_V1}/chat`, {
      question,
      top_k: topK,
      include_citations: includeCitations,
    });
    return response.data;
  }

  async chatStream(question: string, topK: number = 5, includeCitations: boolean = true, callbacks?: StreamCallbacks) {
    const response = await fetch(`${API_V1}/chat/stream`, {
      method: 'POST',
      headers: buildHeaders(),
      body: JSON.stringify({ question, top_k: topK, include_citations: includeCitations }),
    });

    if (!response.ok) {
      let message = `Stream request failed with status ${response.status}`;
      try {
        const payload = await response.json();
        message = payload?.error?.message || payload?.message || message;
      } catch {
        // ignore parse issues
      }
      throw new Error(message);
    }
    if (!response.body) {
      throw new Error('Stream response body is empty');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';
    let aggregated = '';
    let streamError: StreamEvent['error'];
    let finalResult: Partial<ChatResponse> | null = null;

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split('\n\n');
      buffer = events.pop() ?? '';

      for (const block of events) {
        const dataLine = block
          .split('\n')
          .map((line) => line.trim())
          .find((line) => line.startsWith('data:'));
        if (!dataLine) continue;

        const payload = dataLine.slice(5).trim();
        let parsed: StreamEvent;
        try {
          parsed = JSON.parse(payload) as StreamEvent;
        } catch {
          continue;
        }

        callbacks?.onEvent?.(parsed);

        if (parsed.token) {
          aggregated += parsed.token;
          callbacks?.onToken?.(parsed.token);
        }

        if ((parsed as StreamEvent & { result?: Partial<ChatResponse> }).result) {
          finalResult = (parsed as StreamEvent & { result?: Partial<ChatResponse> }).result || null;
        }

        if (parsed.error) {
          streamError = parsed.error;
          break;
        }
        if (parsed.done) {
          break;
        }
      }

      if (streamError) break;
    }

    if (streamError) {
      throw new Error(streamError.message || 'Stream error');
    }

    return {
      answer: (finalResult?.answer as string) || aggregated,
      citations: finalResult?.citations || [],
      model: (finalResult?.model as string) || 'stream',
      latency_ms: Number(finalResult?.latency_ms || 0),
      conversation_id: (finalResult?.conversation_id as string | null) || null,
      mode: finalResult?.mode as string | undefined,
      confidence: finalResult?.confidence as string | undefined,
      metadata: finalResult?.metadata as Record<string, unknown> | undefined,
    } as ChatResponse;
  }

  async getHistory() {
    const response = await this.defaultClient.get<ApiResponse<{ messages: ChatHistoryEntry[] }>>(`${API_V1}/history`);
    return response.data.data?.messages || [];
  }

  async clearHistory() {
    const response = await this.defaultClient.delete<ApiResponse>(`${API_V1}/history`);
    return response.data.data;
  }

  async startIngest() {
    const response = await this.defaultClient.post<ApiResponse<{ ingest_id: string; document_names?: string[]; message?: string; ingested_chunks?: number }>>(`${API_V1}/ingest`);
    return response.data.data;
  }

  async getIngestStatus(ingestId: string) {
    const response = await this.defaultClient.get<ApiResponse<IngestStatusData>>(`${API_V1}/ingest/status/${ingestId}`);
    return response.data.data;
  }

  async getIngestHistory(limit: number = 20) {
    const response = await this.defaultClient.get<ApiResponse<IngestHistoryResponse>>(`${API_V1}/ingest/history?limit=${limit}`);
    return response.data.data?.items || [];
  }

  async uploadFiles(files: FileList) {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    const response = await this.uploadClient.post<ApiResponse<{ files: string[] }>>(`${API_V1}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data.data!;
  }

  async listDocuments() {
    const response = await this.defaultClient.get<ApiResponse<DocumentsResponse>>(`${API_V1}/documents`);
    return response.data.data?.files || [];
  }

  async deleteDocument(filename: string) {
    const response = await this.defaultClient.delete<ApiResponse<{ filename: string }>>(`${API_V1}/documents/${encodeURIComponent(filename)}`);
    return response.data.data;
  }

  async getSystemDataSources() {
    const response = await this.defaultClient.get<ApiResponse<SystemDataSourcesResponse>>(`${API_V1}/system/data-sources`);
    return response.data.data;
  }
}

export const apiClient = new APIClient();
