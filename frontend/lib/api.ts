import { getToken } from "./auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Don't set Content-Type for FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let code = "UNKNOWN";
    let message = "エラーが発生しました";
    try {
      const body = await res.json();
      if (body.error) {
        code = body.error.code || code;
        message = body.error.message || message;
      } else if (body.detail) {
        message = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore parse error
    }
    throw new ApiError(res.status, code, message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ── Auth ──
import type {
  AuthResponse,
  SessionListResponse,
  SessionResponse,
  MediaUploadResponse,
  MediaDetailResponse,
  QuestionsResponse,
  EmotionsResponse,
  SubmitResponseItem,
  FormatsResponse,
  GeneratedTextSchema,
} from "@/types";

export async function register(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function deleteAccount(): Promise<void> {
  return request<void>("/api/auth/account", { method: "DELETE" });
}

// ── Sessions ──
export async function createSession(): Promise<SessionResponse> {
  return request<SessionResponse>("/api/data/sessions", { method: "POST" });
}

export async function listSessions(page = 1, perPage = 20): Promise<SessionListResponse> {
  return request<SessionListResponse>(`/api/data/sessions?page=${page}&per_page=${perPage}`);
}

export async function deleteSession(sessionId: string): Promise<void> {
  return request<void>(`/api/data/sessions/${sessionId}`, { method: "DELETE" });
}

// ── Media ──
export async function uploadMedia(
  sessionId: string,
  file: File,
  mediaType?: string,
): Promise<MediaUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("session_id", sessionId);
  if (mediaType) formData.append("media_type", mediaType);

  return request<MediaUploadResponse>("/api/media/upload", {
    method: "POST",
    body: formData,
  });
}

export async function getMediaDetail(mediaId: string): Promise<MediaDetailResponse> {
  return request<MediaDetailResponse>(`/api/media/${mediaId}`);
}

// ── Cognitive ──
export async function getQuestions(sessionId: string): Promise<QuestionsResponse> {
  return request<QuestionsResponse>(`/api/cognitive/questions/${sessionId}`);
}

export async function submitResponses(
  sessionId: string,
  responses: SubmitResponseItem[],
): Promise<void> {
  return request<void>("/api/cognitive/responses", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, responses }),
  });
}

export async function submitFreeText(sessionId: string, content: string): Promise<void> {
  return request<void>("/api/cognitive/free-text", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, content }),
  });
}

export async function completeQuestions(sessionId: string): Promise<EmotionsResponse> {
  return request<EmotionsResponse>("/api/cognitive/complete-questions", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function getEmotions(sessionId: string): Promise<EmotionsResponse> {
  return request<EmotionsResponse>(`/api/cognitive/emotions/${sessionId}`);
}

export async function selectEmotions(
  sessionId: string,
  candidateIds: string[],
): Promise<void> {
  return request<void>("/api/cognitive/emotions", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, candidate_ids: candidateIds }),
  });
}

// ── Synthesis ──
export async function getFormats(): Promise<FormatsResponse> {
  return request<FormatsResponse>("/api/synthesis/formats");
}

export async function generateText(
  sessionId: string,
  outputFormat: string,
): Promise<GeneratedTextSchema> {
  return request<GeneratedTextSchema>("/api/synthesis/generate", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, output_format: outputFormat }),
  });
}

export async function getGeneratedText(sessionId: string): Promise<GeneratedTextSchema> {
  return request<GeneratedTextSchema>(`/api/synthesis/${sessionId}`);
}
