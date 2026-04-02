import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API, WS_URL } from "@/config";
import { AuthProvider, useAuth } from "./AuthContext";
import { SubscriptionProvider, useSubscription } from "./SubscriptionContext";
import { SocialProvider, useSocial } from "./SocialContext";

const AppInternalContext = createContext(null);

function AppInternalProvider({ children }) {
  const auth = useAuth();
  const sub = useSubscription();
  const social = useSocial();
  const { currentUser } = auth;
  const { isFeatureGated, setShowPricingDialog } = sub;

  // Core
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

  // Undo/Redo
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Properties
  const [selectedElement, setSelectedElement] = useState(null);
  const [propertiesOpen, setPropertiesOpen] = useState(false);

  // Map controls
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const lastPanPos = useRef({ x: 0, y: 0 });

  // Templates
  const [templates, setTemplates] = useState([]);
  const [showTemplateDialog, setShowTemplateDialog] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // Import
  const [showImportDialog, setShowImportDialog] = useState(false);
  const [importConfig, setImportConfig] = useState("");

  // AI Auto-generate
  const [showAutoGenDialog, setShowAutoGenDialog] = useState(false);
  const [autoGenPrompt, setAutoGenPrompt] = useState("");
  const [autoGenLoading, setAutoGenLoading] = useState(false);

  // 3D Preview
  const [show3DPreview, setShow3DPreview] = useState(false);
  const [preview3DData, setPreview3DData] = useState(null);

  // Collaboration
  const [collabEnabled, setCollabEnabled] = useState(false);
  const [collabUsers, setCollabUsers] = useState([]);
  const [userId] = useState(`user-${Math.random().toString(36).substr(2, 9)}`);

  // Gallery
  const [showGalleryDialog, setShowGalleryDialog] = useState(false);
  const [galleryEntries, setGalleryEntries] = useState([]);
  const [galleryLoading, setGalleryLoading] = useState(false);
  const [gallerySearch, setGallerySearch] = useState("");
  const [gallerySort, setGallerySort] = useState("recent");
  const [showPublishDialog, setShowPublishDialog] = useState(false);
  const [publishData, setPublishData] = useState({ description: "", creator_name: "", tags: "" });

  // Custom Prefabs
  const [showCustomPrefabDialog, setShowCustomPrefabDialog] = useState(false);
  const [customPrefabs, setCustomPrefabs] = useState([]);
  const [newPrefab, setNewPrefab] = useState({ name: "", description: "", icon: "cube", color: "#6B7280", category: "custom", is_public: false, tags: "" });

  // Analytics
  const [showAnalyticsDialog, setShowAnalyticsDialog] = useState(false);
  const [analyticsData, setAnalyticsData] = useState(null);

  // Procedural Preview
  const [showProceduralPreview, setShowProceduralPreview] = useState(false);
  const [proceduralSteps, setProceduralSteps] = useState([]);
  const [currentPreviewStep, setCurrentPreviewStep] = useState(0);
  const [previewPlaying, setPreviewPlaying] = useState(false);

  // WebSocket
  const wsRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [collabCursors, setCollabCursors] = useState({});
  const [collabChat, setCollabChat] = useState([]);

  // Versions
  const [showVersionDialog, setShowVersionDialog] = useState(false);
  const [worldVersions, setWorldVersions] = useState([]);

  // Reviews
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviews, setReviews] = useState([]);
  const [newReview, setNewReview] = useState({ rating: 5, comment: "" });
  const [selectedGalleryForReview, setSelectedGalleryForReview] = useState(null);

  // Gallery filters
  const [galleryFilterZones, setGalleryFilterZones] = useState("");
  const [galleryFilterMinRating, setGalleryFilterMinRating] = useState(0);
  const [galleryFilterMapMin, setGalleryFilterMapMin] = useState("");
  const [galleryFilterMapMax, setGalleryFilterMapMax] = useState("");
  const [galleryFollowingOnly, setGalleryFollowingOnly] = useState(false);

  // Collaborators
  const [showCollabDialog, setShowCollabDialog] = useState(false);
  const [worldCollaborators, setWorldCollaborators] = useState({ owner: null, collaborators: [] });
  const [collabInviteEmail, setCollabInviteEmail] = useState("");
  const [collabInviteRole, setCollabInviteRole] = useState("viewer");

  // Thumbnails
  const [thumbnails, setThumbnails] = useState({});

  // Mobile
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [mobileAiPanelOpen, setMobileAiPanelOpen] = useState(false);

  // Install to Game / How-To / Share / PWA
  const [showInstallDialog, setShowInstallDialog] = useState(false);
  const [showHowToDialog, setShowHowToDialog] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [shareInfo, setShareInfo] = useState({ share_enabled: false, share_token: null });
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [pwaInstallable, setPwaInstallable] = useState(false);

  // ========== INIT ==========
  useEffect(() => {
    if (currentUser) { fetchWorlds(); fetchTemplates(); fetchCustomPrefabs(); }
  }, [currentUser]);

  // PWA
  useEffect(() => {
    const handler = (e) => { e.preventDefault(); setDeferredPrompt(e); setPwaInstallable(true); };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const triggerPwaInstall = async () => {
    if (!deferredPrompt) return false;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    setDeferredPrompt(null); setPwaInstallable(false);
    return result.outcome === "accepted";
  };

  // ========== SHARE ==========
  const fetchShareInfo = async (worldId) => {
    try { const r = await axios.get(`${API}/worlds/${worldId}/share`); setShareInfo(r.data); }
    catch (e) { setShareInfo({ share_enabled: false, share_token: null }); }
  };

  const toggleShare = async () => {
    if (!currentWorld) return;
    try { const r = await axios.post(`${API}/worlds/${currentWorld.id}/share`); setShareInfo(r.data); return r.data; }
    catch (e) { alert(e.response?.data?.detail || "Failed to toggle sharing"); }
  };

  // ========== THUMBNAILS ==========
  const fetchThumbnail = async (worldId) => {
    if (thumbnails[worldId]) return;
    try {
      const response = await axios.get(`${API}/worlds/${worldId}/thumbnail`);
      if (response.data.thumbnail) setThumbnails(prev => ({ ...prev, [worldId]: response.data.thumbnail }));
    } catch (e) { /* ignore */ }
  };

  const regenerateThumbnail = async (worldId) => {
    try {
      const response = await axios.post(`${API}/worlds/${worldId}/thumbnail`);
      if (response.data.thumbnail) setThumbnails(prev => ({ ...prev, [worldId]: response.data.thumbnail }));
    } catch (e) { /* ignore */ }
  };

  // ========== WORLD CRUD ==========
  const fetchWorlds = async () => {
    try {
      const response = await axios.get(`${API}/worlds`);
      setWorlds(Array.isArray(response.data) ? response.data : response.data.worlds || []);
    } catch (e) { console.error("Failed to fetch worlds:", e); }
  };

  const createWorld = async () => {
    if (!newWorldName.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post(`${API}/worlds`, { name: newWorldName, seed: newWorldSeed || null, map_width: newWorldSize.width, map_height: newWorldSize.height });
      setCurrentWorld(response.data); fetchWorlds();
      setShowNewWorldDialog(false); setNewWorldName(""); setNewWorldSeed("");
      saveToHistory(response.data); autoZoom(response.data.map_width);
    } catch (e) { console.error("Failed to create world:", e); }
    setLoading(false);
  };

  const loadWorld = async (worldId) => {
    try {
      const response = await axios.get(`${API}/worlds/${worldId}`);
      setCurrentWorld(response.data); setHistory([response.data]); setHistoryIndex(0);
      autoZoom(response.data.map_width);
    } catch (e) { console.error("Failed to load world:", e); }
  };

  const saveWorld = async () => {
    if (!currentWorld) return;
    setLoading(true);
    try {
      await axios.put(`${API}/worlds/${currentWorld.id}`, {
        name: currentWorld.name, terrain: currentWorld.terrain,
        zones: currentWorld.zones, prefabs: currentWorld.prefabs, ai_provider: aiProvider
      });
      regenerateThumbnail(currentWorld.id);
    } catch (e) { console.error("Failed to save world:", e); }
    setLoading(false);
  };

  const deleteWorld = async (worldId) => {
    try {
      await axios.delete(`${API}/worlds/${worldId}`);
      if (currentWorld?.id === worldId) setCurrentWorld(null);
      fetchWorlds();
    } catch (e) { console.error("Failed to delete world:", e); }
  };

  // ========== HISTORY ==========
  const saveToHistory = useCallback((world) => {
    setHistory(prev => {
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push(JSON.parse(JSON.stringify(world)));
      if (newHistory.length > 50) newHistory.shift();
      return newHistory;
    });
    setHistoryIndex(prev => Math.min(prev + 1, 49));
  }, [historyIndex]);

  const undo = useCallback(() => {
    if (historyIndex <= 0) return;
    const newIndex = historyIndex - 1;
    setHistoryIndex(newIndex);
    setCurrentWorld(JSON.parse(JSON.stringify(history[newIndex])));
  }, [history, historyIndex]);

  const redo = useCallback(() => {
    if (historyIndex >= history.length - 1) return;
    const newIndex = historyIndex + 1;
    setHistoryIndex(newIndex);
    setCurrentWorld(JSON.parse(JSON.stringify(history[newIndex])));
  }, [history, historyIndex]);

  const autoZoom = (mapWidth) => {
    if (mapWidth <= 64) setZoom(1);
    else if (mapWidth <= 128) setZoom(0.5);
    else if (mapWidth <= 256) setZoom(0.3);
    else setZoom(0.2);
    setPan({ x: 0, y: 0 });
  };

  // ========== MAP INTERACTIONS ==========
  const handleMapMouseDown = (x, y, e) => {
    if (activeTool === "pan") { setIsPanning(true); lastPanPos.current = { x: e.clientX, y: e.clientY }; return; }
    if (activeTool === "zone") { setIsDragging(true); addZone(x, y); }
    else if (activeTool === "prefab") addPrefab(x, y);
    else if (activeTool === "select") selectElement(x, y);
  };

  const handleMapMouseMove = (x, y, e) => {
    if (isPanning) {
      const dx = e.clientX - lastPanPos.current.x; const dy = e.clientY - lastPanPos.current.y;
      setPan(p => ({ x: p.x + dx, y: p.y + dy }));
      lastPanPos.current = { x: e.clientX, y: e.clientY }; return;
    }
    if (isDragging && activeTool === "zone") addZone(x, y);
    if (collabEnabled && wsRef.current?.readyState === WebSocket.OPEN)
      wsRef.current.send(JSON.stringify({ type: "cursor_move", x, y }));
  };

  const handleMapMouseUp = () => {
    if (isDragging && currentWorld) saveToHistory(currentWorld);
    setIsDragging(false); setIsPanning(false);
  };

  const addZone = (x, y) => {
    if (!currentWorld) return;
    const existingIndex = currentWorld.zones.findIndex(z => z.x === x && z.y === y);
    let updatedZones;
    if (existingIndex >= 0) { updatedZones = [...currentWorld.zones]; updatedZones[existingIndex] = { ...updatedZones[existingIndex], type: selectedZoneType }; }
    else updatedZones = [...currentWorld.zones, { id: `zone-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`, type: selectedZoneType, x, y, difficulty: 1, biomes: [] }];
    const updatedWorld = { ...currentWorld, zones: updatedZones };
    setCurrentWorld(updatedWorld);
    if (!isDragging) saveToHistory(updatedWorld);
    if (collabEnabled) sendWsMessage("zone_add", { zone: updatedZones[updatedZones.length - 1] });
  };

  const addPrefab = (x, y) => {
    if (!currentWorld) return;
    const newP = { id: `prefab-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`, type: selectedPrefabType, x, y, rotation: 0, scale: 1 };
    const updatedWorld = { ...currentWorld, prefabs: [...currentWorld.prefabs, newP] };
    setCurrentWorld(updatedWorld); saveToHistory(updatedWorld);
    if (collabEnabled) sendWsMessage("prefab_add", { prefab: newP });
  };

  const selectElement = (x, y) => {
    if (!currentWorld) return;
    const zone = currentWorld.zones.find(z => z.x === x && z.y === y);
    const prefab = currentWorld.prefabs.find(p => p.x === x && p.y === y);
    if (prefab) { setSelectedElement({ type: "prefab", data: prefab }); setPropertiesOpen(true); }
    else if (zone) { setSelectedElement({ type: "zone", data: zone }); setPropertiesOpen(true); }
    else { setSelectedElement(null); setPropertiesOpen(false); }
  };

  const updateZoneProperty = (zoneId, key, value) => {
    if (!currentWorld) return;
    const updatedWorld = { ...currentWorld, zones: currentWorld.zones.map(z => z.id === zoneId ? { ...z, [key]: value } : z) };
    setCurrentWorld(updatedWorld); saveToHistory(updatedWorld);
  };

  const updateZoneBiomes = (zoneId, biomes) => {
    if (!currentWorld) return;
    const updatedWorld = { ...currentWorld, zones: currentWorld.zones.map(z => z.id === zoneId ? { ...z, biomes } : z) };
    setCurrentWorld(updatedWorld); saveToHistory(updatedWorld);
  };

  const deleteZone = () => {
    if (!currentWorld || !selectedElement || selectedElement.type !== "zone") return;
    const updatedWorld = { ...currentWorld, zones: currentWorld.zones.filter(z => z.id !== selectedElement.data.id) };
    setCurrentWorld(updatedWorld); saveToHistory(updatedWorld); setSelectedElement(null); setPropertiesOpen(false);
  };

  const updatePrefabProperty = (prefabId, key, value) => {
    if (!currentWorld) return;
    const updatedWorld = { ...currentWorld, prefabs: currentWorld.prefabs.map(p => p.id === prefabId ? { ...p, [key]: value } : p) };
    setCurrentWorld(updatedWorld); saveToHistory(updatedWorld);
  };

  const deletePrefab = () => {
    if (!currentWorld || !selectedElement || selectedElement.type !== "prefab") return;
    const updatedWorld = { ...currentWorld, prefabs: currentWorld.prefabs.filter(p => p.id !== selectedElement.data.id) };
    setCurrentWorld(updatedWorld); saveToHistory(updatedWorld); setSelectedElement(null); setPropertiesOpen(false);
  };

  const updateTerrain = (key, value) => {
    if (!currentWorld) return;
    const updatedWorld = { ...currentWorld, terrain: { ...(currentWorld.terrain || {}), [key]: value } };
    setCurrentWorld(updatedWorld); saveToHistory(updatedWorld);
  };

  // ========== AI ==========
  const sendAiMessage = async () => {
    if (!currentWorld || !aiInput.trim()) return;
    if (isFeatureGated("ai")) { setShowPricingDialog(true); return; }
    const userMsg = { role: "user", content: aiInput };
    setAiMessages(prev => [...prev, userMsg]); setAiInput(""); setAiLoading(true);
    try {
      const response = await axios.post(`${API}/ai/chat`, { world_id: currentWorld.id, message: aiInput, provider: aiProvider });
      setAiMessages(prev => [...prev, { role: "assistant", content: response.data.response }]);
      if (response.data.suggestions) {
        const s = response.data.suggestions;
        if (s.zones || s.prefabs || s.terrain) {
          const updatedWorld = { ...currentWorld };
          if (s.zones) updatedWorld.zones = [...updatedWorld.zones, ...s.zones];
          if (s.prefabs) updatedWorld.prefabs = [...updatedWorld.prefabs, ...s.prefabs];
          if (s.terrain) updatedWorld.terrain = { ...(updatedWorld.terrain || {}), ...s.terrain };
          setCurrentWorld(updatedWorld); saveToHistory(updatedWorld);
        }
      }
    } catch (e) { setAiMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]); }
    setAiLoading(false);
  };

  // ========== TEMPLATES ==========
  const fetchTemplates = async () => {
    try { const r = await axios.get(`${API}/templates`); setTemplates(r.data.templates || []); }
    catch (e) { console.error("Failed to fetch templates:", e); }
  };

  const createFromTemplate = async () => {
    if (!selectedTemplate || !newWorldName.trim()) return;
    setLoading(true);
    try {
      const r = await axios.post(`${API}/worlds/from-template`, { name: newWorldName, template: selectedTemplate, map_width: newWorldSize.width, map_height: newWorldSize.height });
      setCurrentWorld(r.data); fetchWorlds();
      setShowTemplateDialog(false); setNewWorldName(""); setSelectedTemplate(null);
      saveToHistory(r.data); autoZoom(r.data.map_width);
    } catch (e) { console.error("Failed to create from template:", e); }
    setLoading(false);
  };

  // ========== IMPORT ==========
  const importWorld = async () => {
    if (!importConfig.trim()) return;
    setLoading(true);
    try {
      const config = JSON.parse(importConfig);
      const r = await axios.post(`${API}/worlds/import`, { config, name: config.name || "Imported World" });
      setCurrentWorld(r.data); fetchWorlds();
      setShowImportDialog(false); setImportConfig("");
      saveToHistory(r.data); autoZoom(r.data.map_width);
    } catch (e) { alert("Failed to import. Check your JSON format."); }
    setLoading(false);
  };

  // ========== EXPORT ==========
  const exportWorld = async (format) => {
    if (!currentWorld) return;
    try {
      const response = await axios.get(`${API}/worlds/${currentWorld.id}/export/${format}`);
      const data = response.data;
      let content, filename, mimeType;
      if (format === "jar") {
        const binaryString = atob(data.data_base64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
        content = bytes; filename = data.filename || `${currentWorld.name.replace(/\s+/g, '_')}_worldgen.jar`; mimeType = "application/java-archive";
      } else if (format === "prefab") {
        content = JSON.stringify(data.data || data, null, 2);
        filename = data.filename || `${currentWorld.name.replace(/\s+/g, '_')}.prefab.json`; mimeType = "application/json";
      } else {
        content = JSON.stringify(data, null, 2);
        filename = `${currentWorld.name.replace(/\s+/g, '_')}_${format}.json`; mimeType = "application/json";
      }
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = filename; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { console.error("Export failed:", e); }
  };

  // ========== AI AUTO-GENERATE ==========
  const autoGenerate = async () => {
    if (!currentWorld || !autoGenPrompt.trim()) return;
    if (isFeatureGated("ai")) { setShowPricingDialog(true); return; }
    setAutoGenLoading(true);
    try {
      const response = await axios.post(`${API}/ai/auto-generate`, { world_id: currentWorld.id, prompt: autoGenPrompt, provider: aiProvider });
      if (response.data.world) {
        const w = response.data.world;
        if (typeof w.created_at === 'string') w.created_at = new Date(w.created_at);
        if (typeof w.updated_at === 'string') w.updated_at = new Date(w.updated_at);
        setShowAutoGenDialog(false); setAutoGenPrompt("");
        requestAnimationFrame(() => { setCurrentWorld(w); saveToHistory(w);
          setAiMessages(prev => [...prev, { role: "assistant", content: `Auto-generated world with ${(w.zones || []).length} zones and ${(w.prefabs || []).length} prefabs.` }]);
        });
      } else { setShowAutoGenDialog(false); setAutoGenPrompt(""); }
    } catch (e) { alert(e.response?.data?.detail || "AI auto-generation failed. Please try again."); }
    setAutoGenLoading(false);
  };

  // ========== 3D PREVIEW ==========
  const load3DPreview = async () => {
    if (!currentWorld) return;
    try { const r = await axios.get(`${API}/worlds/${currentWorld.id}/preview-3d`); setPreview3DData(r.data); setShow3DPreview(true); }
    catch (e) { console.error("Failed to load 3D preview:", e); }
  };

  // ========== COLLABORATION ==========
  const sendWsMessage = (type, data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) wsRef.current.send(JSON.stringify({ type, ...data }));
  };

  const toggleCollab = async () => {
    if (collabEnabled) {
      if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
      setCollabEnabled(false); setWsConnected(false); setCollabCursors({}); setCollabUsers([]);
      if (currentWorld) await axios.post(`${API}/collab/leave`, { world_id: currentWorld.id, user_id: userId, action: "leave" });
    } else {
      if (!currentWorld) return;
      try {
        await axios.post(`${API}/collab/join`, { world_id: currentWorld.id, user_id: userId, action: "join" });
        const ws = new WebSocket(`${WS_URL}/api/ws/collab/${currentWorld.id}/${userId}`);
        ws.onopen = () => setWsConnected(true);
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === "connected" || data.type === "user_joined" || data.type === "user_left") setCollabUsers(data.users || []);
          else if (data.type === "cursor_update") setCollabCursors(prev => ({ ...prev, [data.user_id]: { x: data.x, y: data.y } }));
          else if (data.type === "chat_message") setCollabChat(prev => [...prev, { user: data.user_id, message: data.message }]);
          else if (data.type === "zone_added" && data.zone) setCurrentWorld(prev => prev ? { ...prev, zones: [...prev.zones, data.zone] } : prev);
          else if (data.type === "prefab_added" && data.prefab) setCurrentWorld(prev => prev ? { ...prev, prefabs: [...prev.prefabs, data.prefab] } : prev);
        };
        ws.onclose = () => setWsConnected(false);
        ws.onerror = () => setWsConnected(false);
        wsRef.current = ws; setCollabEnabled(true);
      } catch (e) { console.error("Failed to start collaboration:", e); }
    }
  };

  useEffect(() => { return () => { if (wsRef.current) { wsRef.current.close(); wsRef.current = null; } }; }, []);

  // ========== GALLERY ==========
  const fetchGallery = async () => {
    setGalleryLoading(true);
    try {
      const params = new URLSearchParams({ sort_by: gallerySort, limit: "20" });
      if (gallerySearch) params.set("query", gallerySearch);
      if (galleryFilterZones) params.set("zone_types", galleryFilterZones);
      if (galleryFilterMinRating > 0) params.set("min_rating", String(galleryFilterMinRating));
      if (galleryFilterMapMin) params.set("map_size_min", galleryFilterMapMin);
      if (galleryFilterMapMax) params.set("map_size_max", galleryFilterMapMax);
      if (galleryFollowingOnly) params.set("following_only", "true");
      const r = await axios.get(`${API}/gallery?${params}`);
      setGalleryEntries(r.data.entries || []);
    } catch (e) { console.error("Failed to fetch gallery:", e); }
    setGalleryLoading(false);
  };

  const publishWorld = async () => {
    if (!currentWorld) return;
    try {
      await axios.post(`${API}/gallery/publish`, { world_id: currentWorld.id, description: publishData.description, creator_name: publishData.creator_name || currentUser?.name || "Anonymous", tags: publishData.tags.split(",").map(t => t.trim()).filter(Boolean) });
      setShowPublishDialog(false); setPublishData({ description: "", creator_name: "", tags: "" });
    } catch (e) { alert(e.response?.data?.detail || "Failed to publish"); }
  };

  const downloadFromGallery = async (galleryId) => {
    try {
      const r = await axios.post(`${API}/gallery/${galleryId}/download`);
      if (r.data.world) {
        const w = r.data.world;
        if (typeof w.created_at === 'string') w.created_at = new Date(w.created_at);
        if (typeof w.updated_at === 'string') w.updated_at = new Date(w.updated_at);
        setCurrentWorld(w); saveToHistory(w); setShowGalleryDialog(false);
      }
    } catch (e) { console.error("Failed to download from gallery:", e); }
  };

  // ========== VERSIONS ==========
  const fetchVersions = async () => {
    if (!currentWorld) return;
    try { const r = await axios.get(`${API}/worlds/${currentWorld.id}/versions`); setWorldVersions(r.data.versions || []); }
    catch (e) { console.error("Failed to fetch versions:", e); }
  };

  const createVersion = async () => {
    if (!currentWorld) return;
    try { await axios.post(`${API}/worlds/${currentWorld.id}/versions`); fetchVersions(); }
    catch (e) { console.error("Failed to create version:", e); }
  };

  const restoreVersion = async (versionId) => {
    if (!currentWorld) return;
    try { await axios.post(`${API}/worlds/${currentWorld.id}/versions/${versionId}/restore`); loadWorld(currentWorld.id); setShowVersionDialog(false); }
    catch (e) { console.error("Failed to restore version:", e); }
  };

  const toggleWorldVisibility = async () => {
    if (!currentWorld || !currentUser) return;
    try {
      const newVis = !currentWorld.is_public;
      await axios.put(`${API}/worlds/${currentWorld.id}/visibility?is_public=${newVis}`);
      setCurrentWorld({ ...currentWorld, is_public: newVis });
    } catch (e) { console.error("Failed to update visibility:", e); }
  };

  // ========== REVIEWS ==========
  const fetchReviews = async (galleryId) => {
    try { const r = await axios.get(`${API}/reviews/${galleryId}`); setReviews(r.data.reviews || []); }
    catch (e) { console.error("Failed to fetch reviews:", e); }
  };

  const createReview = async () => {
    if (!currentUser || !selectedGalleryForReview) return;
    try {
      await axios.post(`${API}/reviews`, { gallery_id: selectedGalleryForReview, rating: newReview.rating, comment: newReview.comment });
      fetchReviews(selectedGalleryForReview); setNewReview({ rating: 5, comment: "" });
    } catch (e) { alert(e.response?.data?.detail || "Failed to create review"); }
  };

  // ========== COLLABORATOR MANAGEMENT ==========
  const fetchCollaborators = async () => {
    if (!currentWorld) return;
    try { const r = await axios.get(`${API}/worlds/${currentWorld.id}/collaborators`); setWorldCollaborators(r.data); }
    catch (e) { console.error("Collaborators failed:", e); }
  };

  const addCollaborator = async (userId, role) => {
    if (!currentWorld) return;
    try { await axios.post(`${API}/worlds/${currentWorld.id}/collaborators`, { user_id: userId, role }); fetchCollaborators(); setCollabInviteEmail(""); }
    catch (e) { alert(e.response?.data?.detail || "Failed to add collaborator"); }
  };

  const removeCollaborator = async (userId) => {
    if (!currentWorld) return;
    try { await axios.delete(`${API}/worlds/${currentWorld.id}/collaborators/${userId}`); fetchCollaborators(); }
    catch (e) { alert(e.response?.data?.detail || "Failed to remove collaborator"); }
  };

  const updateCollaboratorRole = async (userId, role) => {
    if (!currentWorld) return;
    try { await axios.put(`${API}/worlds/${currentWorld.id}/collaborators/${userId}`, { role }); fetchCollaborators(); }
    catch (e) { alert(e.response?.data?.detail || "Failed to update role"); }
  };

  // ========== FORKING ==========
  const forkWorld = async (worldId, name) => {
    try { const r = await axios.post(`${API}/worlds/${worldId}/fork`, { name: name || undefined }); fetchWorlds(); return r.data; }
    catch (e) { alert(e.response?.data?.detail || "Fork failed"); }
  };

  const forkFromGallery = async (galleryId, name) => {
    try {
      const r = await axios.post(`${API}/gallery/${galleryId}/fork`, { name: name || undefined });
      fetchWorlds(); if (r.data.world_id) loadWorld(r.data.world_id); setShowGalleryDialog(false); return r.data;
    } catch (e) { alert(e.response?.data?.detail || "Fork failed"); }
  };

  // ========== CUSTOM PREFABS ==========
  const fetchCustomPrefabs = async () => {
    try { const r = await axios.get(`${API}/prefabs/custom`); setCustomPrefabs(r.data.prefabs || []); }
    catch (e) { console.error("Failed to fetch custom prefabs:", e); }
  };

  const createCustomPrefab = async () => {
    if (!newPrefab.name.trim()) return;
    try {
      await axios.post(`${API}/prefabs/custom`, { ...newPrefab, tags: newPrefab.tags.split(",").map(t => t.trim()).filter(Boolean) });
      fetchCustomPrefabs();
      setNewPrefab({ name: "", description: "", icon: "cube", color: "#6B7280", category: "custom", is_public: false, tags: "" });
    } catch (e) { console.error("Failed to create custom prefab:", e); }
  };

  // ========== ANALYTICS ==========
  const fetchAnalytics = async () => {
    try { const r = await axios.get(`${API}/analytics/summary`); setAnalyticsData(r.data); }
    catch (e) { console.error("Failed to fetch analytics:", e); }
  };

  // ========== PROCEDURAL ==========
  const startProceduralPreview = async (template = "adventure") => {
    try {
      const r = await axios.post(`${API}/generate/preview?template=${template}&map_width=32&map_height=32&steps=5`);
      setProceduralSteps(r.data.steps || []); setCurrentPreviewStep(0); setPreviewPlaying(false); setShowProceduralPreview(true);
    } catch (e) { console.error("Failed to start procedural preview:", e); }
  };

  useEffect(() => {
    if (!previewPlaying || !proceduralSteps.length) return;
    const interval = setInterval(() => {
      setCurrentPreviewStep(prev => { if (prev >= proceduralSteps.length - 1) { setPreviewPlaying(false); return prev; } return prev + 1; });
    }, 1500);
    return () => clearInterval(interval);
  }, [previewPlaying, proceduralSteps]);

  // ========== CONTEXT VALUE ==========
  const value = {
    worlds, currentWorld, setCurrentWorld, loading, activeTool, setActiveTool,
    selectedZoneType, setSelectedZoneType, selectedPrefabType, setSelectedPrefabType,
    aiPanelOpen, setAiPanelOpen, aiMessages, aiInput, setAiInput, aiLoading, aiProvider, setAiProvider,
    showNewWorldDialog, setShowNewWorldDialog, newWorldName, setNewWorldName,
    newWorldSeed, setNewWorldSeed, newWorldSize, setNewWorldSize,
    history, historyIndex, undo, redo, saveToHistory,
    selectedElement, setSelectedElement, propertiesOpen, setPropertiesOpen,
    zoom, setZoom, pan, setPan, isPanning, isDragging, autoZoom,
    handleMapMouseDown, handleMapMouseMove, handleMapMouseUp,
    templates, showTemplateDialog, setShowTemplateDialog, selectedTemplate, setSelectedTemplate,
    showImportDialog, setShowImportDialog, importConfig, setImportConfig,
    showAutoGenDialog, setShowAutoGenDialog, autoGenPrompt, setAutoGenPrompt, autoGenLoading,
    show3DPreview, setShow3DPreview, preview3DData,
    collabEnabled, collabUsers, userId, wsConnected, collabCursors, collabChat,
    showGalleryDialog, setShowGalleryDialog, galleryEntries, galleryLoading,
    gallerySearch, setGallerySearch, gallerySort, setGallerySort,
    showPublishDialog, setShowPublishDialog, publishData, setPublishData,
    showCustomPrefabDialog, setShowCustomPrefabDialog, customPrefabs, newPrefab, setNewPrefab,
    showAnalyticsDialog, setShowAnalyticsDialog, analyticsData,
    showProceduralPreview, setShowProceduralPreview, proceduralSteps,
    currentPreviewStep, setCurrentPreviewStep, previewPlaying, setPreviewPlaying,
    showVersionDialog, setShowVersionDialog, worldVersions,
    showReviewDialog, setShowReviewDialog, reviews, newReview, setNewReview,
    selectedGalleryForReview, setSelectedGalleryForReview,
    galleryFilterZones, setGalleryFilterZones, galleryFilterMinRating, setGalleryFilterMinRating,
    galleryFilterMapMin, setGalleryFilterMapMin, galleryFilterMapMax, setGalleryFilterMapMax,
    galleryFollowingOnly, setGalleryFollowingOnly,
    showCollabDialog, setShowCollabDialog, worldCollaborators,
    collabInviteEmail, setCollabInviteEmail, collabInviteRole, setCollabInviteRole,
    fetchWorlds, createWorld, loadWorld, saveWorld, deleteWorld,
    sendAiMessage, fetchTemplates, createFromTemplate,
    importWorld, exportWorld, autoGenerate, load3DPreview,
    toggleCollab, sendWsMessage, fetchGallery, publishWorld,
    downloadFromGallery, fetchCustomPrefabs, createCustomPrefab,
    fetchAnalytics, startProceduralPreview,
    fetchVersions, createVersion, restoreVersion, toggleWorldVisibility,
    fetchReviews, createReview,
    fetchCollaborators, addCollaborator, removeCollaborator, updateCollaboratorRole,
    forkWorld, forkFromGallery,
    updateZoneProperty, updateZoneBiomes, deleteZone,
    updatePrefabProperty, deletePrefab, updateTerrain,
    thumbnails, fetchThumbnail, regenerateThumbnail,
    mobileSidebarOpen, setMobileSidebarOpen, mobileAiPanelOpen, setMobileAiPanelOpen,
    wsRef,
    showInstallDialog, setShowInstallDialog,
    showHowToDialog, setShowHowToDialog,
    pwaInstallable, triggerPwaInstall,
    showShareDialog, setShowShareDialog, shareInfo, fetchShareInfo, toggleShare,
  };

  return <AppInternalContext.Provider value={value}>{children}</AppInternalContext.Provider>;
}

// ========== FACADE: useApp() merges all contexts ==========
export const useApp = () => {
  const auth = useAuth();
  const sub = useSubscription();
  const social = useSocial();
  const internal = useContext(AppInternalContext);
  return { ...auth, ...sub, ...social, ...internal };
};

// ========== COMPOSED PROVIDER ==========
export function AppProvider({ children }) {
  return (
    <AuthProvider>
      <SubscriptionProvider>
        <SocialProvider>
          <AppInternalProvider>
            {children}
          </AppInternalProvider>
        </SocialProvider>
      </SubscriptionProvider>
    </AuthProvider>
  );
}
