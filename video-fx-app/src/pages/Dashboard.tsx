import { useState, useEffect } from 'react';
import { Film, HardDrive, Sparkles, Trash2, Clock, ArrowRight, Upload } from 'lucide-react';
import { listVideos, deleteVideo } from '../services/api';
import type { VideoMetadata } from '../types';

interface DashboardProps {
  onNavigate: (page: string) => void;
  onSelectVideo: (video: VideoMetadata) => void;
}

export default function Dashboard({ onNavigate, onSelectVideo }: DashboardProps) {
  const [videos, setVideos] = useState<VideoMetadata[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchVideos = async () => {
    setLoading(true);
    try {
      const res = await listVideos();
      setVideos(res.videos);
    } catch {
      // API may not be available
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleDelete = async (id: string) => {
    try {
      await deleteVideo(id);
      setVideos(videos.filter((v) => v.id !== id));
    } catch {
      // ignore
    }
  };

  const totalSize = videos.reduce((acc, v) => acc + v.size_bytes, 0);
  const totalEffects = videos.reduce((acc, v) => acc + v.effects_applied.length, 0);
  const pinnedCount = videos.filter((v) => v.ipfs_cid).length;

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Hero */}
      <div className="glass-card rounded-2xl p-8 bg-gradient-to-br from-purple-900/20 to-blue-900/20">
        <h1 className="text-3xl font-bold gradient-text mb-2">Welcome to VideoFX AI</h1>
        <p className="text-zinc-400 max-w-xl">
          AI-powered video effects platform for Indian creators. Apply motion graphics, upscaling,
          style transfer and more using Gemini & Claude AI models.
        </p>
        <div className="flex gap-3 mt-6">
          <button
            onClick={() => onNavigate('upload')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white text-sm font-medium hover:from-purple-500 hover:to-blue-500 transition-all"
          >
            <Upload className="w-4 h-4" />
            Upload Video
          </button>
          <button
            onClick={() => onNavigate('editor')}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-purple-500/30 text-purple-300 text-sm font-medium hover:bg-purple-500/10 transition-all"
          >
            <Film className="w-4 h-4" />
            Open Editor
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Videos', value: videos.length, icon: Film, color: 'purple' },
          { label: 'Storage', value: `${(totalSize / (1024 * 1024)).toFixed(0)} MB`, icon: HardDrive, color: 'blue' },
          { label: 'Effects Applied', value: totalEffects, icon: Sparkles, color: 'violet' },
          { label: 'IPFS Pinned', value: pinnedCount, icon: HardDrive, color: 'emerald' },
        ].map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="glass-card rounded-xl p-4">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg bg-${stat.color}-500/10 flex items-center justify-center`}>
                  <Icon className={`w-5 h-5 text-${stat.color}-400`} />
                </div>
                <div>
                  <p className="text-2xl font-bold text-zinc-100">{stat.value}</p>
                  <p className="text-xs text-zinc-500">{stat.label}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Video Library */}
      <div className="glass-card rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-zinc-200">Video Library</h2>
          <button
            onClick={() => onNavigate('upload')}
            className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
          >
            Upload new <ArrowRight className="w-3 h-3" />
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-zinc-600">Loading...</div>
        ) : videos.length === 0 ? (
          <div className="text-center py-12">
            <Film className="w-16 h-16 mx-auto text-zinc-800 mb-3" />
            <p className="text-zinc-500">No videos yet</p>
            <p className="text-zinc-600 text-sm mt-1">Upload your first video to get started</p>
          </div>
        ) : (
          <div className="space-y-2">
            {videos.map((video) => (
              <div
                key={video.id}
                className="flex items-center gap-4 p-3 rounded-lg hover:bg-white/5 transition-all cursor-pointer group"
                onClick={() => {
                  onSelectVideo(video);
                  onNavigate('editor');
                }}
              >
                <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
                  <Film className="w-6 h-6 text-purple-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-zinc-200 truncate">
                    {video.original_name}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-zinc-500 mt-0.5">
                    <span>{(video.size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
                    <span>{video.format?.toUpperCase()}</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(video.created_at * 1000).toLocaleDateString()}
                    </span>
                    {video.effects_applied.length > 0 && (
                      <span className="flex items-center gap-1 text-purple-400">
                        <Sparkles className="w-3 h-3" />
                        {video.effects_applied.length} effects
                      </span>
                    )}
                    {video.ipfs_cid && (
                      <span className="text-emerald-400">IPFS</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectVideo(video);
                      onNavigate('editor');
                    }}
                    className="px-3 py-1.5 rounded-md bg-purple-500/20 text-purple-300 text-xs hover:bg-purple-500/30"
                  >
                    Edit
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(video.id);
                    }}
                    className="p-1.5 rounded-md hover:bg-red-500/10 text-zinc-500 hover:text-red-400"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
