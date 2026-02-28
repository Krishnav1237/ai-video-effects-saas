import { useState, useCallback, useRef } from 'react';
import { Upload, X, CheckCircle, AlertCircle, Film } from 'lucide-react';
import { uploadVideo } from '../services/api';
import type { VideoMetadata } from '../types';

interface VideoUploaderProps {
  onUploadComplete: (video: VideoMetadata) => void;
}

export default function VideoUploader({ onUploadComplete }: VideoUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setError(null);
      setSuccess(false);

      if (file.size > 500 * 1024 * 1024) {
        setError('File too large. Maximum size is 500MB.');
        return;
      }

      const ext = file.name.split('.').pop()?.toLowerCase();
      if (!['mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v'].includes(ext || '')) {
        setError('Unsupported format. Use MP4, MOV, AVI, MKV, or WebM.');
        return;
      }

      setUploading(true);
      setProgress(0);

      try {
        const res = await uploadVideo(file, (pct) => setProgress(pct));
        setSuccess(true);
        onUploadComplete(res.video);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Upload failed';
        setError(msg);
      } finally {
        setUploading(false);
      }
    },
    [onUploadComplete]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setIsDragOver(false), []);

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className={`upload-zone rounded-2xl p-12 text-center cursor-pointer ${isDragOver ? 'dragover' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />

        {uploading ? (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-purple-500/20 flex items-center justify-center processing-glow">
              <Film className="w-8 h-8 text-purple-400 animate-pulse" />
            </div>
            <p className="text-zinc-300 font-medium">Uploading... {progress}%</p>
            <div className="w-full bg-zinc-800 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-purple-500 to-blue-500 h-full rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-zinc-500">Chunked upload for 1080p videos up to 500MB</p>
          </div>
        ) : success ? (
          <div className="space-y-3">
            <CheckCircle className="w-16 h-16 mx-auto text-green-400" />
            <p className="text-green-300 font-medium">Upload complete!</p>
            <button
              className="text-sm text-purple-400 hover:text-purple-300"
              onClick={(e) => {
                e.stopPropagation();
                setSuccess(false);
              }}
            >
              Upload another
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="w-16 h-16 mx-auto rounded-full bg-purple-500/10 flex items-center justify-center">
              <Upload className="w-8 h-8 text-purple-400" />
            </div>
            <div>
              <p className="text-zinc-200 font-medium text-lg">Drop your video here</p>
              <p className="text-zinc-500 text-sm mt-1">or click to browse</p>
            </div>
            <div className="flex items-center justify-center gap-4 text-xs text-zinc-600">
              <span>MP4, MOV, AVI, MKV, WebM</span>
              <span className="w-1 h-1 rounded-full bg-zinc-700" />
              <span>Up to 500MB</span>
              <span className="w-1 h-1 rounded-full bg-zinc-700" />
              <span>1080p supported</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 animate-slide-in">
          <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
          <p className="text-red-300 text-sm">{error}</p>
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-4 h-4 text-red-400 hover:text-red-300" />
          </button>
        </div>
      )}
    </div>
  );
}
