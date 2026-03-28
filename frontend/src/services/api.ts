import axios, { AxiosInstance } from "axios";

const API_BASE =
  (import.meta.env.VITE_API_URL as string | undefined) ||
  "http://localhost:8000";
const API_V1 = `${API_BASE}/api/v1`;

// Types
export interface Citation {
  source_id: string;
  source_name: string | null;
  chunk_id: string | null;
  score: number | null;
  snippet: string | null;
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
}

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface IngestStatusData {
  ingest_id: string;
  status: "pending" | "processing" | "done" | "failed";
  message?: string;
  created_at: string;
  completed_at?: string;
}

// API Client
class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE,
      timeout: 50000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  async healthCheck() {
    const response = await this.client.get("/health");
    return response.data;
  }

  async chat(
    question: string,
    topK: number = 5,
    includeCitations: boolean = true
  ) {
    const response = await this.client.post<ChatResponse>(`${API_V1}/chat`, {
      question,
      top_k: topK,
      include_citations: includeCitations,
    });
    return response.data;
  }

  async getHistory() {
    const response = await this.client.get<ApiResponse>(`${API_V1}/history`);
    return response.data.data?.messages || [];
  }

  async clearHistory() {
    const response = await this.client.delete<ApiResponse>(`${API_V1}/history`);
    return response.data.data;
  }

  async startIngest() {
    const response = await this.client.post<ApiResponse>(`${API_V1}/ingest`);
    return response.data.data;
  }

  async getIngestStatus(ingestId: string) {
    const response = await this.client.get<ApiResponse<IngestStatusData>>(
      `${API_V1}/ingest/status/${ingestId}`
    );
    return response.data.data;
  }

  async uploadFiles(files: FileList) {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append("files", file));
    const response = await this.client.post<ApiResponse<{ files: string[] }>>(
      `${API_V1}/upload`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return response.data.data!;
  }
}

export const apiClient = new APIClient();
