import { useState, useEffect } from 'react';
import {
  Sparkles, Maximize, Palette, Sun, Scissors, Clock, Anchor, MessageSquare,
  Loader2, CheckCircle, Cpu, AlertCircle, Download,
} from 'lucide-react';
import { listEffects, applyEffect, pollJob, getVideoDownloadUrl } from '../services/api';
import type { EffectItem, EffectType, AIModel, ProcessingJob } from '../types';

const ICON_MAP: Record<string, React.ElementType> = {
  sparkles: Sparkles,
  maximize: Maximize,
  palette: Palette,
  sun: Sun,
  scissors: Scissors,
  clock: Clock,
  anchor: Anchor,
  'message-square': MessageSquare,
};

interface EffectsPanelProps {
  videoId: string | null;
  onJobComplete: (job: ProcessingJob) => void;
}

export default function EffectsPanel({ videoId, onJobComplete }: EffectsPanelProps) {
  const [effects, setEffects] = useState<EffectItem[]>([]);
  const [presets, setPresets] = useState<Record<string, string[]>>({});
  const [selectedModel, setSelectedModel] = useState<AIModel>('auto');
  const [intensity, setIntensity] = useState(0.5);
  const [activeJob, setActiveJob] = useState<ProcessingJob | null>(null);
  const [completedJob, setCompletedJob] = useState<ProcessingJob | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [category, setCategory] = useState('all');
  const [selectedPreset, setSelectedPreset] = useState<string>('');

  useEffect(() => {
    listEffects().then((res) => {
      setEffects(res.effects);
      if (res.presets) setPresets(res.presets);
    }).catch(() => {});
  }, []);

  const handleApply = async (effectType: EffectType) => {
    if (!videoId) return;
    setActiveJob(null);
    setCompletedJob(null);
    setErrorMsg(null);

    // Build effect-specific parameters
    const params: Record<string, unknown> = {};
    if (effectType === 'color_grading' && selectedPreset) {
      params.look = selectedPreset;
    } else if (effectType === 'style_transfer' && selectedPreset) {
      params.style = selectedPreset;
    }

    try {
      const res = await applyEffect(videoId, effectType, selectedModel, intensity, params);
      const jobId = res.job_id;

      // Poll for progress
      const finalJob = await pollJob(jobId, (job) => {
        setActiveJob(job);
      });

      setActiveJob(null);
      setCompletedJob(finalJob);
      onJobComplete(finalJob);
    } catch (err) {
      setActiveJob(null);
      setErrorMsg(err instanceof Error ? err.message : 'Processing failed');
    }
  };

  const categories = ['all', 'creative', 'enhancement', 'editing'];
  const filtered = category === 'all' ? effects : effects.filter((e) => e.category === category);

  // Show preset selector for color grading and style transfer
  const showPresets = category === 'all' || category === 'enhancement' || category === 'creative';
  const colorPresets = presets.color_grading || [];
  const stylePresets = presets.style_transfer || [];

  return (
    <div className="glass-card rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-400" />
          AI Effects
        </h3>
        <div className="flex items-center gap-1 text-xs">
          <Cpu className="w-3 h-3 text-zinc-500" />
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value as AIModel)}
            className="bg-zinc-800/80 text-zinc-300 border border-zinc-700/50 rounded px-2 py-1 text-xs focus:outline-none focus:border-purple-500/50"
          >
            <option value="auto">Auto Select</option>
            <option value="gemini">Gemini 2.0 Flash</option>
            <option value="claude">Claude Sonnet</option>
          </select>
        </div>
      </div>

      {/* Category filter */}
      <div className="flex gap-1">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`px-3 py-1 rounded-full text-xs font-medium capitalize transition-all ${
              category === cat
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                : 'text-zinc-500 hover:text-zinc-300 border border-transparent'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Preset selector */}
      {showPresets && (colorPresets.length > 0 || stylePresets.length > 0) && (
        <div className="space-y-1">
          <label className="text-xs text-zinc-500">Preset / Style</label>
          <select
            value={selectedPreset}
            onChange={(e) => setSelectedPreset(e.target.value)}
            className="w-full bg-zinc-800/80 text-zinc-300 border border-zinc-700/50 rounded px-2 py-1.5 text-xs focus:outline-none focus:border-purple-500/50"
          >
            <option value="">Default</option>
            {colorPresets.length > 0 && (
              <optgroup label="Color Grading">
                {colorPresets.map((p) => (
                  <option key={p} value={p}>{p.replace(/_/g, ' ')}</option>
                ))}
              </optgroup>
            )}
            {stylePresets.length > 0 && (
              <optgroup label="Style Transfer">
                {stylePresets.map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </optgroup>
            )}
          </select>
        </div>
      )}

      {/* Intensity slider */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs text-zinc-500">
          <span>Intensity</span>
          <span className="font-mono">{Math.round(intensity * 100)}%</span>
        </div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={intensity}
          onChange={(e) => setIntensity(Number(e.target.value))}
          className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
        />
      </div>

      {/* Processing progress */}
      {activeJob && (
        <div className="animate-slide-in bg-purple-500/5 border border-purple-500/20 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-purple-400 animate-spin" />
              <span className="text-xs text-purple-300 font-medium capitalize">{activeJob.status}</span>
            </div>
            <span className="text-xs text-zinc-500 font-mono">{activeJob.progress}%</span>
          </div>
          <div className="w-full bg-zinc-800 rounded-full h-1.5">
            <div
              className="bg-gradient-to-r from-purple-500 to-blue-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${activeJob.progress}%` }}
            />
          </div>
          <p className="text-xs text-zinc-500">{activeJob.message}</p>
        </div>
      )}

      {/* Effects grid */}
      <div className="grid grid-cols-2 gap-2 max-h-72 overflow-y-auto pr-1">
        {filtered.map((effect) => {
          const Icon = ICON_MAP[effect.icon] || Sparkles;
          const isProcessing = activeJob !== null;
          const isDisabled = !videoId || isProcessing;

          return (
            <button
              key={effect.type}
              onClick={() => handleApply(effect.type)}
              disabled={isDisabled}
              className={`effect-card glass-card rounded-lg p-3 text-left transition-all ${
                isDisabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-purple-500/5 hover:border-purple-500/20'
              }`}
            >
              <div className="flex items-center gap-2 mb-1.5">
                <div className="w-7 h-7 rounded-md flex items-center justify-center bg-zinc-800/80">
                  <Icon className="w-3.5 h-3.5 text-purple-400" />
                </div>
                <span className="text-xs font-medium text-zinc-200">{effect.name}</span>
              </div>
              <p className="text-xs text-zinc-500 leading-snug line-clamp-2">
                {effect.description}
              </p>
              <div className="mt-1.5 flex items-center gap-1">
                <span className="text-xs px-1.5 py-0.5 rounded bg-zinc-800/50 text-zinc-500">
                  {effect.recommended_model}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Success result */}
      {completedJob && completedJob.result && (
        <div className="animate-slide-in bg-green-500/5 border border-green-500/20 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-400" />
              <span className="text-xs text-green-300 font-medium">Effect Applied</span>
            </div>
            <a
              href={getVideoDownloadUrl(completedJob.result.output_video_id)}
              download
              className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300"
            >
              <Download className="w-3 h-3" />
              Download
            </a>
          </div>
          <div className="text-xs text-zinc-500 space-y-0.5">
            <p>
              Model: <span className="text-zinc-400">{completedJob.result.model_used}</span>
              {completedJob.result.ai_enhanced && (
                <span className="ml-1 text-purple-400">(AI enhanced)</span>
              )}
            </p>
            <p>Processing time: <span className="text-zinc-400">{completedJob.result.processing_time_seconds?.toFixed(1)}s</span></p>
            {completedJob.result.output_info && (
              <p>
                Output: <span className="text-zinc-400">
                  {(completedJob.result.output_info as Record<string, number>).width}x
                  {(completedJob.result.output_info as Record<string, number>).height}
                </span>
              </p>
            )}
          </div>
        </div>
      )}

      {/* Error display */}
      {errorMsg && (
        <div className="animate-slide-in bg-red-500/5 border border-red-500/20 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400" />
            <span className="text-xs text-red-300">{errorMsg}</span>
          </div>
        </div>
      )}

      {!videoId && (
        <p className="text-xs text-zinc-600 text-center py-2">
          Upload or select a video to apply effects
        </p>
      )}
    </div>
  );
}
