import { useCallback } from 'react';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Trash2, Eye, Sparkles, Clock, Film } from 'lucide-react';
import type { TimelineTrack, VideoMetadata } from '../types';

interface TimelineProps {
  tracks: TimelineTrack[];
  videos: VideoMetadata[];
  onTracksChange: (tracks: TimelineTrack[]) => void;
  onSelectTrack: (track: TimelineTrack) => void;
  selectedTrackId: string | null;
  duration: number;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function TrackItem({
  track,
  video,
  isSelected,
  onSelect,
  onRemove,
  duration,
}: {
  track: TimelineTrack;
  video: VideoMetadata | undefined;
  isSelected: boolean;
  onSelect: () => void;
  onRemove: () => void;
  duration: number;
}) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: track.id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const widthPct = duration > 0 ? ((track.end_time - track.start_time) / duration) * 100 : 100;
  const leftPct = duration > 0 ? (track.start_time / duration) * 100 : 0;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`timeline-track rounded-lg p-3 mb-2 cursor-pointer ${
        isSelected
          ? 'glass-card border-purple-500/40 bg-purple-500/10'
          : 'glass-card hover:border-purple-500/20'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-center gap-3">
        <button {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-zinc-600 hover:text-zinc-400">
          <GripVertical className="w-4 h-4" />
        </button>

        <div className="w-8 h-8 rounded bg-purple-500/20 flex items-center justify-center">
          <Film className="w-4 h-4 text-purple-400" />
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-zinc-200 truncate">{track.name}</p>
          <div className="flex items-center gap-2 text-xs text-zinc-500 mt-0.5">
            <Clock className="w-3 h-3" />
            <span>{formatTime(track.start_time)} - {formatTime(track.end_time)}</span>
            {track.effects.length > 0 && (
              <>
                <Sparkles className="w-3 h-3 text-purple-400" />
                <span className="text-purple-400">{track.effects.length} effects</span>
              </>
            )}
          </div>
        </div>

        <div className="flex items-center gap-1">
          <button className="p-1.5 rounded hover:bg-white/5 text-zinc-500 hover:text-zinc-300">
            <Eye className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onRemove(); }}
            className="p-1.5 rounded hover:bg-red-500/10 text-zinc-500 hover:text-red-400"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Timeline bar */}
      <div className="mt-2 h-6 bg-zinc-900/50 rounded relative overflow-hidden">
        <div
          className="absolute top-0 h-full rounded bg-gradient-to-r from-purple-600/60 to-blue-600/60 flex items-center px-2"
          style={{ left: `${leftPct}%`, width: `${Math.max(widthPct, 5)}%` }}
        >
          <span className="text-[10px] text-white/70 truncate">
            {video?.original_name || track.name}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function Timeline({
  tracks,
  videos,
  onTracksChange,
  onSelectTrack,
  selectedTrackId,
  duration,
}: TimelineProps) {
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (over && active.id !== over.id) {
        const oldIdx = tracks.findIndex((t) => t.id === active.id);
        const newIdx = tracks.findIndex((t) => t.id === over.id);
        onTracksChange(arrayMove(tracks, oldIdx, newIdx));
      }
    },
    [tracks, onTracksChange]
  );

  // Time ruler marks
  const marks = [];
  const step = Math.max(1, Math.ceil(duration / 10));
  for (let i = 0; i <= duration; i += step) {
    marks.push(i);
  }

  return (
    <div className="glass-card rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
          <Film className="w-4 h-4 text-purple-400" />
          Timeline
        </h3>
        <span className="text-xs text-zinc-500">
          {tracks.length} track{tracks.length !== 1 ? 's' : ''} &bull; {formatTime(duration)}
        </span>
      </div>

      {/* Time ruler */}
      <div className="flex items-center h-6 mb-2 border-b border-zinc-800/50 relative">
        {marks.map((t) => (
          <div
            key={t}
            className="absolute text-[10px] text-zinc-600"
            style={{ left: `${duration > 0 ? (t / duration) * 100 : 0}%` }}
          >
            {formatTime(t)}
          </div>
        ))}
      </div>

      {tracks.length === 0 ? (
        <div className="text-center py-8 text-zinc-600 text-sm">
          <Film className="w-10 h-10 mx-auto mb-2 opacity-30" />
          Upload a video to start editing
        </div>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={tracks.map((t) => t.id)} strategy={verticalListSortingStrategy}>
            {tracks.map((track) => (
              <TrackItem
                key={track.id}
                track={track}
                video={videos.find((v) => v.id === track.video_id)}
                isSelected={selectedTrackId === track.id}
                onSelect={() => onSelectTrack(track)}
                onRemove={() => onTracksChange(tracks.filter((t) => t.id !== track.id))}
                duration={duration}
              />
            ))}
          </SortableContext>
        </DndContext>
      )}
    </div>
  );
}
