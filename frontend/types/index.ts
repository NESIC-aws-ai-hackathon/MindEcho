// ── Auth ──
export interface AuthResponse {
  user_id: string;
  access_token: string;
  token_type: string;
}

// ── Session ──
export type SessionStatus =
  | "created"
  | "media_uploaded"
  | "questions_generated"
  | "questions_answered"
  | "emotions_selected"
  | "generated"
  | "completed";

export interface SessionResponse {
  id: string;
  user_id: string;
  status: string;
  media_type: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface SessionListResponse {
  items: SessionResponse[];
  total: number;
  page: number;
  per_page: number;
}

// ── Media ──
export interface MediaFileSchema {
  id: string;
  session_id: string;
  user_id: string;
  media_type: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  created_at: string;
}

export interface ImageAnalysis {
  colors: string[];
  composition: string;
  mood: string;
  subjects: string[];
  atmosphere: string;
  texture: string;
  light_direction: string;
  emotional_impression: string;
  image_category: string;
  style_characteristics: string;
}

export interface MusicAnalysis {
  title: string | null;
  artist: string | null;
  album: string | null;
  genre: string | null;
  year: number | null;
  duration_seconds: number | null;
  bpm: number | null;
  key: string | null;
  chord_progression: string | null;
  rhythm: string;
  tempo: string;
  mood: string;
  energy_level: string;
  emotional_impression: string;
}

export interface MediaUploadResponse {
  media_file: MediaFileSchema;
  image_analysis: ImageAnalysis | null;
  music_analysis: MusicAnalysis | null;
}

export interface MediaDetailResponse extends MediaUploadResponse {
  presigned_url: string;
}

// ── Cognitive ──
export interface Choice {
  label: string;
  text: string;
}

export interface ContextQuestionSchema {
  id: string;
  question_order: number;
  question_text: string;
  choices: Choice[];
  selected_choice: string | null;
  other_text: string | null;
}

export interface QuestionsResponse {
  session_id: string;
  questions: ContextQuestionSchema[];
}

export interface SubmitResponseItem {
  question_id: string;
  selected_choice: string;
  other_text?: string;
}

export interface EmotionCandidateSchema {
  id: string;
  candidate_order: number;
  emotion_label: string;
  emotion_description: string;
  is_selected: boolean;
}

export interface EmotionsResponse {
  session_id: string;
  candidates: EmotionCandidateSchema[];
}

// ── Synthesis ──
export interface FormatInfo {
  id: string;
  name: string;
  description: string;
  min_chars: number;
  max_chars: number;
  is_default: boolean;
}

export interface FormatsResponse {
  formats: FormatInfo[];
}

export interface GeneratedTextSchema {
  session_id: string;
  output_format: string;
  generated_content: string;
  generation_count: number;
  created_at: string;
  updated_at: string;
}

// ── Error ──
export interface ApiErrorDetail {
  code: string;
  message: string;
  details: Record<string, unknown> | null;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}
