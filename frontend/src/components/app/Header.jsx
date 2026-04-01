import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Map, Undo2, Redo2, Users, Box, Globe, BarChart3, History,
  Lock, Unlock, PanelRightOpen, PanelRightClose, LogIn, LogOut,
  UserCircle, Bell
} from "lucide-react";

export function Header() {
  const ctx = useApp();

  return (
    <header className="app-header" data-testid="app-header">
      <div className="header-left">
        <Map className="header-icon" />
        <h1 className="header-title">Hytale World Builder</h1>
      </div>
      <div className="header-center">
        {ctx.currentWorld && (
          <div className="world-info">
            <span className="world-name">{ctx.currentWorld.name}</span>
            <span className="world-seed">Seed: {ctx.currentWorld.seed}</span>
            <Badge variant="outline" className="world-size-badge">
              {ctx.currentWorld.map_width}x{ctx.currentWorld.map_height}
            </Badge>
            {ctx.collabEnabled && (
              <Badge className="collab-badge">
                <Users size={12} />
                {ctx.collabUsers.length} online
              </Badge>
            )}
          </div>
        )}
      </div>
      <div className="header-right">
        {ctx.currentWorld && (
          <>
            <Button variant="ghost" size="icon" onClick={ctx.undo} disabled={ctx.historyIndex <= 0} title="Undo" data-testid="undo-btn">
              <Undo2 size={18} />
            </Button>
            <Button variant="ghost" size="icon" onClick={ctx.redo} disabled={ctx.historyIndex >= ctx.history.length - 1} title="Redo" data-testid="redo-btn">
              <Redo2 size={18} />
            </Button>
            <div className="header-divider" />
            <Button variant={ctx.collabEnabled ? "default" : "ghost"} size="icon" onClick={ctx.toggleCollab} title={ctx.collabEnabled ? `Connected (${ctx.collabUsers.length} users)` : "Start Collaboration"} data-testid="collab-btn">
              <Users size={18} />
              {ctx.wsConnected && <span className="ws-indicator" />}
            </Button>
            <Button variant="ghost" size="icon" onClick={ctx.load3DPreview} title="3D Preview" data-testid="preview-3d-btn">
              <Box size={18} />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => { ctx.setShowGalleryDialog(true); ctx.fetchGallery(); }} title="Community Gallery" data-testid="gallery-btn">
              <Globe size={18} />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => { ctx.setShowAnalyticsDialog(true); ctx.fetchAnalytics(); }} title="Analytics" data-testid="analytics-btn">
              <BarChart3 size={18} />
            </Button>
            {ctx.currentUser && (
              <>
                <Button variant="ghost" size="icon" onClick={() => { ctx.setShowVersionDialog(true); ctx.fetchVersions(); }} title="Version History" data-testid="version-history-btn">
                  <History size={18} />
                </Button>
                <Button variant="ghost" size="icon" onClick={ctx.toggleWorldVisibility} title={ctx.currentWorld?.is_public ? "Make Private" : "Make Public"} data-testid="visibility-toggle-btn">
                  {ctx.currentWorld?.is_public ? <Unlock size={18} /> : <Lock size={18} />}
                </Button>
              </>
            )}
            <div className="header-divider" />
          </>
        )}
        <Button variant="ghost" size="sm" onClick={() => ctx.setAiPanelOpen(!ctx.aiPanelOpen)} data-testid="toggle-ai-panel">
          {ctx.aiPanelOpen ? <PanelRightClose size={18} /> : <PanelRightOpen size={18} />}
        </Button>
        <div className="header-divider" />
        {/* Notifications */}
        {ctx.currentUser && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => { ctx.setShowNotifications(!ctx.showNotifications); ctx.fetchNotifications(); }}
            title="Notifications"
            data-testid="notifications-btn"
            className="notification-bell"
          >
            <Bell size={18} />
            {ctx.unreadCount > 0 && <span className="notification-badge">{ctx.unreadCount}</span>}
          </Button>
        )}
        {/* Auth */}
        {ctx.currentUser ? (
          <div className="user-menu">
            <Button variant="ghost" size="sm" onClick={() => { ctx.fetchProfile(ctx.currentUser.id); ctx.setShowProfileDialog(true); }} className="user-btn" data-testid="profile-btn">
              <UserCircle size={18} />
              <span className="user-name">{ctx.currentUser.name}</span>
            </Button>
            <Button variant="ghost" size="icon" onClick={ctx.handleLogout} title="Logout" data-testid="logout-btn">
              <LogOut size={18} />
            </Button>
          </div>
        ) : (
          <Button variant="outline" size="sm" onClick={() => { ctx.setShowAuthDialog(true); ctx.setAuthMode("login"); }} data-testid="login-btn">
            <LogIn size={16} /> Sign In
          </Button>
        )}
      </div>
    </header>
  );
}
