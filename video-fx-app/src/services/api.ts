import axios from 'axios';
import type { EffectType, AIModel, PlanTier, ProcessingJob } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 300000,
});

// --- Videos ---

export async function uploadVideo(file: File, onProgress?: (pct: number) => void) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/api/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total));
    },
  });
  return res.data;
}

export async function listVideos(page = 1, limit = 20) {
  const res = await api.get('/api/videos', { params: { page, limit } });
  return res.data;
}

export async function getVideo(id: string) {
  const res = await api.get(`/api/videos/${id}`);
  return res.data;
}

export async function deleteVideo(id: string) {
  const res = await api.delete(`/api/videos/${id}`);
  return res.data;
}

export function getVideoStreamUrl(videoId: string): string {
  return `${API_URL}/api/videos/${videoId}/stream`;
}

export function getVideoDownloadUrl(videoId: string): string {
  return `${API_URL}/api/videos/${videoId}/download`;
}

export function getVideoThumbnailUrl(videoId: string): string {
  return `${API_URL}/api/videos/${videoId}/thumbnail`;
}

// --- Effects & Jobs ---

export async function listEffects() {
  const res = await api.get('/api/effects');
  return res.data;
}

export async function applyEffect(
  videoId: string,
  effectType: EffectType,
  aiModel: AIModel = 'auto',
  intensity = 0.5,
  parameters: Record<string, unknown> = {}
) {
  const res = await api.post('/api/effects/apply', {
    video_id: videoId,
    effect_type: effectType,
    ai_model: aiModel,
    intensity,
    parameters,
  });
  return res.data;
}

export async function previewEffect(
  videoId: string,
  effectType: EffectType,
  aiModel: AIModel = 'auto',
  intensity = 0.5,
  parameters: Record<string, unknown> = {}
) {
  const res = await api.post('/api/effects/preview', {
    video_id: videoId,
    effect_type: effectType,
    ai_model: aiModel,
    intensity,
    parameters,
  });
  return res.data;
}

export async function getJobStatus(jobId: string): Promise<{ job: ProcessingJob }> {
  const res = await api.get(`/api/jobs/${jobId}`);
  return res.data;
}

export async function listJobs(videoId?: string) {
  const params: Record<string, string> = {};
  if (videoId) params.video_id = videoId;
  const res = await api.get('/api/jobs', { params });
  return res.data;
}

/** Poll a job until it completes or fails. Calls onProgress with each update. */
export async function pollJob(
  jobId: string,
  onProgress: (job: ProcessingJob) => void,
  intervalMs = 800,
): Promise<ProcessingJob> {
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const { job } = await getJobStatus(jobId);
        onProgress(job);
        if (job.status === 'completed') {
          resolve(job);
        } else if (job.status === 'failed') {
          reject(new Error(job.error || job.message || 'Processing failed'));
        } else {
          setTimeout(poll, intervalMs);
        }
      } catch (err) {
        reject(err);
      }
    };
    poll();
  });
}

// --- Storage (IPFS/Pinata) ---

export async function pinVideo(videoId: string, name?: string) {
  const res = await api.post('/api/storage/pin', { video_id: videoId, name });
  return res.data;
}

export async function getStorageInfo(cid: string) {
  const res = await api.get(`/api/storage/${cid}`);
  return res.data;
}

// --- Payments ---

export async function getPlans() {
  const res = await api.get('/api/payments/plans');
  return res.data;
}

export async function createCheckout(plan: PlanTier, successUrl: string, cancelUrl: string) {
  const res = await api.post('/api/payments/create-checkout', {
    plan,
    success_url: successUrl,
    cancel_url: cancelUrl,
  });
  return res.data;
}

export async function getSubscription() {
  const res = await api.get('/api/user/subscription');
  return res.data;
}

export async function getAppInfo() {
  const res = await api.get('/api/info');
  return res.data;
}
