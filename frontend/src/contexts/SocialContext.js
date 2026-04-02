import { createContext, useContext, useState, useEffect, useRef } from "react";
import axios from "axios";
import { API, WS_URL } from "@/config";
import { useAuth } from "./AuthContext";

const SocialContext = createContext(null);
export const useSocial = () => useContext(SocialContext);

export function SocialProvider({ children }) {
  const { currentUser, setCurrentUser } = useAuth();

  // Profile
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [profileData, setProfileData] = useState(null);
  const [editProfile, setEditProfile] = useState({ name: "", bio: "" });

  // Notifications
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);

  // User Search
  const [showUserSearchDialog, setShowUserSearchDialog] = useState(false);
  const [userSearchQuery, setUserSearchQuery] = useState("");
  const [userSearchResults, setUserSearchResults] = useState([]);
  const [suggestedUsers, setSuggestedUsers] = useState([]);

  // Activity Feed
  const [showActivityFeed, setShowActivityFeed] = useState(false);
  const [activityFeed, setActivityFeed] = useState([]);

  const notifWsRef = useRef(null);

  // Profile
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

  // Notifications
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

  // Social
  const followUser = async (uid) => {
    try { await axios.post(`${API}/users/${uid}/follow`); fetchProfile(uid); }
    catch (e) { alert(e.response?.data?.detail || "Failed to follow"); }
  };

  const unfollowUser = async (uid) => {
    try { await axios.post(`${API}/users/${uid}/unfollow`); fetchProfile(uid); }
    catch (e) { alert(e.response?.data?.detail || "Failed to unfollow"); }
  };

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

  // Notification WebSocket
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
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify({ type: "ping" }));
        else clearInterval(pingInterval);
      }, 30000);
      notifWsRef.current = ws;
    } catch (e) { console.error("Notification WS failed:", e); }
  };

  useEffect(() => {
    if (currentUser) { fetchNotifications(); connectNotificationWs(); }
    return () => { if (notifWsRef.current) { notifWsRef.current.close(); notifWsRef.current = null; } };
  }, [currentUser]);

  const value = {
    showProfileDialog, setShowProfileDialog, profileData, editProfile, setEditProfile,
    fetchProfile, updateProfile,
    notifications, unreadCount, showNotifications, setShowNotifications,
    fetchNotifications, markAllRead, followUser, unfollowUser,
    showUserSearchDialog, setShowUserSearchDialog, userSearchQuery, setUserSearchQuery,
    userSearchResults, suggestedUsers, showActivityFeed, setShowActivityFeed, activityFeed,
    searchUsers, fetchSuggestedUsers, fetchActivityFeed,
  };

  return <SocialContext.Provider value={value}>{children}</SocialContext.Provider>;
}
