import { useState, useCallback } from 'react';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Editor from './pages/Editor';
import UploadPage from './pages/UploadPage';
import PricingPage from './pages/PricingPage';
import type { VideoMetadata } from './types';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [videos, setVideos] = useState<VideoMetadata[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<VideoMetadata | null>(null);

  const handleUploadComplete = useCallback(
    (video: VideoMetadata) => {
      setVideos((prev) => [video, ...prev]);
      setSelectedVideo(video);
      setCurrentPage('editor');
    },
    []
  );

  const handleSelectVideo = useCallback((video: VideoMetadata) => {
    setSelectedVideo(video);
  }, []);

  const handleNavigate = useCallback((page: string) => {
    setCurrentPage(page);
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <Navbar currentPage={currentPage} onNavigate={handleNavigate} />
      <main>
        {currentPage === 'dashboard' && (
          <Dashboard
            onNavigate={handleNavigate}
            onSelectVideo={handleSelectVideo}
          />
        )}
        {currentPage === 'editor' && (
          <Editor
            videos={videos}
            selectedVideo={selectedVideo}
            onVideosChange={setVideos}
          />
        )}
        {currentPage === 'upload' && (
          <UploadPage onUploadComplete={handleUploadComplete} />
        )}
        {currentPage === 'pricing' && <PricingPage />}
      </main>
    </div>
  );
}

export default App;
