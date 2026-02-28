import { useState } from 'react';
import { HardDrive, Upload, ExternalLink, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { pinVideo } from '../services/api';
import type { VideoMetadata } from '../types';

interface StoragePanelProps {
  video: VideoMetadata | null;
  onPinned: (cid: string, url: string) => void;
}

export default function StoragePanel({ video, onPinned }: StoragePanelProps) {
  const [pinning, setPinning] = useState(false);
  const [pinResult, setPinResult] = useState<{ cid: string; url: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handlePin = async () => {
    if (!video) return;
    setPinning(true);
    setError(null);
    try {
      const res = await pinVideo(video.id, video.original_name);
      setPinResult({ cid: res.ipfs_cid, url: res.ipfs_url });
      onPinned(res.ipfs_cid, res.ipfs_url);
    } catch {
      setError('Failed to pin video to IPFS');
    } finally {
      setPinning(false);
    }
  };

  return (
    <div className="glass-card rounded-xl p-4 space-y-3">
      <h3 className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
        <HardDrive className="w-4 h-4 text-purple-400" />
        IPFS Storage
      </h3>

      <p className="text-xs text-zinc-500">
        Pin your videos to IPFS via Pinata for decentralized, permanent storage.
      </p>

      {video ? (
        <div className="space-y-3">
          <div className="bg-zinc-900/50 rounded-lg p-3">
            <p className="text-xs text-zinc-400 truncate">{video.original_name}</p>
            <p className="text-[10px] text-zinc-600 mt-0.5">
              {(video.size_bytes / (1024 * 1024)).toFixed(1)} MB &bull; {video.format?.toUpperCase()}
            </p>
          </div>

          {video.ipfs_cid ? (
            <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-3 space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-xs text-green-300 font-medium">Pinned to IPFS</span>
              </div>
              <p className="text-[10px] text-zinc-500 break-all font-mono">{video.ipfs_cid}</p>
              {video.ipfs_url && (
                <a
                  href={video.ipfs_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300"
                >
                  View on IPFS <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          ) : pinResult ? (
            <div className="bg-green-500/5 border border-green-500/20 rounded-lg p-3 space-y-2 animate-slide-in">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-xs text-green-300 font-medium">Successfully Pinned</span>
              </div>
              <p className="text-[10px] text-zinc-500 break-all font-mono">{pinResult.cid}</p>
              <a
                href={pinResult.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300"
              >
                View on IPFS <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          ) : (
            <button
              onClick={handlePin}
              disabled={pinning}
              className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white text-sm font-medium hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 transition-all"
            >
              {pinning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Pinning to IPFS...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Pin to IPFS
                </>
              )}
            </button>
          )}

          {error && (
            <div className="flex items-center gap-2 text-xs text-red-400">
              <AlertCircle className="w-3 h-3" />
              {error}
            </div>
          )}
        </div>
      ) : (
        <p className="text-xs text-zinc-600 text-center py-4">Select a video to pin to IPFS</p>
      )}
    </div>
  );
}
