import { useState, useCallback } from 'react';
import VideoPreview from '../components/VideoPreview';
import Timeline from '../components/Timeline';
import EffectsPanel from '../components/EffectsPanel';
import StoragePanel from '../components/StoragePanel';
import { getVideo } from '../services/api';
import type { VideoMetadata, TimelineTrack, ProcessingJob } from '../types';

interface EditorProps {
  videos: VideoMetadata[];
  selectedVideo: VideoMetadata | null;
  onVideosChange: (videos: VideoMetadata[]) => void;
}

export default function Editor({ videos, selectedVideo, onVideosChange }: EditorProps) {
  const [tracks, setTracks] = useState<TimelineTrack[]>(() => {
    if (selectedVideo) {
      return [
        {
          id: `track-${selectedVideo.id}`,
          video_id: selectedVideo.id,
          name: selectedVideo.original_name,
          start_time: 0,
          end_time: selectedVideo.duration_seconds || 30,
          effects: [],
          layer: 0,
        },
      ];
    }
    return [];
  });
  const [selectedTrackId, setSelectedTrackId] = useState<string | null>(
    tracks.length > 0 ? tracks[0].id : null
  );
  const [outputVideo, setOutputVideo] = useState<VideoMetadata | null>(null);

  const selectedTrack = tracks.find((t) => t.id === selectedTrackId);
  const activeVideo = selectedTrack
    ? videos.find((v) => v.id === selectedTrack.video_id) || selectedVideo
    : selectedVideo;

  const duration = Math.max(...tracks.map((t) => t.end_time), 30);

  const handleJobComplete = useCallback(
    async (job: ProcessingJob) => {
      if (!job.result) return;

      // Fetch the output video metadata
      try {
        const outputMeta = await getVideo(job.result.output_video_id);
        if (outputMeta) {
          setOutputVideo(outputMeta);
        }
      } catch {
        // Output video metadata fetch failed
      }

      // Update the track with the applied effect
      if (selectedTrackId) {
        setTracks((prev) =>
          prev.map((t) =>
            t.id === selectedTrackId
              ? { ...t, effects: [...t.effects, job.effect_type as TimelineTrack['effects'][number]] }
              : t
          )
        );
      }
      // Update video metadata
      if (activeVideo) {
        const updatedVideos = videos.map((v) =>
          v.id === activeVideo.id
            ? { ...v, effects_applied: [...v.effects_applied, job.effect_type] }
            : v
        );
        onVideosChange(updatedVideos);
      }
    },
    [selectedTrackId, activeVideo, videos, onVideosChange]
  );

  const handlePinned = useCallback(
    (cid: string, url: string) => {
      if (activeVideo) {
        const updatedVideos = videos.map((v) =>
          v.id === activeVideo.id ? { ...v, ipfs_cid: cid, ipfs_url: url } : v
        );
        onVideosChange(updatedVideos);
      }
    },
    [activeVideo, videos, onVideosChange]
  );

  return (
    <div className="h-[calc(100vh-56px)] flex flex-col p-4 gap-4 overflow-hidden">
      {/* Top: Preview + Effects */}
      <div className="flex gap-4 flex-1 min-h-0">
        {/* Preview */}
        <div className="flex-1">
          <VideoPreview
            video={activeVideo || null}
            outputVideo={outputVideo}
            showCompare={outputVideo !== null}
          />
        </div>

        {/* Right sidebar */}
        <div className="w-80 flex flex-col gap-4 overflow-y-auto">
          <EffectsPanel
            videoId={activeVideo?.id || null}
            onJobComplete={handleJobComplete}
          />
          <StoragePanel
            video={activeVideo || null}
            onPinned={handlePinned}
          />
        </div>
      </div>

      {/* Bottom: Timeline */}
      <div className="flex-shrink-0">
        <Timeline
          tracks={tracks}
          videos={videos}
          onTracksChange={setTracks}
          onSelectTrack={(track) => setSelectedTrackId(track.id)}
          selectedTrackId={selectedTrackId}
          duration={duration}
        />
      </div>
    </div>
  );
}
