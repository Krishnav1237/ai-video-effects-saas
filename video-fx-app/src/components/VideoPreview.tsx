import { Film, Play, Pause, Volume2, VolumeX, Maximize, Download, ArrowLeftRight } from 'lucide-react';
import { useState, useRef, useEffect, useCallback } from 'react';
import { getVideoStreamUrl, getVideoDownloadUrl } from '../services/api';
import type { VideoMetadata } from '../types';

interface VideoPreviewProps {
  video: VideoMetadata | null;
  outputVideo: VideoMetadata | null;
  showCompare?: boolean;
}

export default function VideoPreview({ video, outputVideo, showCompare = false }: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [comparing, setComparing] = useState(false);
  const [videoLoaded, setVideoLoaded] = useState(false);

  const activeVideo = comparing && outputVideo ? outputVideo : video;
  const streamUrl = activeVideo ? getVideoStreamUrl(activeVideo.id) : null;

  const formatTime = (s: number) => {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
  };

  const togglePlay = useCallback(() => {
    const el = videoRef.current;
    if (!el) return;
    if (isPlaying) {
      el.pause();
    } else {
      el.play().catch(() => {});
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleTimeUpdate = useCallback(() => {
    const el = videoRef.current;
    if (el) setCurrentTime(el.currentTime);
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    const el = videoRef.current;
    if (el) {
      setDuration(el.duration);
      setVideoLoaded(true);
    }
  }, []);

  const handleSeek = useCallback((val: number) => {
    const el = videoRef.current;
    if (el) {
      el.currentTime = val;
      setCurrentTime(val);
    }
  }, []);

  useEffect(() => {
    setVideoLoaded(false);
    setCurrentTime(0);
    setIsPlaying(false);
  }, [activeVideo?.id]);

  const downloadUrl = outputVideo
    ? getVideoDownloadUrl(outputVideo.id)
    : video
    ? getVideoDownloadUrl(video.id)
    : null;

  return (
    <div className="glass-card rounded-xl overflow-hidden h-full flex flex-col">
      {/* Video area */}
      <div className="relative aspect-video bg-zinc-950 flex items-center justify-center flex-shrink-0">
        {streamUrl ? (
          <>
            <video
              ref={videoRef}
              src={streamUrl}
              className="w-full h-full object-contain"
              muted={isMuted}
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onEnded={() => setIsPlaying(false)}
              playsInline
            />
            {/* Play button overlay (only when paused and loaded) */}
            {!isPlaying && videoLoaded && (
              <button
                onClick={togglePlay}
                className="absolute inset-0 flex items-center justify-center group"
              >
                <div className="w-16 h-16 rounded-full bg-purple-500/20 flex items-center justify-center backdrop-blur-sm group-hover:bg-purple-500/30 transition-all">
                  <Play className="w-7 h-7 text-white ml-1" />
                </div>
              </button>
            )}
            {/* Compare badge */}
            {comparing && outputVideo && (
              <div className="absolute top-3 left-3 bg-purple-600/80 backdrop-blur-sm rounded-md px-2 py-1 text-xs text-white font-medium">
                Processed Output
              </div>
            )}
            {!comparing && video && (
              <div className="absolute top-3 left-3 bg-zinc-800/80 backdrop-blur-sm rounded-md px-2 py-1 text-xs text-zinc-300">
                {video.original_name}
                {video.width && video.height && (
                  <span className="text-zinc-500 ml-1.5">{video.width}x{video.height}</span>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="text-center">
            <Film className="w-20 h-20 text-zinc-800 mx-auto mb-3" />
            <p className="text-zinc-600 text-sm">No video selected</p>
            <p className="text-zinc-700 text-xs mt-1">Upload or select a video to preview</p>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="px-4 py-3 space-y-2">
        {/* Progress bar */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500 w-10 font-mono">{formatTime(currentTime)}</span>
          <div className="flex-1 relative">
            <input
              type="range"
              min={0}
              max={duration || 1}
              step={0.01}
              value={currentTime}
              onChange={(e) => handleSeek(Number(e.target.value))}
              className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-purple-500"
            />
          </div>
          <span className="text-xs text-zinc-500 w-10 font-mono text-right">{formatTime(duration)}</span>
        </div>

        {/* Control buttons */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <button
              onClick={togglePlay}
              disabled={!streamUrl}
              className="p-1.5 rounded hover:bg-white/5 text-zinc-400 hover:text-white transition-colors disabled:opacity-30"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>
            <button
              onClick={() => {
                setIsMuted(!isMuted);
                if (videoRef.current) videoRef.current.muted = !isMuted;
              }}
              className="p-1.5 rounded hover:bg-white/5 text-zinc-400 hover:text-white transition-colors"
            >
              {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
            </button>
          </div>

          <div className="flex items-center gap-1">
            {/* Compare toggle */}
            {outputVideo && showCompare && (
              <button
                onClick={() => setComparing(!comparing)}
                className={`p-1.5 rounded transition-colors ${
                  comparing
                    ? 'bg-purple-500/20 text-purple-400'
                    : 'hover:bg-white/5 text-zinc-400 hover:text-white'
                }`}
                title="Compare original vs processed"
              >
                <ArrowLeftRight className="w-4 h-4" />
              </button>
            )}
            {/* Download */}
            {downloadUrl && (
              <a
                href={downloadUrl}
                download
                className="p-1.5 rounded hover:bg-white/5 text-zinc-400 hover:text-white transition-colors"
                title="Download video"
              >
                <Download className="w-4 h-4" />
              </a>
            )}
            {/* Fullscreen */}
            <button
              onClick={() => videoRef.current?.requestFullscreen()}
              className="p-1.5 rounded hover:bg-white/5 text-zinc-400 hover:text-white transition-colors"
            >
              <Maximize className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
