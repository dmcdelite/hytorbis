import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import axios from "axios";
import { API, WS_URL } from "@/config";

axios.defaults.withCredentials = true;

const AppContext = createContext(null);
export const useApp = () => useContext(AppContext);

export function AppProvider({ children }) {
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

  // Auth
  const [currentUser, setCurrentUser] = useState(null);
  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ email: "", password: "", name: "" });
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");

  // Profile
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [profileData, setProfileData] = useState(null);
  const [editProfile, setEditProfile] = useState({ name: "", bio: "" });

  // Versions
  const [showVersionDialog, setShowVersionDialog] = useState(false);
  const [worldVersions, setWorldVersions] = useState([]);

  // Reviews
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviews, setReviews] = useState([]);
  const [newReview, setNewReview] = useState({ rating: 5, comment: "" });
  const [selectedGalleryForReview, setSelectedGalleryForReview] = useState(null);

  // Social
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);

  // Enhanced Social
  const [showUserSearchDialog, setShowUserSearchDialog] = useState(false);
  const [userSearchQuery, setUserSearchQuery] = useState("");
  const [userSearchResults, setUserSearchResults] = useState([]);
  const [suggestedUsers, setSuggestedUsers] = useState([]);
  const [showActivityFeed, setShowActivityFeed] = useState(false);
  const [activityFeed, setActivityFeed] = useState([]);

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

  // Thumbnails cache
  const [thumbnails, setThumbnails] = useState({});

  // Mobile sidebar state
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [mobileAiPanelOpen, setMobileAiPanelOpen] = useState(false);

  // Subscription
  const [subscription, setSubscription] = useState({ plan: "free", limits: null });
  const [showPricingDialog, setShowPricingDialog] = useState(false);
  const [showSubscriptionDialog, setShowSubscriptionDialog] = useState(false);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  // Notification WebSocket ref
  const notifWsRef = useRef(null);

  // ========== INIT ==========
  useEffect(() => {
    checkAuth();
  }, []);

  // When user changes, fetch subscription + worlds
  useEffect(() => {
    if (currentUser) {
      fetchWorlds();
      fetchTemplates();
      fetchCustomPrefabs();
      fetchSubscriptionStatus();
    }
  }, [currentUser]);

  // ========== THUMBNAILS ==========
  const fetchThumbnail = async (worldId) => {
    if (thumbnails[worldId]) return;
    try {
      const response = await axios.get(`${API}/worlds/${worldId}/thumbnail`);
      if (response.data.thumbnail) {
        setThumbnails(prev => ({ ...prev, [worldId]: response.data.thumbnail }));
      }
    } catch (e) { /* ignore */ }
  };

  const regenerateThumbnail = async (worldId) => {
    try {
      const response = await axios.post(`${API}/worlds/${worldId}/thumbnail`);
      if (response.data.thumbnail) {
        setThumbnails(prev => ({ ...prev, [worldId]: response.data.thumbnail }));
      }
    } catch (e) { /* ignore */ }
  };

  // ========== AUTH ==========
  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setCurrentUser(response.data);
    } catch (e) { setCurrentUser(null); }
  };

  const handleLogin = async () => {
    setAuthLoading(true); setAuthError("");
    try {
      const response = await axios.post(`${API}/auth/login`, { email: authForm.email, password: authForm.password });
      setCurrentUser(response.data);
      setShowAuthDialog(false);
      setAuthForm({ email: "", password: "", name: "" });
    } catch (e) { setAuthError(e.response?.data?.detail || "Login failed"); }
    setAuthLoading(false);
  };

  const handleRegister = async () => {
    setAuthLoading(true); setAuthError("");
    try {
      const response = await axios.post(`${API}/auth/register`, { email: authForm.email, password: authForm.password, name: authForm.name });
      setCurrentUser(response.data);
      setShowAuthDialog(false);
      setAuthForm({ email: "", password: "", name: "" });
    } catch (e) { setAuthError(e.response?.data?.detail || "Registration failed"); }
    setAuthLoading(false);
  };

  const handleLogout = async () => {
    try { await axios.post(`${API}/auth/logout`); } catch (e) {}
    setCurrentUser(null);
    setSubscription({ plan: "free", limits: null });
  };

  // ========== SUBSCRIPTION ==========
  const fetchSubscriptionStatus = async () => {
    try {
      const response = await axios.get(`${API}/subscription/status`);
      setSubscription(response.data);
    } catch (e) { setSubscription({ plan: "free", limits: null }); }
  };

  const startCheckout = async (planId) => {
    setCheckoutLoading(true);
    try {
      const response = await axios.post(`${API}/subscription/checkout/stripe`, {
        plan_id: planId,
        origin_url: window.location.origin,
      });
      if (response.data.url) {
        window.location.href = response.data.url;
      }
    } catch (e) {
      alert(e.response?.data?.detail || "Failed to start checkout");
    }
    setCheckoutLoading(false);
  };

  const verifyCheckout = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/subscription/checkout/status/${sessionId}`);
      if (response.data.status === "paid") {
        await fetchSubscriptionStatus();
        return "paid";
      }
      return response.data.status;
    } catch (e) { return "error"; }
  };

  const isFeatureGated = (feature) => {
    const plan = subscription?.plan || "free";
    const gateMap = {
      ai: plan === "free",
      collab: plan === "free",
      analytics: plan === "free" || plan === "creator",
      version_history: plan === "free",
    };
    return gateMap[feature] || false;
  };

  // PayPal
  const createPaypalOrder = async (planId) => {
    try {
      const response = await axios.post(`${API}/subscription/checkout/paypal`, {
        plan_id: planId,
        origin_url: window.location.origin,
      });
      return response.data.order_id;
    } catch (e) {
      throw new Error(e.response?.data?.detail || "Failed to create PayPal order");
    }
  };

  const capturePaypalOrder = async (orderId) => {
    try {
      const response = await axios.post(`${API}/subscription/paypal/capture/${orderId}`);
      if (response.data.status === "paid") {
        await fetchSubscriptionStatus();
        return "paid";
      }
      return response.data.status;
    } catch (e) { return "error"; }
  };

  const fetchPaymentHistory = async () => {
    try {
      const response = await axios.get(`${API}/subscription/history`);
      setPaymentHistory(response.data.transactions || []);
    } catch (e) { setPaymentHistory([]); }
  };

  const cancelSubscription = async () => {
    try {
      const response = await axios.post(`${API}/subscription/cancel`);
      if (response.data.status === "cancelled") {
        await fetchSubscriptionStatus();
        return true;
      }
      return false;
    } catch (e) {
      alert(e.response?.data?.detail || "Failed to cancel");
      return false;
    }
  };

  // ========== PROFILE ==========
  const fetchProfile = async (uid) => {
    try {
      const response = await axios.get(`${API}/users/${uid}/profile`);
      setProfileData(response.data);
      setEditProfile({ name: response.data.name || "", bio: response.data.bio || "" });
    } catch (e) { console.error("Failed to fetch profile:", e); }
  };

  const updateProfile = async () => {
    if (!currentUser) return;
    try {
      await axios.put(`${API}/users/profile`, editProfile);
      setCurrentUser({ ...currentUser, ...editProfile });
      setShowProfileDialog(false);
    } catch (e) { console.error("Failed to update profile:", e); }
  };

  // ========== SOCIAL ==========
  const fetchNotifications = async () => {
    if (!currentUser) return;
    try {
      const response = await axios.get(`${API}/notifications`);
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
    } catch (e) { console.error("Failed to fetch notifications:", e); }
  };

  const markAllRead = async () => {
    try {
      await axios.post(`${API}/notifications/read-all`);
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (e) { console.error("Failed to mark notifications:", e); }
  };

  const followUser = async (uid) => {
    try {
      await axios.post(`${API}/users/${uid}/follow`);
      fetchProfile(uid);
    } catch (e) { alert(e.response?.data?.detail || "Failed to follow"); }
  };

  const unfollowUser = async (uid) => {
    try {
      await axios.post(`${API}/users/${uid}/unfollow`);
      fetchProfile(uid);
    } catch (e) { alert(e.response?.data?.detail || "Failed to unfollow"); }
  };

  useEffect(() => {
    if (currentUser) {
      fetchNotifications();
      connectNotificationWs();
    }
    return () => {
      if (notifWsRef.current) { notifWsRef.current.close(); notifWsRef.current = null; }
    };
  }, [currentUser]);

  // Real-time notification WebSocket
  const connectNotificationWs = () => {
    if (!currentUser || notifWsRef.current) return;
    try {
      const ws = new WebSocket(`${WS_URL}/api/ws/notifications/${currentUser.id}`);
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "notification") {
          setNotifications(prev => [data.data, ...prev]);
          setUnreadCount(prev => prev + 1);
        }
      };
      ws.onclose = () => { notifWsRef.current = null; };
      // Ping every 30s to keep alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "ping" }));
        else clearInterval(pingInterval);
      }, 30000);
      notifWsRef.current = ws;
    } catch (e) { console.error("Notification WS failed:", e); }
  };

  // ========== ENHANCED SOCIAL ==========
  const searchUsers = async (q) => {
    if (!q || q.length < 2) { setUserSearchResults([]); return; }
    try {
      const response = await axios.get(`${API}/users/search?q=${encodeURIComponent(q)}`);
      setUserSearchResults(response.data.users || []);
    } catch (e) { console.error("Search failed:", e); }
  };

  const fetchSuggestedUsers = async () => {
    try {
      const response = await axios.get(`${API}/users/suggested`);
      setSuggestedUsers(response.data.suggestions || []);
    } catch (e) { console.error("Suggested users failed:", e); }
  };

  const fetchActivityFeed = async () => {
    try {
      const response = await axios.get(`${API}/activity-feed`);
      setActivityFeed(response.data.activities || []);
    } catch (e) { console.error("Activity feed failed:", e); }
  };

  // ========== COLLABORATOR MANAGEMENT ==========
  const fetchCollaborators = async () => {
    if (!currentWorld) return;
    try {
      const response = await axios.get(`${API}/worlds/${currentWorld.id}/collaborators`);
      setWorldCollaborators(response.data);
    } catch (e) { console.error("Collaborators failed:", e); }
  };

  const addCollaborator = async (userId, role) => {
    if (!currentWorld) return;
    try {
      await axios.post(`${API}/worlds/${currentWorld.id}/collaborators`, { user_id: userId, role });
      fetchCollaborators();
      setCollabInviteEmail("");
    } catch (e) { alert(e.response?.data?.detail || "Failed to add collaborator"); }
  };

  const removeCollaborator = async (userId) => {
    if (!currentWorld) return;
    try {
      await axios.delete(`${API}/worlds/${currentWorld.id}/collaborators/${userId}`);
      fetchCollaborators();
    } catch (e) { alert(e.response?.data?.detail || "Failed to remove collaborator"); }
  };

  const updateCollaboratorRole = async (userId, role) => {
    if (!currentWorld) return;
    try {
      await axios.put(`${API}/worlds/${currentWorld.id}/collaborators/${userId}`, { role });
      fetchCollaborators();
    } catch (e) { alert(e.response?.data?.detail || "Failed to update role"); }
  };

  // ========== WORLD FORKING ==========
  const forkWorld = async (worldId, name) => {
    try {
      const response = await axios.post(`${API}/worlds/${worldId}/fork`, { name: name || undefined });
      fetchWorlds();
      return response.data;
    } catch (e) { alert(e.response?.data?.detail || "Fork failed"); }
  };

  const forkFromGallery = async (galleryId, name) => {
    try {
      const response = await axios.post(`${API}/gallery/${galleryId}/fork`, { name: name || undefined });
      fetchWorlds();
      if (response.data.world_id) loadWorld(response.data.world_id);
      setShowGalleryDialog(false);
      return response.data;
    } catch (e) { alert(e.response?.data?.detail || "Fork failed"); }
  };

  // ========== VERSIONS ==========
  const fetchVersions = async () => {
    if (!currentWorld) return;
    try {
      const response = await axios.get(`${API}/worlds/${currentWorld.id}/versions`);
      setWorldVersions(response.data.versions || []);
    } catch (e) { console.error("Failed to fetch versions:", e); }
  };

  const createVersion = async () => {
    if (!currentWorld) return;
    try { await axios.post(`${API}/worlds/${currentWorld.id}/versions`); fetchVersions(); }
    catch (e) { console.error("Failed to create version:", e); }
  };

  const restoreVersion = async (versionId) => {
    if (!currentWorld) return;
    try {
      await axios.post(`${API}/worlds/${currentWorld.id}/versions/${versionId}/restore`);
      loadWorld(currentWorld.id);
      setShowVersionDialog(false);
    } catch (e) { console.error("Failed to restore version:", e); }
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
    try {
      const response = await axios.get(`${API}/reviews/${galleryId}`);
      setReviews(response.data.reviews || []);
    } catch (e) { console.error("Failed to fetch reviews:", e); }
  };

  const createReview = async () => {
    if (!currentUser || !selectedGalleryForReview) return;
    try {
      await axios.post(`${API}/reviews`, { gallery_id: selectedGalleryForReview, rating: newReview.rating, comment: newReview.comment });
      fetchReviews(selectedGalleryForReview);
      setNewReview({ rating: 5, comment: "" });
    } catch (e) { alert(e.response?.data?.detail || "Failed to create review"); }
  };

  // ========== WORLD CRUD ==========
  const fetchWorlds = async () => {
    try {
      const response = await axios.get(`${API}/worlds`);
      const data = Array.isArray(response.data) ? response.data : response.data.worlds || [];
      setWorlds(data);
    } catch (e) { console.error("Failed to fetch worlds:", e); }
  };

  const createWorld = async () => {
    if (!newWorldName.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post(`${API}/worlds`, { name: newWorldName, seed: newWorldSeed || null, map_width: newWorldSize.width, map_height: newWorldSize.height });
      setCurrentWorld(response.data);
      fetchWorlds();
      setShowNewWorldDialog(false);
      setNewWorldName(""); setNewWorldSeed("");
      saveToHistory(response.data);
      autoZoom(response.data.map_width);
    } catch (e) { console.error("Failed to create world:", e); }
    setLoading(false);
  };

  const loadWorld = async (worldId) => {
    try {
      const response = await axios.get(`${API}/worlds/${worldId}`);
      setCurrentWorld(response.data);
      setHistory([response.data]);
      setHistoryIndex(0);
      autoZoom(response.data.map_width);
    } catch (e) { console.error("Failed to load world:", e); }
  };

  const saveWorld = async () => {
    if (!currentWorld) return;
    setLoading(true);
    try {
      await axios.put(`${API}/worlds/${currentWorld.id}`, {
        name: currentWorld.name, terrain: currentWorld.terrain,
        zones: currentWorld.zones, prefabs: currentWorld.prefabs,
        ai_provider: aiProvider
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
    if (activeTool === "pan") {
      setIsPanning(true);
      lastPanPos.current = { x: e.clientX, y: e.clientY };
      return;
    }
    if (activeTool === "zone") {
      setIsDragging(true);
      addZone(x, y);
    } else if (activeTool === "prefab") {
      addPrefab(x, y);
    } else if (activeTool === "select") {
      selectElement(x, y);
    }
  };

  const handleMapMouseMove = (x, y, e) => {
    if (isPanning) {
      const dx = e.clientX - lastPanPos.current.x;
      const dy = e.clientY - lastPanPos.current.y;
      setPan(p => ({ x: p.x + dx, y: p.y + dy }));
      lastPanPos.current = { x: e.clientX, y: e.clientY };
      return;
    }
    if (isDragging && activeTool === "zone") addZone(x, y);
    if (collabEnabled && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "cursor_move", x, y }));
    }
  };

  const handleMapMouseUp = () => {
    if (isDragging && currentWorld) saveToHistory(currentWorld);
    setIsDragging(false);
    setIsPanning(false);
  };

  const addZone = (x, y) => {
    if (!currentWorld) return;
    const existingIndex = currentWorld.zones.findIndex(z => z.x === x && z.y === y);
    let updatedZones;
    if (existingIndex >= 0) {
      updatedZones = [...currentWorld.zones];
      updatedZones[existingIndex] = { ...updatedZones[existingIndex], type: selectedZoneType };
    } else {
      updatedZones = [...currentWorld.zones, { id: `zone-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`, type: selectedZoneType, x, y, difficulty: 1, biomes: [] }];
    }
    const updatedWorld = { ...currentWorld, zones: updatedZones };
    setCurrentWorld(updatedWorld);
    if (!isDragging) saveToHistory(updatedWorld);
    if (collabEnabled) sendWsMessage("zone_add", { zone: updatedZones[updatedZones.length - 1] });
  };

  const addPrefab = (x, y) => {
    if (!currentWorld) return;
    const newP = { id: `prefab-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`, type: selectedPrefabType, x, y, rotation: 0, scale: 1 };
    const updatedWorld = { ...currentWorld, prefabs: [...currentWorld.prefabs, newP] };
    setCurrentWorld(updatedWorld);
    saveToHistory(updatedWorld);
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
    const updatedZones = currentWorld.zones.map(z => z.id === zoneId ? { ...z, [key]: value } : z);
    const updatedWorld = { ...currentWorld, zones: updatedZones };
    setCurrentWorld(updatedWorld);
    saveToHistory(updatedWorld);
  };

  const updateZoneBiomes = (zoneId, biomes) => {
    if (!currentWorld) return;
    const updatedZones = currentWorld.zones.map(z => z.id === zoneId ? { ...z, biomes } : z);
    const updatedWorld = { ...currentWorld, zones: updatedZones };
    setCurrentWorld(updatedWorld);
    saveToHistory(updatedWorld);
  };

  const deleteZone = () => {
    if (!currentWorld || !selectedElement || selectedElement.type !== "zone") return;
    const updatedWorld = { ...currentWorld, zones: currentWorld.zones.filter(z => z.id !== selectedElement.data.id) };
    setCurrentWorld(updatedWorld);
    saveToHistory(updatedWorld);
    setSelectedElement(null); setPropertiesOpen(false);
  };

  const updatePrefabProperty = (prefabId, key, value) => {
    if (!currentWorld) return;
    const updatedPrefabs = currentWorld.prefabs.map(p => p.id === prefabId ? { ...p, [key]: value } : p);
    const updatedWorld = { ...currentWorld, prefabs: updatedPrefabs };
    setCurrentWorld(updatedWorld);
    saveToHistory(updatedWorld);
  };

  const deletePrefab = () => {
    if (!currentWorld || !selectedElement || selectedElement.type !== "prefab") return;
    const updatedWorld = { ...currentWorld, prefabs: currentWorld.prefabs.filter(p => p.id !== selectedElement.data.id) };
    setCurrentWorld(updatedWorld);
    saveToHistory(updatedWorld);
    setSelectedElement(null); setPropertiesOpen(false);
  };

  const updateTerrain = (key, value) => {
    if (!currentWorld) return;
    const updatedTerrain = { ...(currentWorld.terrain || {}), [key]: value };
    const updatedWorld = { ...currentWorld, terrain: updatedTerrain };
    setCurrentWorld(updatedWorld);
    saveToHistory(updatedWorld);
  };

  // ========== AI ==========
  const sendAiMessage = async () => {
    if (!currentWorld || !aiInput.trim()) return;
    if (isFeatureGated("ai")) { setShowPricingDialog(true); return; }
    const userMsg = { role: "user", content: aiInput };
    setAiMessages(prev => [...prev, userMsg]);
    setAiInput(""); setAiLoading(true);
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
          setCurrentWorld(updatedWorld);
          saveToHistory(updatedWorld);
        }
      }
    } catch (e) {
      setAiMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]);
    }
    setAiLoading(false);
  };

  // ========== TEMPLATES ==========
  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`);
      setTemplates(response.data.templates || []);
    } catch (e) { console.error("Failed to fetch templates:", e); }
  };

  const createFromTemplate = async () => {
    if (!selectedTemplate || !newWorldName.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post(`${API}/worlds/from-template`, { name: newWorldName, template: selectedTemplate, map_width: newWorldSize.width, map_height: newWorldSize.height });
      setCurrentWorld(response.data);
      fetchWorlds();
      setShowTemplateDialog(false);
      setNewWorldName(""); setSelectedTemplate(null);
      saveToHistory(response.data);
      autoZoom(response.data.map_width);
    } catch (e) { console.error("Failed to create from template:", e); }
    setLoading(false);
  };

  // ========== IMPORT ==========
  const importWorld = async () => {
    if (!importConfig.trim()) return;
    setLoading(true);
    try {
      const config = JSON.parse(importConfig);
      const response = await axios.post(`${API}/worlds/import`, { config, name: config.name || "Imported World" });
      setCurrentWorld(response.data);
      fetchWorlds();
      setShowImportDialog(false);
      setImportConfig("");
      saveToHistory(response.data);
      autoZoom(response.data.map_width);
    } catch (e) {
      alert("Failed to import. Check your JSON format.");
    }
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
        content = bytes;
        filename = data.filename || `${currentWorld.name.replace(/\s+/g, '_')}_worldgen.jar`;
        mimeType = "application/java-archive";
      } else if (format === "prefab") {
        content = JSON.stringify(data.data || data, null, 2);
        filename = data.filename || `${currentWorld.name.replace(/\s+/g, '_')}.prefab.json`;
        mimeType = "application/json";
      } else {
        content = JSON.stringify(data, null, 2);
        filename = `${currentWorld.name.replace(/\s+/g, '_')}_${format}.json`;
        mimeType = "application/json";
      }
      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename; a.click();
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
        setShowAutoGenDialog(false);
        setAutoGenPrompt("");
        // Defer heavy grid re-render to next frame to avoid INP lag
        requestAnimationFrame(() => {
          setCurrentWorld(w);
          saveToHistory(w);
          setAiMessages(prev => [...prev, { role: "assistant", content: `Auto-generated world with ${(w.zones || []).length} zones and ${(w.prefabs || []).length} prefabs.` }]);
        });
      } else {
        setShowAutoGenDialog(false);
        setAutoGenPrompt("");
      }
    } catch (e) {
      alert(e.response?.data?.detail || "AI auto-generation failed. Please try again.");
    }
    setAutoGenLoading(false);
  };

  // ========== 3D PREVIEW ==========
  const load3DPreview = async () => {
    if (!currentWorld) return;
    try {
      const response = await axios.get(`${API}/worlds/${currentWorld.id}/preview-3d`);
      setPreview3DData(response.data);
      setShow3DPreview(true);
    } catch (e) { console.error("Failed to load 3D preview:", e); }
  };

  // ========== COLLABORATION ==========
  const sendWsMessage = (type, data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type, ...data }));
    }
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
        ws.onopen = () => { setWsConnected(true); };
        ws.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.type === "connected" || data.type === "user_joined" || data.type === "user_left") setCollabUsers(data.users || []);
          else if (data.type === "cursor_update") setCollabCursors(prev => ({ ...prev, [data.user_id]: { x: data.x, y: data.y } }));
          else if (data.type === "chat_message") setCollabChat(prev => [...prev, { user: data.user_id, message: data.message }]);
          else if (data.type === "zone_added" && data.zone) setCurrentWorld(prev => prev ? { ...prev, zones: [...prev.zones, data.zone] } : prev);
          else if (data.type === "prefab_added" && data.prefab) setCurrentWorld(prev => prev ? { ...prev, prefabs: [...prev.prefabs, data.prefab] } : prev);
        };
        ws.onclose = () => { setWsConnected(false); };
        ws.onerror = () => { setWsConnected(false); };
        wsRef.current = ws;
        setCollabEnabled(true);
      } catch (e) { console.error("Failed to start collaboration:", e); }
    }
  };

  useEffect(() => {
    return () => { if (wsRef.current) { wsRef.current.close(); wsRef.current = null; } };
  }, []);

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
      const response = await axios.get(`${API}/gallery?${params}`);
      setGalleryEntries(response.data.entries || []);
    } catch (e) { console.error("Failed to fetch gallery:", e); }
    setGalleryLoading(false);
  };

  const publishWorld = async () => {
    if (!currentWorld) return;
    try {
      await axios.post(`${API}/gallery/publish`, { world_id: currentWorld.id, description: publishData.description, creator_name: publishData.creator_name || currentUser?.name || "Anonymous", tags: publishData.tags.split(",").map(t => t.trim()).filter(Boolean) });
      setShowPublishDialog(false);
      setPublishData({ description: "", creator_name: "", tags: "" });
    } catch (e) { alert(e.response?.data?.detail || "Failed to publish"); }
  };

  const downloadFromGallery = async (galleryId) => {
    try {
      const response = await axios.post(`${API}/gallery/${galleryId}/download`);
      if (response.data.world) {
        const w = response.data.world;
        if (typeof w.created_at === 'string') w.created_at = new Date(w.created_at);
        if (typeof w.updated_at === 'string') w.updated_at = new Date(w.updated_at);
        setCurrentWorld(w);
        saveToHistory(w);
        setShowGalleryDialog(false);
      }
    } catch (e) { console.error("Failed to download from gallery:", e); }
  };

  // ========== CUSTOM PREFABS ==========
  const fetchCustomPrefabs = async () => {
    try {
      const response = await axios.get(`${API}/prefabs/custom`);
      setCustomPrefabs(response.data.prefabs || []);
    } catch (e) { console.error("Failed to fetch custom prefabs:", e); }
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
    try {
      const response = await axios.get(`${API}/analytics/summary`);
      setAnalyticsData(response.data);
    } catch (e) { console.error("Failed to fetch analytics:", e); }
  };

  // ========== PROCEDURAL PREVIEW ==========
  const startProceduralPreview = async (template = "adventure") => {
    try {
      const response = await axios.post(`${API}/generate/preview?template=${template}&map_width=32&map_height=32&steps=5`);
      setProceduralSteps(response.data.steps || []);
      setCurrentPreviewStep(0);
      setPreviewPlaying(false);
      setShowProceduralPreview(true);
    } catch (e) { console.error("Failed to start procedural preview:", e); }
  };

  useEffect(() => {
    if (!previewPlaying || !proceduralSteps.length) return;
    const interval = setInterval(() => {
      setCurrentPreviewStep(prev => {
        if (prev >= proceduralSteps.length - 1) { setPreviewPlaying(false); return prev; }
        return prev + 1;
      });
    }, 1500);
    return () => clearInterval(interval);
  }, [previewPlaying, proceduralSteps]);

  // ========== CONTEXT VALUE ==========
  const value = {
    // Core
    worlds, currentWorld, setCurrentWorld, loading, activeTool, setActiveTool,
    selectedZoneType, setSelectedZoneType, selectedPrefabType, setSelectedPrefabType,
    aiPanelOpen, setAiPanelOpen, aiMessages, aiInput, setAiInput, aiLoading, aiProvider, setAiProvider,
    showNewWorldDialog, setShowNewWorldDialog, newWorldName, setNewWorldName,
    newWorldSeed, setNewWorldSeed, newWorldSize, setNewWorldSize,
    // History
    history, historyIndex, undo, redo, saveToHistory,
    // Properties
    selectedElement, setSelectedElement, propertiesOpen, setPropertiesOpen,
    // Map
    zoom, setZoom, pan, setPan, isPanning, isDragging, autoZoom,
    handleMapMouseDown, handleMapMouseMove, handleMapMouseUp,
    // Templates
    templates, showTemplateDialog, setShowTemplateDialog, selectedTemplate, setSelectedTemplate,
    // Import
    showImportDialog, setShowImportDialog, importConfig, setImportConfig,
    // AutoGen
    showAutoGenDialog, setShowAutoGenDialog, autoGenPrompt, setAutoGenPrompt, autoGenLoading,
    // 3D
    show3DPreview, setShow3DPreview, preview3DData,
    // Collab
    collabEnabled, collabUsers, userId, wsConnected, collabCursors, collabChat,
    // Gallery
    showGalleryDialog, setShowGalleryDialog, galleryEntries, galleryLoading,
    gallerySearch, setGallerySearch, gallerySort, setGallerySort,
    showPublishDialog, setShowPublishDialog, publishData, setPublishData,
    // Custom Prefabs
    showCustomPrefabDialog, setShowCustomPrefabDialog, customPrefabs, newPrefab, setNewPrefab,
    // Analytics
    showAnalyticsDialog, setShowAnalyticsDialog, analyticsData,
    // Procedural
    showProceduralPreview, setShowProceduralPreview, proceduralSteps,
    currentPreviewStep, setCurrentPreviewStep, previewPlaying, setPreviewPlaying,
    // Auth
    currentUser, showAuthDialog, setShowAuthDialog, authMode, setAuthMode,
    authForm, setAuthForm, authLoading, authError, setAuthError,
    // Profile
    showProfileDialog, setShowProfileDialog, profileData, editProfile, setEditProfile,
    // Versions
    showVersionDialog, setShowVersionDialog, worldVersions,
    // Reviews
    showReviewDialog, setShowReviewDialog, reviews, newReview, setNewReview,
    selectedGalleryForReview, setSelectedGalleryForReview,
    // Social
    notifications, unreadCount, showNotifications, setShowNotifications,
    // Enhanced Social
    showUserSearchDialog, setShowUserSearchDialog, userSearchQuery, setUserSearchQuery,
    userSearchResults, suggestedUsers, showActivityFeed, setShowActivityFeed, activityFeed,
    // Gallery filters
    galleryFilterZones, setGalleryFilterZones, galleryFilterMinRating, setGalleryFilterMinRating,
    galleryFilterMapMin, setGalleryFilterMapMin, galleryFilterMapMax, setGalleryFilterMapMax,
    galleryFollowingOnly, setGalleryFollowingOnly,
    // Collaborators
    showCollabDialog, setShowCollabDialog, worldCollaborators,
    collabInviteEmail, setCollabInviteEmail, collabInviteRole, setCollabInviteRole,
    // Functions
    fetchWorlds, createWorld, loadWorld, saveWorld, deleteWorld,
    sendAiMessage, fetchTemplates, createFromTemplate,
    importWorld, exportWorld, autoGenerate, load3DPreview,
    toggleCollab, sendWsMessage, fetchGallery, publishWorld,
    downloadFromGallery, fetchCustomPrefabs, createCustomPrefab,
    fetchAnalytics, startProceduralPreview,
    handleLogin, handleRegister, handleLogout, checkAuth,
    fetchProfile, updateProfile,
    fetchVersions, createVersion, restoreVersion, toggleWorldVisibility,
    fetchReviews, createReview,
    fetchNotifications, markAllRead, followUser, unfollowUser,
    searchUsers, fetchSuggestedUsers, fetchActivityFeed,
    fetchCollaborators, addCollaborator, removeCollaborator, updateCollaboratorRole,
    forkWorld, forkFromGallery,
    updateZoneProperty, updateZoneBiomes, deleteZone,
    updatePrefabProperty, deletePrefab, updateTerrain,
    thumbnails, fetchThumbnail, regenerateThumbnail,
    mobileSidebarOpen, setMobileSidebarOpen, mobileAiPanelOpen, setMobileAiPanelOpen,
    wsRef,
    // Subscription
    subscription, showPricingDialog, setShowPricingDialog, checkoutLoading,
    showSubscriptionDialog, setShowSubscriptionDialog, paymentHistory,
    fetchSubscriptionStatus, startCheckout, verifyCheckout, isFeatureGated,
    createPaypalOrder, capturePaypalOrder,
    fetchPaymentHistory, cancelSubscription,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
