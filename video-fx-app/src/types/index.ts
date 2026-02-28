export type VideoStatus = 'uploading' | 'uploaded' | 'processing' | 'completed' | 'failed';

export type EffectType =
  | 'motion_graphics'
  | 'upscaling'
  | 'style_transfer'
  | 'color_grading'
  | 'background_removal'
  | 'slow_motion'
  | 'stabilization'
  | 'auto_caption';

export type AIModel = 'gemini' | 'claude' | 'auto';

export type PlanTier = 'free' | 'pro' | 'enterprise';

export type JobStatus = 'queued' | 'analyzing' | 'processing' | 'encoding' | 'completed' | 'failed';

export interface VideoMetadata {
  id: string;
  filename: string;
  original_name: string;
  size_bytes: number;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  format: string | null;
  status: VideoStatus;
  ipfs_cid: string | null;
  ipfs_url: string | null;
  created_at: number;
  effects_applied: string[];
}

export interface EffectItem {
  type: EffectType;
  name: string;
  description: string;
  icon: string;
  recommended_model: string;
  category: string;
  produces_output: boolean;
}

export interface ProcessingJob {
  id: string;
  video_id: string;
  effect_type: string;
  ai_model: string;
  intensity: number;
  status: JobStatus;
  progress: number;
  message: string;
  result: {
    output_video_id: string;
    processing_time_seconds: number;
    model_used: string;
    ai_enhanced: boolean;
    effect_params: Record<string, unknown>;
    input_info: Record<string, unknown>;
    output_info: Record<string, unknown>;
  } | null;
  error: string | null;
  created_at: number;
  started_at: number | null;
  completed_at: number | null;
  processing_time_seconds: number | null;
}

export interface PricingPlan {
  tier: PlanTier;
  name: string;
  price_inr: number;
  price_display: string;
  features: string[];
  max_video_size_mb: number;
  max_monthly_exports: number;
  ai_models_available: string[];
}

export interface SubscriptionStatus {
  tier: PlanTier;
  active: boolean;
  exports_used: number;
  exports_limit: number;
  storage_used_mb: number;
  storage_limit_mb: number;
}

export interface TimelineTrack {
  id: string;
  video_id: string;
  name: string;
  start_time: number;
  end_time: number;
  effects: EffectType[];
  layer: number;
}

export interface Project {
  id: string;
  name: string;
  tracks: TimelineTrack[];
  duration: number;
}
