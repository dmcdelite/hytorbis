import { useState, useEffect, useCallback, useRef } from "react";
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
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Map, Sparkles, Mountain, Home, Castle, Landmark, Building, 
  Download, Save, Trash2, Plus, Settings, Wand2, Send, Bot,
  TreePine, Snowflake, Sun, Skull, Waves, ChevronRight, X,
  RefreshCw, FolderOpen, FileJson, Loader2, PanelRightOpen, PanelRightClose,
  Undo2, Redo2, Paintbrush, MousePointer, ZoomIn, ZoomOut, Move,
  Layers, Edit3, Maximize2, Upload, LayoutTemplate, Users, Box,
  Swords, Heart, Compass, Pickaxe, Eye
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

const BIOME_CONFIG = {
  forest: { name: "Forest", zones: ["emerald_grove"], color: "#22C55E" },
  plains: { name: "Plains", zones: ["emerald_grove", "desert"], color: "#84CC16" },
  swamp: { name: "Swamp", zones: ["emerald_grove"], color: "#65A30D" },
  mountains: { name: "Mountains", zones: ["emerald_grove", "borea", "arctic"], color: "#78716C" },
  tundra: { name: "Tundra", zones: ["borea", "arctic"], color: "#A5F3FC" },
  glacier: { name: "Glacier", zones: ["arctic"], color: "#E0F2FE" },
  dunes: { name: "Dunes", zones: ["desert"], color: "#FCD34D" },
  oasis: { name: "Oasis", zones: ["desert"], color: "#34D399" },
  void: { name: "Void", zones: ["corrupted"], color: "#7C3AED" },
  wasteland: { name: "Wasteland", zones: ["corrupted"], color: "#A855F7" }
};

const MAP_SIZE_PRESETS = [
  { label: "Small (32x32)", width: 32, height: 32 },
  { label: "Medium (64x64)", width: 64, height: 64 },
  { label: "Large (128x128)", width: 128, height: 128 },
  { label: "Huge (256x256)", width: 256, height: 256 },
  { label: "Max (512x512)", width: 512, height: 512 }
];

const TEMPLATE_ICONS = {
  adventure: Compass,
  peaceful: Heart,
  challenge: Swords,
  exploration: Map,
  dungeon_crawler: Pickaxe
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
  const [newWorldSize, setNewWorldSize] = useState({ width: 64, height: 64 });
  
  // P1: Undo/Redo
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  
  // P1: Properties Panel
  const [selectedElement, setSelectedElement] = useState(null);
  const [propertiesOpen, setPropertiesOpen] = useState(false);
  
  // Map controls
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const lastPanPos = useRef({ x: 0, y: 0 });

  // P2: Templates
  const [templates, setTemplates] = useState([]);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // P2: Import
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importConfig, setImportConfig] = useState("");

  // P2: AI Auto-generate
  const [showAutoGenDialog, setShowAutoGenDialog] = useState(false);
  const [autoGenPrompt, setAutoGenPrompt] = useState("");
  const [autoGenLoading, setAutoGenLoading] = useState(false);

  // P2: 3D Preview
  const [show3DPreview, setShow3DPreview] = useState(false);
  const [preview3DData, setPreview3DData] = useState(null);

  // P2: Collaboration
  const [collabEnabled, setCollabEnabled] = useState(false);
  const [collabUsers, setCollabUsers] = useState([]);
  const [userId] = useState(`user-${Math.random().toString(36).substr(2, 9)}`);

  // Fetch worlds and templates on mount
  useEffect(() => {
    fetchWorlds();
    fetchTemplates();
  }, []);

  // Collaboration polling
  useEffect(() => {
    let interval;
    if (collabEnabled && currentWorld) {
      interval = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/collab/${currentWorld.id}/status`);
          setCollabUsers(response.data.users || []);
        } catch (e) {
          console.error("Collab poll error:", e);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [collabEnabled, currentWorld]);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data.templates || []);
    } catch (e) {
      console.error("Failed to fetch templates:", e);
    }
  };

  // Save to history when world changes
  const saveToHistory = useCallback((newWorld) => {
    if (!newWorld) return;
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(JSON.parse(JSON.stringify(newWorld)));
    if (newHistory.length > 50) newHistory.shift();
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [history, historyIndex]);

  const undo = useCallback(() => {
    if (historyIndex > 0) {
      setHistoryIndex(historyIndex - 1);
      setCurrentWorld(JSON.parse(JSON.stringify(history[historyIndex - 1])));
    }
  }, [history, historyIndex]);

  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      setHistoryIndex(historyIndex + 1);
      setCurrentWorld(JSON.parse(JSON.stringify(history[historyIndex + 1])));
    }
  }, [history, historyIndex]);

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
        map_width: newWorldSize.width,
        map_height: newWorldSize.height
      });
      setCurrentWorld(response.data);
      setWorlds([...worlds, response.data]);
      setShowNewWorldDialog(false);
      setNewWorldName("");
      setNewWorldSeed("");
      setAiMessages([]);
      setHistory([response.data]);
      setHistoryIndex(0);
      autoZoom(newWorldSize.width);
    } catch (e) {
      console.error("Failed to create world:", e);
    }
    setLoading(false);
  };

  // P2: Create from template
  const createFromTemplate = async () => {
    if (!newWorldName.trim() || !selectedTemplate) return;
    setLoading(true);
    try {
      const response = await axios.post(`${API}/worlds/from-template`, {
        name: newWorldName,
        template: selectedTemplate,
        map_width: newWorldSize.width,
        map_height: newWorldSize.height
      });
      setCurrentWorld(response.data);
      setWorlds([...worlds, response.data]);
      setShowTemplateDialog(false);
      setNewWorldName("");
      setSelectedTemplate(null);
      setAiMessages([]);
      setHistory([response.data]);
      setHistoryIndex(0);
      autoZoom(newWorldSize.width);
    } catch (e) {
      console.error("Failed to create from template:", e);
    }
    setLoading(false);
  };

  // P2: Import world
  const importWorld = async () => {
    if (!importConfig.trim()) return;
    setLoading(true);
    try {
      const config = JSON.parse(importConfig);
      const response = await axios.post(`${API}/worlds/import`, {
        config: config,
        name: newWorldName || null
      });
      setCurrentWorld(response.data);
      setWorlds([...worlds, response.data]);
      setShowImportDialog(false);
      setImportConfig("");
      setNewWorldName("");
      setHistory([response.data]);
      setHistoryIndex(0);
      autoZoom(response.data.map_width);
    } catch (e) {
      console.error("Failed to import world:", e);
      alert("Invalid JSON format. Please check your configuration.");
    }
    setLoading(false);
  };

  // P2: AI Auto-generate
  const autoGenerateWorld = async () => {
    if (!autoGenPrompt.trim() || !currentWorld) return;
    setAutoGenLoading(true);
    try {
      const response = await axios.post(`${API}/ai/auto-generate`, {
        world_id: currentWorld.id,
        prompt: autoGenPrompt,
        provider: aiProvider
      });
      
      const updatedWorld = response.data.world;
      setCurrentWorld(updatedWorld);
      saveToHistory(updatedWorld);
      setShowAutoGenDialog(false);
      setAutoGenPrompt("");
      
      // Add to AI messages
      setAiMessages(prev => [
        ...prev,
        { role: "user", content: `Generate: ${autoGenPrompt}` },
        { role: "assistant", content: `Generated ${updatedWorld.zones?.length || 0} zones and ${updatedWorld.prefabs?.length || 0} prefabs. ${response.data.generated?.description || ''}` }
      ]);
    } catch (e) {
      console.error("Auto-generate failed:", e);
      alert("Failed to generate. Please try a different prompt.");
    }
    setAutoGenLoading(false);
  };

  // P2: Load 3D preview data
  const load3DPreview = async () => {
    if (!currentWorld) return;
    setLoading(true);
    try {
      const response = await axios.get(`${API}/worlds/${currentWorld.id}/preview-3d`);
      setPreview3DData(response.data);
      setShow3DPreview(true);
    } catch (e) {
      console.error("Failed to load 3D preview:", e);
    }
    setLoading(false);
  };

  // P2: Toggle collaboration
  const toggleCollab = async () => {
    if (!currentWorld) return;
    
    if (!collabEnabled) {
      try {
        await axios.post(`${API}/collab/join`, {
          world_id: currentWorld.id,
          user_id: userId,
          action: "join"
        });
        setCollabEnabled(true);
      } catch (e) {
        console.error("Failed to join collab:", e);
      }
    } else {
      try {
        await axios.post(`${API}/collab/leave`, {
          world_id: currentWorld.id,
          user_id: userId,
          action: "leave"
        });
        setCollabEnabled(false);
        setCollabUsers([]);
      } catch (e) {
        console.error("Failed to leave collab:", e);
      }
    }
  };

  const autoZoom = (mapWidth) => {
    if (mapWidth > 256) setZoom(0.2);
    else if (mapWidth > 128) setZoom(0.3);
    else if (mapWidth > 64) setZoom(0.5);
    else setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  const loadWorld = async (worldId) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/worlds/${worldId}`);
      setCurrentWorld(response.data);
      setAiMessages([]);
      setHistory([response.data]);
      setHistoryIndex(0);
      autoZoom(response.data.map_width);
      setCollabEnabled(false);
      setCollabUsers([]);
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
        setHistory([]);
        setHistoryIndex(-1);
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

  // Map interaction handlers
  const handleMapMouseDown = useCallback((x, y, e) => {
    if (!currentWorld) return;
    
    if (activeTool === "pan" || e.button === 1 || (e.button === 0 && e.altKey)) {
      setIsPanning(true);
      lastPanPos.current = { x: e.clientX, y: e.clientY };
      return;
    }

    if (activeTool === "zone" || activeTool === "prefab") {
      setIsDragging(true);
      handleCellAction(x, y);
    } else if (activeTool === "select") {
      const zone = currentWorld.zones.find(z => z.x === x && z.y === y);
      const prefab = currentWorld.prefabs.find(p => p.x === x && p.y === y);
      if (zone) {
        setSelectedElement({ type: "zone", data: zone });
        setPropertiesOpen(true);
      } else if (prefab) {
        setSelectedElement({ type: "prefab", data: prefab });
        setPropertiesOpen(true);
      } else {
        setSelectedElement(null);
      }
    }
  }, [activeTool, currentWorld]);

  const handleMapMouseMove = useCallback((x, y, e) => {
    if (isPanning) {
      const dx = e.clientX - lastPanPos.current.x;
      const dy = e.clientY - lastPanPos.current.y;
      setPan(prev => ({ x: prev.x + dx, y: prev.y + dy }));
      lastPanPos.current = { x: e.clientX, y: e.clientY };
      return;
    }
    
    if (isDragging && (activeTool === "zone" || activeTool === "prefab")) {
      handleCellAction(x, y);
    }
  }, [isDragging, isPanning, activeTool]);

  const handleMapMouseUp = useCallback(() => {
    if (isDragging && currentWorld) {
      saveToHistory(currentWorld);
    }
    setIsDragging(false);
    setIsPanning(false);
  }, [isDragging, currentWorld, saveToHistory]);

  const handleCellAction = useCallback((x, y) => {
    if (!currentWorld) return;

    if (activeTool === "zone") {
      const existingIndex = currentWorld.zones.findIndex(z => z.x === x && z.y === y);
      if (existingIndex === -1) {
        const newZone = {
          id: `zone-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          type: selectedZoneType,
          x,
          y,
          width: 1,
          height: 1,
          difficulty: 1,
          biomes: []
        };
        setCurrentWorld(prev => ({
          ...prev,
          zones: [...prev.zones, newZone]
        }));
      }
    } else if (activeTool === "prefab") {
      const existingIndex = currentWorld.prefabs.findIndex(p => p.x === x && p.y === y);
      if (existingIndex === -1) {
        const newPrefab = {
          id: `prefab-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          type: selectedPrefabType,
          x,
          y,
          rotation: 0,
          scale: 1.0
        };
        setCurrentWorld(prev => ({
          ...prev,
          prefabs: [...prev.prefabs, newPrefab]
        }));
      }
    }
  }, [activeTool, selectedZoneType, selectedPrefabType, currentWorld]);

  const removeZone = (zoneId) => {
    if (!currentWorld) return;
    const newWorld = {
      ...currentWorld,
      zones: currentWorld.zones.filter(z => z.id !== zoneId)
    };
    setCurrentWorld(newWorld);
    saveToHistory(newWorld);
    setSelectedElement(null);
  };

  const removePrefab = (prefabId) => {
    if (!currentWorld) return;
    const newWorld = {
      ...currentWorld,
      prefabs: currentWorld.prefabs.filter(p => p.id !== prefabId)
    };
    setCurrentWorld(newWorld);
    saveToHistory(newWorld);
    setSelectedElement(null);
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

  const updateZoneProperty = (zoneId, property, value) => {
    if (!currentWorld) return;
    const newWorld = {
      ...currentWorld,
      zones: currentWorld.zones.map(z => 
        z.id === zoneId ? { ...z, [property]: value } : z
      )
    };
    setCurrentWorld(newWorld);
    setSelectedElement(prev => prev ? { ...prev, data: { ...prev.data, [property]: value } } : null);
  };

  const updateZoneBiomes = (zoneId, biomes) => {
    if (!currentWorld) return;
    const newWorld = {
      ...currentWorld,
      zones: currentWorld.zones.map(z =>
        z.id === zoneId ? { ...z, biomes } : z
      )
    };
    setCurrentWorld(newWorld);
    setSelectedElement(prev => prev ? { ...prev, data: { ...prev.data, biomes } } : null);
  };

  const updatePrefabProperty = (prefabId, property, value) => {
    if (!currentWorld) return;
    const newWorld = {
      ...currentWorld,
      prefabs: currentWorld.prefabs.map(p =>
        p.id === prefabId ? { ...p, [property]: value } : p
      )
    };
    setCurrentWorld(newWorld);
    setSelectedElement(prev => prev ? { ...prev, data: { ...prev.data, [property]: value } } : null);
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
      
      // Handle JAR export (binary)
      if (format === "jar" && response.data.data_base64) {
        const binaryString = atob(response.data.data_base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes], { type: "application/java-archive" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = response.data.filename || `${currentWorld.name}_worldgen.jar`;
        link.click();
        URL.revokeObjectURL(url);
        return;
      }
      
      // Handle prefab export
      if (format === "prefab") {
        const dataStr = JSON.stringify(response.data.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement("a");
        link.href = url;
        link.download = response.data.filename || `${currentWorld.name}.prefab.json`;
        link.click();
        URL.revokeObjectURL(url);
        return;
      }
      
      // Standard JSON export
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
              <Badge variant="outline" className="world-size-badge">
                {currentWorld.map_width}x{currentWorld.map_height}
              </Badge>
              {collabEnabled && (
                <Badge className="collab-badge">
                  <Users size={12} />
                  {collabUsers.length} online
                </Badge>
              )}
            </div>
          )}
        </div>
        <div className="header-right">
          {currentWorld && (
            <>
              <Button
                variant="ghost"
                size="icon"
                onClick={undo}
                disabled={historyIndex <= 0}
                title="Undo"
                data-testid="undo-btn"
              >
                <Undo2 size={18} />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={redo}
                disabled={historyIndex >= history.length - 1}
                title="Redo"
                data-testid="redo-btn"
              >
                <Redo2 size={18} />
              </Button>
              <div className="header-divider" />
              <Button
                variant={collabEnabled ? "default" : "ghost"}
                size="icon"
                onClick={toggleCollab}
                title="Collaboration"
                data-testid="collab-btn"
              >
                <Users size={18} />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={load3DPreview}
                title="3D Preview"
                data-testid="preview-3d-btn"
              >
                <Box size={18} />
              </Button>
              <div className="header-divider" />
            </>
          )}
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
        {/* Left Sidebar */}
        <aside className="sidebar-left" data-testid="sidebar-left">
          <div className="sidebar-section">
            <div className="section-header">
              <FolderOpen size={16} />
              <span>Worlds</span>
              <div className="section-actions">
                <Button variant="ghost" size="icon" onClick={() => setShowTemplateDialog(true)} title="From Template" data-testid="template-btn">
                  <LayoutTemplate size={16} />
                </Button>
                <Button variant="ghost" size="icon" onClick={() => setShowImportDialog(true)} title="Import" data-testid="import-btn">
                  <Upload size={16} />
                </Button>
                <Button variant="ghost" size="icon" onClick={() => setShowNewWorldDialog(true)} title="New World" data-testid="new-world-btn">
                  <Plus size={16} />
                </Button>
              </div>
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
                    <span className="world-item-seed">{world.seed} • {world.map_width}x{world.map_height}</span>
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
                  <p className="text-muted">Create or import a world</p>
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
                <Button variant={activeTool === "select" ? "default" : "secondary"} className="tool-btn" onClick={() => setActiveTool("select")} data-testid="tool-select">
                  <MousePointer size={16} />
                  Select
                </Button>
                <Button variant={activeTool === "zone" ? "default" : "secondary"} className="tool-btn" onClick={() => setActiveTool("zone")} data-testid="tool-zone">
                  <Paintbrush size={16} />
                  Zone
                </Button>
                <Button variant={activeTool === "prefab" ? "default" : "secondary"} className="tool-btn" onClick={() => setActiveTool("prefab")} data-testid="tool-prefab">
                  <Castle size={16} />
                  Prefab
                </Button>
                <Button variant={activeTool === "pan" ? "default" : "secondary"} className="tool-btn" onClick={() => setActiveTool("pan")} data-testid="tool-pan">
                  <Move size={16} />
                  Pan
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

          {/* P2: AI Auto-Generate */}
          {currentWorld && (
            <div className="sidebar-section">
              <Button 
                variant="outline" 
                className="auto-gen-btn" 
                onClick={() => setShowAutoGenDialog(true)}
                data-testid="auto-generate-btn"
              >
                <Wand2 size={16} />
                AI Auto-Generate
              </Button>
            </div>
          )}

          {/* Zoom Controls */}
          {currentWorld && (
            <div className="sidebar-section">
              <div className="section-header">
                <ZoomIn size={16} />
                <span>Zoom: {Math.round(zoom * 100)}%</span>
              </div>
              <div className="zoom-controls">
                <Button variant="secondary" size="icon" onClick={() => setZoom(z => Math.max(0.1, z - 0.1))} data-testid="zoom-out">
                  <ZoomOut size={16} />
                </Button>
                <Slider
                  value={[zoom]}
                  min={0.1}
                  max={2}
                  step={0.1}
                  onValueChange={([v]) => setZoom(v)}
                  className="zoom-slider"
                />
                <Button variant="secondary" size="icon" onClick={() => setZoom(z => Math.min(2, z + 0.1))} data-testid="zoom-in">
                  <ZoomIn size={16} />
                </Button>
              </div>
              <Button variant="ghost" size="sm" className="fit-btn" onClick={() => { autoZoom(currentWorld.map_width); }}>
                <Maximize2 size={14} />
                Reset View
              </Button>
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
                <Button variant="secondary" onClick={() => exportWorld("json")} data-testid="export-json-btn" title="Export as JSON">
                  <FileJson size={16} />
                  JSON
                </Button>
                <Button variant="secondary" onClick={() => exportWorld("hytale")} data-testid="export-hytale-btn" title="Export Hytale config">
                  <Download size={16} />
                  Hytale
                </Button>
              </div>
              <div className="export-buttons">
                <Button variant="secondary" onClick={() => exportWorld("prefab")} data-testid="export-prefab-btn" title="Export as .prefab.json">
                  <Layers size={16} />
                  Prefab
                </Button>
                <Button variant="secondary" onClick={() => exportWorld("jar")} data-testid="export-jar-btn" title="Export as .jar mod package">
                  <Box size={16} />
                  JAR
                </Button>
              </div>
            </div>
          )}
        </aside>

        {/* Main Canvas */}
        <main className="canvas-area" data-testid="canvas-area">
          {currentWorld ? (
            <>
              <MapCanvas
                world={currentWorld}
                onMouseDown={handleMapMouseDown}
                onMouseMove={handleMapMouseMove}
                onMouseUp={handleMapMouseUp}
                activeTool={activeTool}
                zoom={zoom}
                pan={pan}
                selectedElement={selectedElement}
              />
              <TerrainPanel terrain={currentWorld.terrain} onUpdate={updateTerrain} />
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
                  <p>Build worlds up to 512x512 tiles</p>
                  <div className="empty-actions">
                    <Button onClick={() => setShowNewWorldDialog(true)} data-testid="create-first-world-btn">
                      <Plus size={16} />
                      New World
                    </Button>
                    <Button variant="outline" onClick={() => setShowTemplateDialog(true)}>
                      <LayoutTemplate size={16} />
                      From Template
                    </Button>
                    <Button variant="outline" onClick={() => setShowImportDialog(true)}>
                      <Upload size={16} />
                      Import
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>

        {/* AI Panel */}
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
                  <p className="text-muted">Ask for suggestions or use AI Auto-Generate for full map population.</p>
                </div>
              ) : (
                aiMessages.map((msg, i) => (
                  <div key={i} className={`ai-message ${msg.role}`}>
                    <div className="ai-message-content">{msg.content}</div>
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
                placeholder={currentWorld ? "Ask for suggestions..." : "Create a world first"}
                disabled={!currentWorld || aiLoading}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendAiMessage();
                  }
                }}
                data-testid="ai-input"
              />
              <Button onClick={sendAiMessage} disabled={!currentWorld || !aiInput.trim() || aiLoading} className="ai-send-btn" data-testid="ai-send-btn">
                <Send size={16} />
              </Button>
            </div>
          </aside>
        )}

        {/* Properties Panel */}
        <Sheet open={propertiesOpen} onOpenChange={setPropertiesOpen}>
          <SheetContent side="right" className="properties-sheet">
            <SheetHeader>
              <SheetTitle className="properties-title">
                <Edit3 size={18} />
                {selectedElement?.type === "zone" ? "Zone Properties" : "Prefab Properties"}
              </SheetTitle>
            </SheetHeader>
            {selectedElement?.type === "zone" && (
              <ZonePropertiesPanel
                zone={selectedElement.data}
                onUpdate={updateZoneProperty}
                onUpdateBiomes={updateZoneBiomes}
                onDelete={() => { removeZone(selectedElement.data.id); setPropertiesOpen(false); }}
              />
            )}
            {selectedElement?.type === "prefab" && (
              <PrefabPropertiesPanel
                prefab={selectedElement.data}
                onUpdate={updatePrefabProperty}
                onDelete={() => { removePrefab(selectedElement.data.id); setPropertiesOpen(false); }}
              />
            )}
          </SheetContent>
        </Sheet>
      </div>

      {/* New World Dialog */}
      <Dialog open={showNewWorldDialog} onOpenChange={setShowNewWorldDialog}>
        <DialogContent className="dialog-content">
          <DialogHeader>
            <DialogTitle>Create New World</DialogTitle>
          </DialogHeader>
          <div className="dialog-form">
            <div className="form-group">
              <Label>World Name</Label>
              <Input value={newWorldName} onChange={(e) => setNewWorldName(e.target.value)} placeholder="My Hytale World" data-testid="new-world-name-input" />
            </div>
            <div className="form-group">
              <Label>Seed (optional)</Label>
              <div className="seed-input-group">
                <Input value={newWorldSeed} onChange={(e) => setNewWorldSeed(e.target.value)} placeholder="Auto-generate" data-testid="new-world-seed-input" />
                <Button variant="secondary" size="icon" onClick={generateSeed}><RefreshCw size={16} /></Button>
              </div>
            </div>
            <div className="form-group">
              <Label>Map Size</Label>
              <Select value={`${newWorldSize.width}x${newWorldSize.height}`} onValueChange={(v) => {
                const preset = MAP_SIZE_PRESETS.find(p => `${p.width}x${p.height}` === v);
                if (preset) setNewWorldSize({ width: preset.width, height: preset.height });
              }}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {MAP_SIZE_PRESETS.map((p) => (
                    <SelectItem key={p.label} value={`${p.width}x${p.height}`}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={createWorld} disabled={!newWorldName.trim() || loading} data-testid="create-world-btn">
              {loading ? <Loader2 className="animate-spin" size={16} /> : <Plus size={16} />}
              Create World
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* P2: Template Dialog */}
      <Dialog open={showTemplateDialog} onOpenChange={setShowTemplateDialog}>
        <DialogContent className="dialog-content dialog-lg">
          <DialogHeader>
            <DialogTitle>Create from Template</DialogTitle>
          </DialogHeader>
          <div className="dialog-form">
            <div className="form-group">
              <Label>World Name</Label>
              <Input value={newWorldName} onChange={(e) => setNewWorldName(e.target.value)} placeholder="My World" />
            </div>
            <div className="form-group">
              <Label>Map Size</Label>
              <Select value={`${newWorldSize.width}x${newWorldSize.height}`} onValueChange={(v) => {
                const preset = MAP_SIZE_PRESETS.find(p => `${p.width}x${p.height}` === v);
                if (preset) setNewWorldSize({ width: preset.width, height: preset.height });
              }}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {MAP_SIZE_PRESETS.map((p) => (
                    <SelectItem key={p.label} value={`${p.width}x${p.height}`}>{p.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Label>Select Template</Label>
            <div className="template-grid">
              {templates.map((t) => {
                const Icon = TEMPLATE_ICONS[t.id] || Map;
                return (
                  <Card 
                    key={t.id} 
                    className={`template-card ${selectedTemplate === t.id ? 'selected' : ''}`}
                    onClick={() => setSelectedTemplate(t.id)}
                    data-testid={`template-${t.id}`}
                  >
                    <CardHeader className="template-card-header">
                      <Icon size={24} />
                      <CardTitle className="template-card-title">{t.name}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription>{t.description}</CardDescription>
                      <div className="template-difficulty">
                        Difficulty: {t.difficulty_range[0]}-{t.difficulty_range[1]}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
            <Button onClick={createFromTemplate} disabled={!newWorldName.trim() || !selectedTemplate || loading} data-testid="create-from-template-btn">
              {loading ? <Loader2 className="animate-spin" size={16} /> : <LayoutTemplate size={16} />}
              Create from Template
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* P2: Import Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent className="dialog-content">
          <DialogHeader>
            <DialogTitle>Import World</DialogTitle>
          </DialogHeader>
          <div className="dialog-form">
            <div className="form-group">
              <Label>World Name (optional)</Label>
              <Input value={newWorldName} onChange={(e) => setNewWorldName(e.target.value)} placeholder="Auto-detect from config" />
            </div>
            <div className="form-group">
              <Label>JSON Configuration</Label>
              <Textarea 
                value={importConfig} 
                onChange={(e) => setImportConfig(e.target.value)} 
                placeholder="Paste your world JSON config here..."
                className="import-textarea"
                data-testid="import-config-input"
              />
            </div>
            <Button onClick={importWorld} disabled={!importConfig.trim() || loading} data-testid="import-world-btn">
              {loading ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />}
              Import World
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* P2: AI Auto-Generate Dialog */}
      <Dialog open={showAutoGenDialog} onOpenChange={setShowAutoGenDialog}>
        <DialogContent className="dialog-content">
          <DialogHeader>
            <DialogTitle>AI Auto-Generate World</DialogTitle>
          </DialogHeader>
          <div className="dialog-form">
            <p className="form-hint">Describe the world you want and AI will generate zones, prefabs, and terrain settings.</p>
            <div className="form-group">
              <Label>Prompt</Label>
              <Textarea 
                value={autoGenPrompt} 
                onChange={(e) => setAutoGenPrompt(e.target.value)} 
                placeholder="e.g., Create a challenging dungeon-crawler with corrupted zones in the center surrounded by emerald groves. Add many dungeons and ruins."
                className="autogen-textarea"
                data-testid="autogen-prompt-input"
              />
            </div>
            <div className="form-group">
              <Label>AI Provider</Label>
              <Select value={aiProvider} onValueChange={setAiProvider}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="openai">GPT-5.2</SelectItem>
                  <SelectItem value="anthropic">Claude</SelectItem>
                  <SelectItem value="gemini">Gemini</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={autoGenerateWorld} disabled={!autoGenPrompt.trim() || autoGenLoading} data-testid="generate-world-btn">
              {autoGenLoading ? <Loader2 className="animate-spin" size={16} /> : <Wand2 size={16} />}
              Generate World
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* P2: 3D Preview Dialog */}
      <Dialog open={show3DPreview} onOpenChange={setShow3DPreview}>
        <DialogContent className="dialog-content dialog-xl">
          <DialogHeader>
            <DialogTitle>3D World Preview</DialogTitle>
          </DialogHeader>
          {preview3DData && (
            <Preview3D data={preview3DData} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Map Canvas Component
function MapCanvas({ world, onMouseDown, onMouseMove, onMouseUp, activeTool, zoom, pan, selectedElement }) {
  const containerRef = useRef(null);
  const [visibleRange, setVisibleRange] = useState({ startX: 0, endX: 50, startY: 0, endY: 50 });
  
  const cellSize = Math.max(8, Math.min(32, Math.floor(800 / Math.max(world.map_width, world.map_height))));
  const scaledCellSize = cellSize * zoom;

  useEffect(() => {
    const updateVisibleRange = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const buffer = 5;
      
      const startX = Math.max(0, Math.floor(-pan.x / scaledCellSize) - buffer);
      const endX = Math.min(world.map_width, Math.ceil((rect.width - pan.x) / scaledCellSize) + buffer);
      const startY = Math.max(0, Math.floor(-pan.y / scaledCellSize) - buffer);
      const endY = Math.min(world.map_height, Math.ceil((rect.height - pan.y) / scaledCellSize) + buffer);
      
      setVisibleRange({ startX, endX, startY, endY });
    };
    
    updateVisibleRange();
    window.addEventListener('resize', updateVisibleRange);
    return () => window.removeEventListener('resize', updateVisibleRange);
  }, [pan, zoom, scaledCellSize, world.map_width, world.map_height]);

  const zoneMap = {};
  world.zones.forEach(zone => { zoneMap[`${zone.x}-${zone.y}`] = zone; });

  const prefabMap = {};
  world.prefabs.forEach(prefab => {
    const key = `${prefab.x}-${prefab.y}`;
    if (!prefabMap[key]) prefabMap[key] = [];
    prefabMap[key].push(prefab);
  });

  const visibleCells = [];
  for (let y = visibleRange.startY; y < visibleRange.endY; y++) {
    for (let x = visibleRange.startX; x < visibleRange.endX; x++) {
      const key = `${x}-${y}`;
      const zone = zoneMap[key];
      const prefabs = prefabMap[key] || [];
      const isSelected = selectedElement && (
        (selectedElement.type === "zone" && zone?.id === selectedElement.data.id) ||
        (selectedElement.type === "prefab" && prefabs.some(p => p.id === selectedElement.data.id))
      );
      visibleCells.push({ x, y, key, zone, prefabs, isSelected });
    }
  }

  const handleMouseEvent = (e, type) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.floor((e.clientX - rect.left - pan.x) / scaledCellSize);
    const y = Math.floor((e.clientY - rect.top - pan.y) / scaledCellSize);
    
    if (x >= 0 && x < world.map_width && y >= 0 && y < world.map_height) {
      if (type === 'down') onMouseDown(x, y, e);
      else if (type === 'move') onMouseMove(x, y, e);
    }
    if (type === 'up') onMouseUp();
  };

  return (
    <div className="map-canvas-container" data-testid="map-canvas">
      <div 
        ref={containerRef}
        className="map-viewport"
        onMouseDown={(e) => handleMouseEvent(e, 'down')}
        onMouseMove={(e) => handleMouseEvent(e, 'move')}
        onMouseUp={(e) => handleMouseEvent(e, 'up')}
        onMouseLeave={(e) => handleMouseEvent(e, 'up')}
        style={{ cursor: activeTool === 'pan' ? 'grab' : activeTool === 'select' ? 'default' : 'crosshair' }}
      >
        <div 
          className="map-grid-container"
          style={{
            width: world.map_width * scaledCellSize,
            height: world.map_height * scaledCellSize,
            transform: `translate(${pan.x}px, ${pan.y}px)`,
            backgroundSize: `${scaledCellSize}px ${scaledCellSize}px`,
            backgroundImage: `linear-gradient(to right, var(--border-default) 1px, transparent 1px), linear-gradient(to bottom, var(--border-default) 1px, transparent 1px)`
          }}
        >
          {visibleCells.map(({ x, y, key, zone, prefabs, isSelected }) => {
            const ZoneIcon = zone ? ZONE_CONFIG[zone.type]?.icon : null;
            return (
              <div
                key={key}
                className={`map-cell-abs ${isSelected ? 'selected' : ''}`}
                style={{
                  left: x * scaledCellSize,
                  top: y * scaledCellSize,
                  width: scaledCellSize,
                  height: scaledCellSize,
                  backgroundColor: zone ? `${ZONE_CONFIG[zone.type]?.color}50` : 'transparent',
                  borderColor: isSelected ? '#fff' : (zone ? ZONE_CONFIG[zone.type]?.color : 'transparent')
                }}
                data-testid={`cell-${x}-${y}`}
              >
                {zone && scaledCellSize > 16 && (
                  <div className="cell-content">
                    {ZoneIcon && <ZoneIcon size={Math.min(14, scaledCellSize * 0.5)} style={{ color: ZONE_CONFIG[zone.type]?.color }} />}
                  </div>
                )}
                {prefabs.map((prefab) => {
                  const PrefabIcon = PREFAB_CONFIG[prefab.type]?.icon;
                  return (
                    <div key={prefab.id} className="cell-prefab-marker">
                      {PrefabIcon && scaledCellSize > 12 && <PrefabIcon size={Math.min(12, scaledCellSize * 0.4)} />}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
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
          <span className="legend-title">Stats</span>
          <span className="legend-stat">{world.zones.length} zones</span>
          <span className="legend-stat">{world.prefabs.length} prefabs</span>
        </div>
      </div>
    </div>
  );
}

// Zone Properties Panel
function ZonePropertiesPanel({ zone, onUpdate, onUpdateBiomes, onDelete }) {
  const zoneConfig = ZONE_CONFIG[zone.type];
  const availableBiomes = Object.entries(BIOME_CONFIG).filter(([_, b]) => b.zones.includes(zone.type));

  const toggleBiome = (biomeId) => {
    const currentBiomes = zone.biomes || [];
    const existingIndex = currentBiomes.findIndex(b => b.type === biomeId);
    if (existingIndex >= 0) {
      onUpdateBiomes(zone.id, currentBiomes.filter((_, i) => i !== existingIndex));
    } else {
      onUpdateBiomes(zone.id, [...currentBiomes, { type: biomeId, density: 0.5, variation: 0.3 }]);
    }
  };

  const updateBiomeSetting = (biomeId, key, value) => {
    const currentBiomes = zone.biomes || [];
    onUpdateBiomes(zone.id, currentBiomes.map(b => b.type === biomeId ? { ...b, [key]: value } : b));
  };

  return (
    <div className="properties-panel">
      <div className="property-group">
        <Label>Zone Type</Label>
        <div className="zone-type-display">
          <div className="color-dot large" style={{ backgroundColor: zoneConfig.color }} />
          <span>{zoneConfig.name}</span>
        </div>
      </div>
      <div className="property-group">
        <Label>Position</Label>
        <div className="position-display">X: {zone.x}, Y: {zone.y}</div>
      </div>
      <div className="property-group">
        <Label>Difficulty (1-10)</Label>
        <div className="slider-with-value">
          <Slider value={[zone.difficulty || 1]} min={1} max={10} step={1} onValueChange={([v]) => onUpdate(zone.id, 'difficulty', v)} />
          <span className="slider-value">{zone.difficulty || 1}</span>
        </div>
      </div>
      <div className="property-group">
        <Label className="flex items-center gap-2"><Layers size={14} />Biomes</Label>
        <div className="biome-list">
          {availableBiomes.map(([biomeId, biomeConfig]) => {
            const isActive = zone.biomes?.some(b => b.type === biomeId);
            const biomeData = zone.biomes?.find(b => b.type === biomeId);
            return (
              <div key={biomeId} className={`biome-item ${isActive ? 'active' : ''}`}>
                <div className="biome-header" onClick={() => toggleBiome(biomeId)}>
                  <div className="color-dot" style={{ backgroundColor: biomeConfig.color }} />
                  <span>{biomeConfig.name}</span>
                  <input type="checkbox" checked={isActive} readOnly />
                </div>
                {isActive && biomeData && (
                  <div className="biome-settings">
                    <div className="biome-slider">
                      <span>Density</span>
                      <Slider value={[biomeData.density || 0.5]} min={0} max={1} step={0.1} onValueChange={([v]) => updateBiomeSetting(biomeId, 'density', v)} />
                      <span>{(biomeData.density || 0.5).toFixed(1)}</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <Button variant="destructive" onClick={onDelete} className="delete-btn"><Trash2 size={16} />Delete Zone</Button>
    </div>
  );
}

// Prefab Properties Panel
function PrefabPropertiesPanel({ prefab, onUpdate, onDelete }) {
  const prefabConfig = PREFAB_CONFIG[prefab.type];
  const Icon = prefabConfig.icon;

  return (
    <div className="properties-panel">
      <div className="property-group">
        <Label>Structure Type</Label>
        <div className="prefab-type-display"><Icon size={18} /><span>{prefabConfig.name}</span></div>
      </div>
      <div className="property-group">
        <Label>Position</Label>
        <div className="position-display">X: {prefab.x}, Y: {prefab.y}</div>
      </div>
      <div className="property-group">
        <Label>Rotation</Label>
        <Select value={String(prefab.rotation || 0)} onValueChange={(v) => onUpdate(prefab.id, 'rotation', parseInt(v))}>
          <SelectTrigger><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="0">0°</SelectItem>
            <SelectItem value="90">90°</SelectItem>
            <SelectItem value="180">180°</SelectItem>
            <SelectItem value="270">270°</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div className="property-group">
        <Label>Scale</Label>
        <div className="slider-with-value">
          <Slider value={[prefab.scale || 1]} min={0.5} max={2} step={0.1} onValueChange={([v]) => onUpdate(prefab.id, 'scale', v)} />
          <span className="slider-value">{(prefab.scale || 1).toFixed(1)}x</span>
        </div>
      </div>
      <Button variant="destructive" onClick={onDelete} className="delete-btn"><Trash2 size={16} />Delete Structure</Button>
    </div>
  );
}

// Terrain Panel
function TerrainPanel({ terrain, onUpdate }) {
  return (
    <div className="terrain-panel" data-testid="terrain-panel">
      <h3 className="terrain-title"><Mountain size={16} />Terrain Settings</h3>
      <div className="terrain-controls">
        {[
          { key: "height_scale", label: "Height", min: 0.1, max: 3, default: 1 },
          { key: "cave_density", label: "Caves", min: 0, max: 1, default: 0.5 },
          { key: "river_frequency", label: "Rivers", min: 0, max: 1, default: 0.3 },
          { key: "mountain_scale", label: "Mountains", min: 0, max: 1, default: 0.5 },
          { key: "ocean_level", label: "Ocean", min: 0, max: 1, default: 0.3 }
        ].map(({ key, label, min, max, default: def }) => (
          <div key={key} className="terrain-control">
            <div className="control-header">
              <Label>{label}</Label>
              <span className="control-value">{(terrain?.[key] || def).toFixed(2)}</span>
            </div>
            <Slider value={[terrain?.[key] || def]} min={min} max={max} step={0.05} onValueChange={([v]) => onUpdate(key, v)} />
          </div>
        ))}
      </div>
    </div>
  );
}

// P2: 3D Preview Component
function Preview3D({ data }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current || !data) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    const { dimensions, height_map, zones, terrain } = data;
    const cellSize = Math.min(600 / dimensions.width, 400 / dimensions.height);
    
    canvas.width = dimensions.width * cellSize;
    canvas.height = dimensions.height * cellSize;
    
    // Create a zone lookup
    const zoneMap = {};
    zones.forEach(z => { zoneMap[`${z.x}-${z.y}`] = z; });

    // Draw height map with zone colors
    for (let y = 0; y < dimensions.height; y++) {
      for (let x = 0; x < dimensions.width; x++) {
        const height = height_map[y]?.[x] || 0.5;
        const zone = zoneMap[`${x}-${y}`];
        
        let baseColor;
        if (zone) {
          const zoneColors = {
            emerald_grove: [16, 185, 129],
            borea: [6, 182, 212],
            desert: [245, 158, 11],
            arctic: [226, 232, 240],
            corrupted: [139, 92, 246]
          };
          baseColor = zoneColors[zone.type] || [107, 114, 128];
        } else {
          // Water or empty
          if (height < terrain.ocean_level) {
            baseColor = [30, 64, 175]; // Water
          } else {
            baseColor = [71, 85, 105]; // Empty land
          }
        }
        
        // Apply height shading
        const brightness = 0.5 + height * 0.5;
        const r = Math.min(255, Math.floor(baseColor[0] * brightness));
        const g = Math.min(255, Math.floor(baseColor[1] * brightness));
        const b = Math.min(255, Math.floor(baseColor[2] * brightness));
        
        ctx.fillStyle = `rgb(${r}, ${g}, ${b})`;
        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
      }
    }
    
    // Draw prefabs as markers
    data.prefabs.forEach(p => {
      ctx.fillStyle = '#fff';
      ctx.beginPath();
      ctx.arc(p.position.x * cellSize + cellSize/2, p.position.y * cellSize + cellSize/2, cellSize/3, 0, Math.PI * 2);
      ctx.fill();
    });
    
  }, [data]);

  return (
    <div className="preview-3d-container">
      <canvas ref={canvasRef} className="preview-3d-canvas" />
      <div className="preview-3d-info">
        <p>Height-mapped terrain view with zone coloring</p>
        <p className="text-muted">White dots indicate structure locations</p>
      </div>
    </div>
  );
}

export default App;
