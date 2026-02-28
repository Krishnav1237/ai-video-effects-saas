import VideoUploader from '../components/VideoUploader';
import { Film, Zap, Shield, Globe } from 'lucide-react';
import type { VideoMetadata } from '../types';

interface UploadPageProps {
  onUploadComplete: (video: VideoMetadata) => void;
}

export default function UploadPage({ onUploadComplete }: UploadPageProps) {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold gradient-text mb-2">Upload Video</h1>
        <p className="text-zinc-500">
          Upload your video to start applying AI-powered effects
        </p>
      </div>

      <VideoUploader onUploadComplete={onUploadComplete} />

      {/* Features */}
      <div className="grid grid-cols-3 gap-4 mt-8">
        {[
          {
            icon: Zap,
            title: 'Low Latency',
            desc: 'Chunked uploads for fast 1080p video processing under 500MB',
          },
          {
            icon: Shield,
            title: 'Secure Storage',
            desc: 'Videos stored securely with optional IPFS decentralized pinning',
          },
          {
            icon: Globe,
            title: 'Multi-Model AI',
            desc: 'Gemini & Claude orchestration for best-in-class effects',
          },
        ].map((feat) => {
          const Icon = feat.icon;
          return (
            <div key={feat.title} className="glass-card rounded-xl p-5 text-center">
              <div className="w-12 h-12 mx-auto rounded-xl bg-purple-500/10 flex items-center justify-center mb-3">
                <Icon className="w-6 h-6 text-purple-400" />
              </div>
              <h3 className="text-sm font-semibold text-zinc-200 mb-1">{feat.title}</h3>
              <p className="text-xs text-zinc-500">{feat.desc}</p>
            </div>
          );
        })}
      </div>

      {/* Supported formats */}
      <div className="glass-card rounded-xl p-5">
        <h3 className="text-sm font-semibold text-zinc-300 flex items-center gap-2 mb-3">
          <Film className="w-4 h-4 text-purple-400" />
          Supported Formats
        </h3>
        <div className="grid grid-cols-6 gap-2">
          {['MP4', 'MOV', 'AVI', 'MKV', 'WebM', 'M4V'].map((fmt) => (
            <div
              key={fmt}
              className="text-center py-2 rounded-lg bg-zinc-900/50 border border-zinc-800/50 text-xs text-zinc-400 font-medium"
            >
              {fmt}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
