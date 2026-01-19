import { useState, useEffect } from 'react';
import { api } from './api';
import { Download, Trash2, Youtube, Settings2 } from 'lucide-react';
import Starfield from './components/Starfield';

function App() {
  const [url, setUrl] = useState("");
  const [activeDownloads, setActiveDownloads] = useState({});
  const [completedDownloads, setCompletedDownloads] = useState([]);
  const [quality, setQuality] = useState("best");
  const [format, setFormat] = useState("any");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [connected, setConnected] = useState(false);

  useEffect(() => {
    // Initial fetch of downloads
    api.getDownloads().then(setCompletedDownloads);

    // Connect to WebSocket
    const ws = api.connectWebSocket((data) => {
      if (data.type === "progress") {
        setActiveDownloads((prev) => ({
          ...prev,
          [data.data.id]: { ...prev[data.data.id], ...data.data },
        }));
      } else if (data.type === "finished") {
        setActiveDownloads((prev) => {
          const next = { ...prev };
          delete next[data.data.id];
          return next;
        });
        // Refresh library
        api.getDownloads().then(setCompletedDownloads);
      } else if (data.type === "connected") {
        setConnected(true);
      }
    });

    return () => ws.close();
  }, []);

  const handleDownload = async () => {
    if (!url) return;
    try {
      await api.startDownload(url, format, quality);
      setUrl("");
    } catch (e) {
      console.error(e);
      alert("Failed to start download");
    }
  };

  const handleDelete = async (filename) => {
    try {
      await api.deleteDownload(filename);
      setCompletedDownloads((prev) => prev.filter((d) => d.filename !== filename));
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen relative font-sans text-xierra-text selection:bg-white selection:text-black pb-20">
      <Starfield />
      <div className="stars"></div>

      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md bg-black/50 border-b border-xierra-border">
        <div className="max-w-7xl mx-auto px-6 py-5 flex justify-between items-center">
          <div>
            <div className="flex items-center gap-3 text-white">
              <span className="text-xl font-black tracking-widest">XIERRA</span>
              <span className="text-xierra-muted text-xl font-light">|</span>
              <span className="text-xl font-mono tracking-widest text-gray-300">OURTUBE</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-1.5 h-1.5 rounded-full bg-green-500"></div>
              <span className="text-[10px] font-bold tracking-widest text-xierra-muted uppercase">System Ready</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 bg-xierra-card/80 border border-xierra-border rounded-full px-4 py-2 backdrop-blur-md shadow-sm">
              <span className="text-[10px] font-bold tracking-widest text-xierra-muted uppercase border-r border-xierra-border pr-3">Library</span>
              <span className="text-xs font-mono text-white">{completedDownloads.length}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto p-4 md:p-8 space-y-12 bg-black/95 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/5 relative z-10 mt-8">
        {/* Input Section */}
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <div className="flex flex-col md:flex-row gap-3">
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste link..."
              className="flex-1 bg-white/5 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-white/40 transition placeholder-gray-500 shadow-inner"
            />
            <button
              onClick={handleDownload}
              className="bg-transparent border border-white/30 hover:bg-white/10 hover:border-white text-white px-5 py-3 rounded-lg font-bold tracking-widest transition shadow-[0_0_15px_rgba(255,255,255,0.05)] uppercase text-[10px]"
            >
              Download
            </button>
          </div>

          <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between bg-white/5 p-4 rounded-xl border border-white/10">
            <div className="flex gap-4 w-full md:w-auto">
              <div className="flex-1 md:flex-none">
                <label className="block text-[10px] uppercase tracking-widest text-gray-500 mb-1.5 ml-1">Quality</label>
                <div className="relative">
                  <select
                    value={quality}
                    onChange={(e) => setQuality(e.target.value)}
                    className="w-full md:w-32 appearance-none bg-black border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/30 cursor-pointer"
                  >
                    <option value="best">Best</option>
                    <option value="best_ios">Best (iOS)</option>
                    <option value="2160p">2160p</option>
                    <option value="1440p">1440p</option>
                    <option value="1080p">1080p</option>
                    <option value="720p">720p</option>
                    <option value="480p">480p</option>
                    <option value="360p">360p</option>
                    <option value="240p">240p</option>
                    <option value="worst">Worst</option>
                  </select>
                </div>
              </div>

              <div className="flex-1 md:flex-none">
                <label className="block text-[10px] uppercase tracking-widest text-gray-500 mb-1.5 ml-1">Format</label>
                <div className="relative">
                  <select
                    value={format}
                    onChange={(e) => setFormat(e.target.value)}
                    className="w-full md:w-32 appearance-none bg-black border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-white/30 cursor-pointer"
                  >
                    <option value="any">Any (Best)</option>
                    <option value="mp4">MP4</option>
                    <option value="m4a">M4A</option>
                    <option value="mp3">MP3</option>
                    <option value="opus">OPUS</option>
                    <option value="wav">WAV</option>
                    <option value="flac">FLAC</option>
                    <option value="thumbnail">Thumbnail</option>
                  </select>
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className={`w-full md:w-auto mt-2 md:mt-6 flex items-center justify-center gap-2 text-xs uppercase tracking-wider px-4 py-2.5 rounded-lg transition border ${showAdvanced ? 'bg-white text-black border-white' : 'border-white/10 text-gray-400 hover:text-white hover:border-white/30'} `}
            >
              <Settings2 size={14} />
              Options
            </button>
          </div>

          {showAdvanced && (
            <div className="bg-black/90 border border-white/10 rounded-xl p-6 grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-top-2 duration-300">
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-[10px] uppercase tracking-widest text-gray-500">Auto Start</label>
                  <select className="w-full bg-black border border-white/10 rounded-lg p-2 text-sm text-gray-300"><option>YES</option><option>NO</option></select>
                </div>
              </div>
              <div className="space-y-4">
                <div className="col-span-1 md:col-span-2 flex flex-col gap-3 pt-2">
                  <label className="flex items-center gap-3 text-sm text-gray-400 cursor-pointer hover:text-white transition group">
                    <div className="w-4 h-4 border border-white/10 rounded group-hover:border-white/50"></div>
                    Strict Playlist Mode
                  </label>
                  <label className="flex items-center gap-3 text-sm text-gray-400 cursor-pointer hover:text-white transition group">
                    <div className="w-4 h-4 border border-white/10 rounded group-hover:border-white/50"></div>
                    Split by chapters
                  </label>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Downloading Section */}
        {Object.keys(activeDownloads).length > 0 && (
          <div className="space-y-4 animate-in fade-in duration-500">
            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-[0.2em] border-b border-white/10 pb-2">Processing Queue</h2>
            <div className="space-y-3">
              {Object.values(activeDownloads).map((d) => (
                <div key={d.id} className="bg-white/5 border border-white/10 p-4 rounded-xl flex flex-col md:flex-row md:items-center gap-4 relative overflow-hidden group">
                  <div className="absolute bottom-0 left-0 h-0.5 bg-white/20 w-full md:hidden">
                    <div className="h-full bg-white transition-all duration-300" style={{ width: d.percent }} />
                  </div>

                  <div className="flex-1 min-w-0 z-10">
                    <div className="text-sm font-medium truncate text-white mb-2">{d.filename || "Fetching metadata..."}</div>

                    <div className="hidden md:block h-1 bg-white/10 rounded-full overflow-hidden w-full max-w-sm">
                      <div className="h-full bg-white transition-all duration-300 shadow-[0_0_10px_rgba(255,255,255,0.5)]" style={{ width: d.percent }} />
                    </div>
                  </div>

                  <div className="flex items-center justify-between md:justify-end gap-6 text-xs font-mono text-gray-400 z-10">
                    <span className="bg-black/50 px-2 py-1 rounded border border-white/10">{d.speed}</span>
                    <span className="bg-black/50 px-2 py-1 rounded border border-white/10">{d.eta}</span>
                    <span className="text-white font-bold">{d.percent}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Completed Section */}
        <div className="space-y-4 pt-4">
          <div className="flex justify-between items-end border-b border-white/10 pb-2">
            <h2 className="text-xs font-bold text-gray-500 uppercase tracking-[0.2em]">Library</h2>
            <button className="text-[10px] uppercase tracking-wider text-gray-500 hover:text-white transition">Clear All</button>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {completedDownloads.map((file) => (
              <div key={file.filename} className="bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/20 p-4 rounded-xl flex items-center justify-between transition group">
                <div className="flex items-center gap-4 overflow-hidden">
                  <div className="w-2 h-2 rounded-full bg-white/20 group-hover:bg-green-400 shadow-[0_0_8px_rgba(255,255,255,0.1)] transition-all"></div>
                  <div className="flex flex-col min-w-0">
                    <a
                      href={`http://localhost:8000${file.url}`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm text-gray-200 hover:text-white truncate font-medium transition"
                    >
                      {file.filename}
                    </a >
                    <span className="text-[10px] text-gray-500 font-mono mt-0.5">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div >
                </div >

                <div className="flex items-center gap-2 md:gap-4 md:opacity-0 md:group-hover:opacity-100 transition-all ml-4">
                  <a href={`http://localhost:8000${file.url}`} download className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition">
                    <Download size={16} />
                  </a>
                  <button onClick={() => handleDelete(file.filename)} className="p-2 hover:bg-red-500/10 rounded-lg text-gray-400 hover:text-red-500 transition">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div >
            ))}

            {
              completedDownloads.length === 0 && (
                <div className="text-gray-600/50 text-center py-12 text-sm tracking-widest uppercase">Void Empty</div>
              )
            }
          </div >
        </div >
      </main >
    </div >
  );
}

export default App;
