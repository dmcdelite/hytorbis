import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { 
  Map, Sparkles, Mountain, Home, Castle, Landmark, Building, 
  Download, Save, Trash2, Plus, Settings, Wand2, Send, Bot,
  TreePine, Snowflake, Sun, Skull, Waves, ChevronRight, X,
  RefreshCw, FolderOpen, FileJson, Loader2, PanelRightOpen, PanelRightClose
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Zone colors and data
const ZONE_CONFIG = {
  emerald_grove: { name: "Emerald Grove", color: "#10B981", icon: TreePine },
  borea: { name: "Borea", color: "#06B6D4", icon: Snowflake },
  desert: { name: "Desert", color: "#F59E0B", icon: Sun },
  arctic: { name: "Arctic", color: "#E2E8F0", icon: Snowflake },
  corrupted: { name: "Corrupted", color: "#8B5CF6", icon: Skull }
};

const PREFAB_CONFIG = {
  dungeon: { name: "Dungeon", icon: Castle },
  village: { name: "Village", icon: Home },
  ruins: { name: "Ruins", icon: Landmark },
  tower: { name: "Tower", icon: Building },
  cave_entrance: { name: "Cave", icon: Mountain },
  portal: { name: "Portal", icon: Sparkles }
};

// Main App Component
function App() {
  const [worlds, setWorlds] = useState([]);
  const [currentWorld, setCurrentWorld] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTool, setActiveTool] = useState("select");
  const [selectedZoneType, setSelectedZoneType] = useState("emerald_grove");
  const [selectedPrefabType, setSelectedPrefabType] = useState("dungeon");
  const [aiPanelOpen, setAiPanelOpen] = useState(true);
  const [aiMessages, setAiMessages] = useState([]);
  const [aiInput, setAiInput] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiProvider, setAiProvider] = useState("openai");
  const [showNewWorldDialog, setShowNewWorldDialog] = useState(false);
  const [newWorldName, setNewWorldName] = useState("");
  const [newWorldSeed, setNewWorldSeed] = useState("");

  // Fetch worlds on mount
  useEffect(() => {
    fetchWorlds();
  }, []);

  const fetchWorlds = async () => {
    try {
      const response = await axios.get(`${API}/worlds`);
      setWorlds(response.data);
    } catch (e) {
      console.error("Failed to fetch worlds:", e);
    }
  };

  const createWorld = async () => {
    if (!newWorldName.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post(`${API}/worlds`, {
        name: newWorldName,
        seed: newWorldSeed || null,
        map_width: 20,
        map_height: 20
      });
      setCurrentWorld(response.data);
      setWorlds([...worlds, response.data]);
      setShowNewWorldDialog(false);
      setNewWorldName("");
      setNewWorldSeed("");
      setAiMessages([]);
    } catch (e) {
      console.error("Failed to create world:", e);
    }
    setLoading(false);
  };

  const loadWorld = async (worldId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/worlds/${worldId}`);
      setCurrentWorld(response.data);
      setAiMessages([]);
    } catch (e) {
      console.error("Failed to load world:", e);
    }
    setLoading(false);
  };

  const saveWorld = async () => {
    if (!currentWorld) return;
    setLoading(true);
    try {
      await axios.put(`${API}/worlds/${currentWorld.id}`, {
        terrain: currentWorld.terrain,
        zones: currentWorld.zones,
        prefabs: currentWorld.prefabs,
        ai_provider: aiProvider
      });
      fetchWorlds();
    } catch (e) {
      console.error("Failed to save world:", e);
    }
    setLoading(false);
  };

  const deleteWorld = async (worldId) => {
    try {
      await axios.delete(`${API}/worlds/${worldId}`);
      if (currentWorld?.id === worldId) {
        setCurrentWorld(null);
      }
      setWorlds(worlds.filter(w => w.id !== worldId));
    } catch (e) {
      console.error("Failed to delete world:", e);
    }
  };

  const generateSeed = async () => {
    try {
      const response = await axios.get(`${API}/seed/random`);
      setNewWorldSeed(response.data.seed);
    } catch (e) {
      console.error("Failed to generate seed:", e);
    }
  };

  const handleMapClick = useCallback((x, y) => {
    if (!currentWorld) return;

    if (activeTool === "zone") {
      const newZone = {
        id: `zone-${Date.now()}`,
        type: selectedZoneType,
        x,
        y,
        width: 1,
        height: 1,
        difficulty: 1,
        biomes: []
      };
      setCurrentWorld({
        ...currentWorld,
        zones: [...currentWorld.zones, newZone]
      });
    } else if (activeTool === "prefab") {
      const newPrefab = {
        id: `prefab-${Date.now()}`,
        type: selectedPrefabType,
        x,
        y,
        rotation: 0,
        scale: 1.0
      };
      setCurrentWorld({
        ...currentWorld,
        prefabs: [...currentWorld.prefabs, newPrefab]
      });
    }
  }, [activeTool, selectedZoneType, selectedPrefabType, currentWorld]);

  const removeZone = (zoneId) => {
    if (!currentWorld) return;
    setCurrentWorld({
      ...currentWorld,
      zones: currentWorld.zones.filter(z => z.id !== zoneId)
    });
  };

  const removePrefab = (prefabId) => {
    if (!currentWorld) return;
    setCurrentWorld({
      ...currentWorld,
      prefabs: currentWorld.prefabs.filter(p => p.id !== prefabId)
    });
  };

  const updateTerrain = (key, value) => {
    if (!currentWorld) return;
    setCurrentWorld({
      ...currentWorld,
      terrain: {
        ...currentWorld.terrain,
        [key]: value
      }
    });
  };

  const sendAiMessage = async () => {
    if (!aiInput.trim() || !currentWorld) return;
    
    const userMessage = { role: "user", content: aiInput };
    setAiMessages([...aiMessages, userMessage]);
    setAiInput("");
    setAiLoading(true);

    try {
      const response = await axios.post(`${API}/ai/chat`, {
        world_id: currentWorld.id,
        message: aiInput,
        provider: aiProvider
      });
      
      const assistantMessage = { 
        role: "assistant", 
        content: response.data.response,
        suggestions: response.data.suggestions
      };
      setAiMessages(prev => [...prev, assistantMessage]);
    } catch (e) {
      console.error("AI chat failed:", e);
      setAiMessages(prev => [...prev, { 
        role: "assistant", 
        content: "Sorry, I encountered an error. Please try again." 
      }]);
    }
    setAiLoading(false);
  };

  const exportWorld = async (format) => {
    if (!currentWorld) return;
    try {
      const response = await axios.get(`${API}/worlds/${currentWorld.id}/export/${format}`);
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: "application/json" });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${currentWorld.name}_${format}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed:", e);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header" data-testid="app-header">
        <div className="header-left">
          <Map className="header-icon" />
          <h1 className="header-title">Hytale World Builder</h1>
        </div>
        <div className="header-center">
          {currentWorld && (
            <div className="world-info">
              <span className="world-name">{currentWorld.name}</span>
              <span className="world-seed">Seed: {currentWorld.seed}</span>
            </div>
          )}
        </div>
        <div className="header-right">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setAiPanelOpen(!aiPanelOpen)}
            data-testid="toggle-ai-panel"
          >
            {aiPanelOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
          </Button>
        </div>
      </header>

      <div className="main-content">
        {/* Left Sidebar - Worlds & Tools */}
        <aside className="sidebar-left" data-testid="sidebar-left">
          <div className="sidebar-section">
            <div className="section-header">
              <FolderOpen size={16} />
              <span>Worlds</span>
              <Dialog open={showNewWorldDialog} onOpenChange={setShowNewWorldDialog}>
                <DialogTrigger asChild>
                  <Button variant="ghost" size="icon" className="ml-auto" data-testid="new-world-btn">
                    <Plus size={16} />
                  </Button>
                </DialogTrigger>
                <DialogContent className="dialog-content">
                  <DialogHeader>
                    <DialogTitle>Create New World</DialogTitle>
                  </DialogHeader>
                  <div className="dialog-form">
                    <div className="form-group">
                      <Label>World Name</Label>
                      <Input
                        value={newWorldName}
                        onChange={(e) => setNewWorldName(e.target.value)}
                        placeholder="My Hytale World"
                        data-testid="new-world-name-input"
                      />
                    </div>
                    <div className="form-group">
                      <Label>Seed (optional)</Label>
                      <div className="seed-input-group">
                        <Input
                          value={newWorldSeed}
                          onChange={(e) => setNewWorldSeed(e.target.value)}
                          placeholder="Auto-generate"
                          data-testid="new-world-seed-input"
                        />
                        <Button variant="secondary" size="icon" onClick={generateSeed} data-testid="generate-seed-btn">
                          <RefreshCw size={16} />
                        </Button>
                      </div>
                    </div>
                    <Button onClick={createWorld} disabled={!newWorldName.trim() || loading} data-testid="create-world-btn">
                      {loading ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}
                      Create World
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
            <ScrollArea className="worlds-list">
              {worlds.map((world) => (
                <div
                  key={world.id}
                  className={`world-item ${currentWorld?.id === world.id ? "active" : ""}`}
                  onClick={() => loadWorld(world.id)}
                  data-testid={`world-item-${world.id}`}
                >
                  <div className="world-item-info">
                    <span className="world-item-name">{world.name}</span>
                    <span className="world-item-seed">{world.seed}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="world-delete-btn"
                    onClick={(e) => { e.stopPropagation(); deleteWorld(world.id); }}
                    data-testid={`delete-world-${world.id}`}
                  >
                    <Trash2 size={14} />
                  </Button>
                </div>
              ))}
              {worlds.length === 0 && (
                <div className="empty-state">
                  <p>No worlds yet</p>
                  <p className="text-muted">Create your first world to begin</p>
                </div>
              )}
            </ScrollArea>
          </div>

          {/* Tools */}
          {currentWorld && (
            <div className="sidebar-section">
              <div className="section-header">
                <Settings size={16} />
                <span>Tools</span>
              </div>
              <div className="tools-grid">
                <Button
                  variant={activeTool === "select" ? "default" : "secondary"}
                  className="tool-btn"
                  onClick={() => setActiveTool("select")}
                  data-testid="tool-select"
                >
                  <ChevronRight size={16} />
                  Select
                </Button>
                <Button
                  variant={activeTool === "zone" ? "default" : "secondary"}
                  className="tool-btn"
                  onClick={() => setActiveTool("zone")}
                  data-testid="tool-zone"
                >
                  <Map size={16} />
                  Zone
                </Button>
                <Button
                  variant={activeTool === "prefab" ? "default" : "secondary"}
                  className="tool-btn"
                  onClick={() => setActiveTool("prefab")}
                  data-testid="tool-prefab"
                >
                  <Castle size={16} />
                  Prefab
                </Button>
              </div>

              {activeTool === "zone" && (
                <div className="tool-options">
                  <Label className="tool-label">Zone Type</Label>
                  <Select value={selectedZoneType} onValueChange={setSelectedZoneType}>
                    <SelectTrigger data-testid="zone-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(ZONE_CONFIG).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          <div className="select-item-with-color">
                            <div className="color-dot" style={{ backgroundColor: config.color }} />
                            {config.name}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {activeTool === "prefab" && (
                <div className="tool-options">
                  <Label className="tool-label">Structure Type</Label>
                  <Select value={selectedPrefabType} onValueChange={setSelectedPrefabType}>
                    <SelectTrigger data-testid="prefab-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(PREFAB_CONFIG).map(([key, config]) => {
                        const Icon = config.icon;
                        return (
                          <SelectItem key={key} value={key}>
                            <div className="select-item-with-icon">
                              <Icon size={14} />
                              {config.name}
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          {currentWorld && (
            <div className="sidebar-section sidebar-actions">
              <Button onClick={saveWorld} disabled={loading} className="action-btn" data-testid="save-world-btn">
                <Save size={16} />
                Save World
              </Button>
              <div className="export-buttons">
                <Button variant="secondary" onClick={() => exportWorld("json")} data-testid="export-json-btn">
                  <FileJson size={16} />
                  JSON
                </Button>
                <Button variant="secondary" onClick={() => exportWorld("hytale")} data-testid="export-hytale-btn">
                  <Download size={16} />
                  Hytale
                </Button>
              </div>
            </div>
          )}
        </aside>

        {/* Main Canvas Area */}
        <main className="canvas-area" data-testid="canvas-area">
          {currentWorld ? (
            <>
              <MapCanvas
                world={currentWorld}
                onCellClick={handleMapClick}
                onRemoveZone={removeZone}
                onRemovePrefab={removePrefab}
                activeTool={activeTool}
              />
              <TerrainPanel
                terrain={currentWorld.terrain}
                onUpdate={updateTerrain}
              />
            </>
          ) : (
            <div className="empty-canvas">
              <div className="empty-canvas-content">
                <img 
                  src="https://images.pexels.com/photos/9977648/pexels-photo-9977648.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940" 
                  alt="World"
                  className="empty-canvas-bg"
                />
                <div className="empty-canvas-overlay">
                  <Wand2 size={48} className="empty-icon" />
                  <h2>Create Your World</h2>
                  <p>Start by creating a new world or select an existing one</p>
                  <Button onClick={() => setShowNewWorldDialog(true)} data-testid="create-first-world-btn">
                    <Plus size={16} />
                    New World
                  </Button>
                </div>
              </div>
            </div>
          )}
        </main>

        {/* Right Panel - AI Assistant */}
        {aiPanelOpen && (
          <aside className="sidebar-right" data-testid="ai-panel">
            <div className="ai-header">
              <div className="ai-title">
                <img 
                  src="https://images.unsplash.com/photo-1641380184601-06e153dec2fc?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2OTF8MHwxfHNlYXJjaHwyfHxnbG93aW5nJTIwcnVuZSUyMG1hZ2ljfGVufDB8fHx8MTc3NTA3NzMyM3ww&ixlib=rb-4.1.0&q=85"
                  alt="AI"
                  className="ai-avatar"
                />
                <span>World Architect AI</span>
              </div>
              <Select value={aiProvider} onValueChange={setAiProvider}>
                <SelectTrigger className="ai-provider-select" data-testid="ai-provider-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">GPT-5.2</SelectItem>
                  <SelectItem value="anthropic">Claude</SelectItem>
                  <SelectItem value="gemini">Gemini</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <ScrollArea className="ai-messages">
              {aiMessages.length === 0 ? (
                <div className="ai-welcome">
                  <Bot size={32} className="ai-welcome-icon" />
                  <p>I can help you design your world!</p>
                  <p className="text-muted">Try asking me to suggest zone layouts, prefab placements, or terrain settings.</p>
                </div>
              ) : (
                aiMessages.map((msg, i) => (
                  <div key={i} className={`ai-message ${msg.role}`}>
                    <div className="ai-message-content">
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              {aiLoading && (
                <div className="ai-message assistant">
                  <div className="ai-message-content">
                    <Loader2 className="animate-spin" size={16} />
                    <span>Thinking...</span>
                  </div>
                </div>
              )}
            </ScrollArea>

            <div className="ai-input-area">
              <Textarea
                value={aiInput}
                onChange={(e) => setAiInput(e.target.value)}
                placeholder={currentWorld ? "Ask for world suggestions..." : "Create a world first"}
                disabled={!currentWorld || aiLoading}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendAiMessage();
                  }
                }}
                data-testid="ai-input"
              />
              <Button 
                onClick={sendAiMessage} 
                disabled={!currentWorld || !aiInput.trim() || aiLoading}
                className="ai-send-btn"
                data-testid="ai-send-btn"
              >
                <Send size={16} />
              </Button>
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

// Map Canvas Component
function MapCanvas({ world, onCellClick, onRemoveZone, onRemovePrefab, activeTool }) {
  const gridSize = Math.max(world.map_width, world.map_height);
  const cellSize = Math.min(Math.floor(600 / gridSize), 40);

  // Create a map of zones by position
  const zoneMap = {};
  world.zones.forEach(zone => {
    const key = `${zone.x}-${zone.y}`;
    zoneMap[key] = zone;
  });

  // Create a map of prefabs by position
  const prefabMap = {};
  world.prefabs.forEach(prefab => {
    const key = `${prefab.x}-${prefab.y}`;
    if (!prefabMap[key]) prefabMap[key] = [];
    prefabMap[key].push(prefab);
  });

  return (
    <div className="map-canvas-container" data-testid="map-canvas">
      <div 
        className="map-grid"
        style={{
          gridTemplateColumns: `repeat(${world.map_width}, ${cellSize}px)`,
          gridTemplateRows: `repeat(${world.map_height}, ${cellSize}px)`
        }}
      >
        {Array.from({ length: world.map_height }).map((_, y) =>
          Array.from({ length: world.map_width }).map((_, x) => {
            const key = `${x}-${y}`;
            const zone = zoneMap[key];
            const prefabs = prefabMap[key] || [];
            const ZoneIcon = zone ? ZONE_CONFIG[zone.type]?.icon : null;

            return (
              <div
                key={key}
                className={`map-cell ${activeTool !== "select" ? "clickable" : ""}`}
                style={{
                  backgroundColor: zone ? `${ZONE_CONFIG[zone.type]?.color}40` : "transparent",
                  borderColor: zone ? ZONE_CONFIG[zone.type]?.color : undefined
                }}
                onClick={() => onCellClick(x, y)}
                data-testid={`cell-${x}-${y}`}
              >
                {zone && (
                  <div className="cell-zone" title={ZONE_CONFIG[zone.type]?.name}>
                    {ZoneIcon && <ZoneIcon size={14} style={{ color: ZONE_CONFIG[zone.type]?.color }} />}
                    <button
                      className="cell-remove"
                      onClick={(e) => { e.stopPropagation(); onRemoveZone(zone.id); }}
                      title="Remove zone"
                    >
                      <X size={10} />
                    </button>
                  </div>
                )}
                {prefabs.map((prefab, i) => {
                  const PrefabIcon = PREFAB_CONFIG[prefab.type]?.icon;
                  return (
                    <div key={prefab.id} className="cell-prefab" title={PREFAB_CONFIG[prefab.type]?.name}>
                      {PrefabIcon && <PrefabIcon size={12} />}
                      <button
                        className="cell-remove"
                        onClick={(e) => { e.stopPropagation(); onRemovePrefab(prefab.id); }}
                        title="Remove prefab"
                      >
                        <X size={10} />
                      </button>
                    </div>
                  );
                })}
              </div>
            );
          })
        )}
      </div>

      <div className="map-legend">
        <div className="legend-section">
          <span className="legend-title">Zones</span>
          {Object.entries(ZONE_CONFIG).map(([key, config]) => (
            <div key={key} className="legend-item">
              <div className="color-dot" style={{ backgroundColor: config.color }} />
              <span>{config.name}</span>
            </div>
          ))}
        </div>
        <div className="legend-section">
          <span className="legend-title">Prefabs</span>
          {Object.entries(PREFAB_CONFIG).map(([key, config]) => {
            const Icon = config.icon;
            return (
              <div key={key} className="legend-item">
                <Icon size={12} />
                <span>{config.name}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// Terrain Panel Component
function TerrainPanel({ terrain, onUpdate }) {
  return (
    <div className="terrain-panel" data-testid="terrain-panel">
      <h3 className="terrain-title">
        <Mountain size={16} />
        Terrain Settings
      </h3>
      <div className="terrain-controls">
        <div className="terrain-control">
          <div className="control-header">
            <Label>Height Scale</Label>
            <span className="control-value">{terrain?.height_scale?.toFixed(2) || "1.00"}</span>
          </div>
          <Slider
            value={[terrain?.height_scale || 1]}
            min={0.1}
            max={3}
            step={0.1}
            onValueChange={([v]) => onUpdate("height_scale", v)}
            data-testid="terrain-height-slider"
          />
        </div>
        <div className="terrain-control">
          <div className="control-header">
            <Label>Cave Density</Label>
            <span className="control-value">{terrain?.cave_density?.toFixed(2) || "0.50"}</span>
          </div>
          <Slider
            value={[terrain?.cave_density || 0.5]}
            min={0}
            max={1}
            step={0.05}
            onValueChange={([v]) => onUpdate("cave_density", v)}
            data-testid="terrain-cave-slider"
          />
        </div>
        <div className="terrain-control">
          <div className="control-header">
            <Label>River Frequency</Label>
            <span className="control-value">{terrain?.river_frequency?.toFixed(2) || "0.30"}</span>
          </div>
          <Slider
            value={[terrain?.river_frequency || 0.3]}
            min={0}
            max={1}
            step={0.05}
            onValueChange={([v]) => onUpdate("river_frequency", v)}
            data-testid="terrain-river-slider"
          />
        </div>
        <div className="terrain-control">
          <div className="control-header">
            <Label>Mountain Scale</Label>
            <span className="control-value">{terrain?.mountain_scale?.toFixed(2) || "0.50"}</span>
          </div>
          <Slider
            value={[terrain?.mountain_scale || 0.5]}
            min={0}
            max={1}
            step={0.05}
            onValueChange={([v]) => onUpdate("mountain_scale", v)}
            data-testid="terrain-mountain-slider"
          />
        </div>
        <div className="terrain-control">
          <div className="control-header">
            <Label>Ocean Level</Label>
            <span className="control-value">{terrain?.ocean_level?.toFixed(2) || "0.30"}</span>
          </div>
          <Slider
            value={[terrain?.ocean_level || 0.3]}
            min={0}
            max={1}
            step={0.05}
            onValueChange={([v]) => onUpdate("ocean_level", v)}
            data-testid="terrain-ocean-slider"
          />
        </div>
      </div>
    </div>
  );
}

export default App;
