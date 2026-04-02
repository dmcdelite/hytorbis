import { useState, useEffect, useRef } from "react";
import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { MAP_SIZE_PRESETS, TEMPLATE_ICONS } from "@/config";
import {
  Plus, Wand2, Loader2, FileJson, Upload, Download, ThumbsUp, Search, Tag,
  TrendingUp, Activity, Eye, Star, History, Lock, Unlock, UserCircle,
  LogIn, User, Save, Send, RefreshCw, Play, Pause, SkipForward, Package, Box, Edit3, Bell,
  GitFork, UserPlus, UserMinus, Filter, X, Trash2, Shield, Pencil, Users, Camera
} from "lucide-react";
import { ZONE_CONFIG } from "@/config";

// Helper for accessible dialog descriptions
const HiddenDesc = ({ children }) => <DialogDescription className="sr-only">{children}</DialogDescription>;

export function AppDialogs() {
  const ctx = useApp();

  return (
    <>
      {/* New World */}
      <Dialog open={ctx.showNewWorldDialog} onOpenChange={ctx.setShowNewWorldDialog}>
        <DialogContent className="dialog-content" data-testid="new-world-dialog">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><Plus size={20} />New World</DialogTitle></DialogHeader>
          <HiddenDesc>Create a new world with custom name, seed, and map size</HiddenDesc>
          <div className="dialog-form">
            <div className="form-group"><Label>World Name</Label><Input value={ctx.newWorldName} onChange={(e) => ctx.setNewWorldName(e.target.value)} placeholder="My Hytale World" data-testid="new-world-name" /></div>
            <div className="form-group"><Label>Seed (optional)</Label><Input value={ctx.newWorldSeed} onChange={(e) => ctx.setNewWorldSeed(e.target.value)} placeholder="Leave blank for random" data-testid="new-world-seed" /></div>
            <div className="form-group"><Label>Map Size</Label>
              <div className="size-presets">
                {MAP_SIZE_PRESETS.map((preset) => (
                  <Button key={preset.label} variant={ctx.newWorldSize.width === preset.width ? "default" : "outline"} size="sm" onClick={() => ctx.setNewWorldSize({ width: preset.width, height: preset.height })} data-testid={`size-${preset.width}`}>{preset.label}</Button>
                ))}
              </div>
            </div>
            <Button onClick={ctx.createWorld} disabled={ctx.loading || !ctx.newWorldName.trim()} data-testid="create-world-submit"><Plus size={16} />Create World</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Template */}
      <Dialog open={ctx.showTemplateDialog} onOpenChange={ctx.setShowTemplateDialog}>
        <DialogContent className="dialog-content dialog-lg" data-testid="template-dialog">
          <DialogHeader><DialogTitle>World Templates</DialogTitle></DialogHeader>
          <HiddenDesc>Choose a template to quickly create a pre-designed world</HiddenDesc>
          <div className="dialog-form">
            <div className="form-group"><Label>World Name</Label><Input value={ctx.newWorldName} onChange={(e) => ctx.setNewWorldName(e.target.value)} placeholder="My World" data-testid="template-world-name" /></div>
            <div className="form-group"><Label>Map Size</Label>
              <div className="size-presets">{MAP_SIZE_PRESETS.map((p) => (<Button key={p.label} variant={ctx.newWorldSize.width === p.width ? "default" : "outline"} size="sm" onClick={() => ctx.setNewWorldSize({ width: p.width, height: p.height })}>{p.label}</Button>))}</div>
            </div>
            <div className="template-grid">
              {ctx.templates.map((t) => {
                const Icon = TEMPLATE_ICONS[t.id] || Wand2;
                return (
                  <Card key={t.id} className={`template-card ${ctx.selectedTemplate === t.id ? "selected" : ""}`} onClick={() => ctx.setSelectedTemplate(t.id)} data-testid={`template-${t.id}`}>
                    <CardHeader className="template-card-header"><Icon size={24} /><CardTitle className="template-card-title">{t.name}</CardTitle></CardHeader>
                    <CardContent><CardDescription>{t.description}</CardDescription></CardContent>
                  </Card>
                );
              })}
            </div>
            <Button onClick={ctx.createFromTemplate} disabled={!ctx.selectedTemplate || !ctx.newWorldName.trim()} data-testid="create-from-template-btn"><Wand2 size={16} />Create from Template</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Import */}
      <Dialog open={ctx.showImportDialog} onOpenChange={ctx.setShowImportDialog}>
        <DialogContent className="dialog-content" data-testid="import-dialog">
          <DialogHeader><DialogTitle><Upload size={20} />Import World</DialogTitle></DialogHeader>
          <HiddenDesc>Import a world from a JSON configuration</HiddenDesc>
          <div className="dialog-form">
            <Textarea value={ctx.importConfig} onChange={(e) => ctx.setImportConfig(e.target.value)} placeholder="Paste JSON configuration..." className="import-textarea" rows={10} data-testid="import-config-input" />
            <Button onClick={ctx.importWorld} disabled={!ctx.importConfig.trim()} data-testid="import-submit"><FileJson size={16} />Import</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Auto-Generate */}
      <Dialog open={ctx.showAutoGenDialog} onOpenChange={ctx.setShowAutoGenDialog}>
        <DialogContent className="dialog-content" data-testid="autogen-dialog">
          <DialogHeader><DialogTitle><Wand2 size={20} />AI Auto-Generate</DialogTitle></DialogHeader>
          <HiddenDesc>Describe your world and let AI generate it for you</HiddenDesc>
          <div className="dialog-form">
            <Textarea value={ctx.autoGenPrompt} onChange={(e) => ctx.setAutoGenPrompt(e.target.value)} placeholder="Describe your world..." rows={4} data-testid="autogen-prompt" />
            <Button onClick={ctx.autoGenerate} disabled={ctx.autoGenLoading || !ctx.autoGenPrompt.trim()} data-testid="autogen-submit">
              {ctx.autoGenLoading ? <><Loader2 className="animate-spin" size={16} />Generating...</> : <><Wand2 size={16} />Generate World</>}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* 3D Preview */}
      <Dialog open={ctx.show3DPreview} onOpenChange={ctx.setShow3DPreview}>
        <DialogContent className="dialog-content dialog-xl" data-testid="preview-3d-dialog">
          <DialogHeader><DialogTitle><Box size={20} />3D Terrain Preview</DialogTitle></DialogHeader>
          <HiddenDesc>Height-mapped 3D terrain preview of your world</HiddenDesc>
          {ctx.preview3DData && <Preview3DCanvas data={ctx.preview3DData} />}
        </DialogContent>
      </Dialog>

      {/* Gallery */}
      <Dialog open={ctx.showGalleryDialog} onOpenChange={ctx.setShowGalleryDialog}>
        <DialogContent className="dialog-content dialog-xl" data-testid="gallery-dialog">
          <DialogHeader><DialogTitle>Community Gallery</DialogTitle></DialogHeader>
          <HiddenDesc>Browse, search, and download worlds shared by the community</HiddenDesc>
          <div className="gallery-controls">
            <div className="gallery-search"><Search size={16} /><Input value={ctx.gallerySearch} onChange={(e) => ctx.setGallerySearch(e.target.value)} placeholder="Search worlds..." data-testid="gallery-search" onKeyDown={(e) => e.key === "Enter" && ctx.fetchGallery()} /></div>
            <Select value={ctx.gallerySort} onValueChange={(v) => { ctx.setGallerySort(v); ctx.fetchGallery(); }}>
              <SelectTrigger className="gallery-sort-select" data-testid="gallery-sort"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="recent">Recent</SelectItem><SelectItem value="popular">Popular</SelectItem><SelectItem value="downloads">Downloads</SelectItem><SelectItem value="likes">Likes</SelectItem><SelectItem value="rating">Rating</SelectItem></SelectContent>
            </Select>
          </div>
          {/* Advanced Filters */}
          <div className="gallery-filters" data-testid="gallery-filters">
            <div className="filter-row">
              <Select value={ctx.galleryFilterZones || "all"} onValueChange={(v) => { ctx.setGalleryFilterZones(v === "all" ? "" : v); }}>
                <SelectTrigger className="filter-select" data-testid="filter-zone-type"><SelectValue placeholder="Zone Type" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Zones</SelectItem>
                  {Object.entries(ZONE_CONFIG).map(([k, v]) => (<SelectItem key={k} value={k}>{v.name}</SelectItem>))}
                </SelectContent>
              </Select>
              <Input className="filter-input-sm" type="number" placeholder="Min size" value={ctx.galleryFilterMapMin} onChange={(e) => ctx.setGalleryFilterMapMin(e.target.value)} data-testid="filter-map-min" />
              <Input className="filter-input-sm" type="number" placeholder="Max size" value={ctx.galleryFilterMapMax} onChange={(e) => ctx.setGalleryFilterMapMax(e.target.value)} data-testid="filter-map-max" />
              <Select value={String(ctx.galleryFilterMinRating)} onValueChange={(v) => ctx.setGalleryFilterMinRating(parseFloat(v))}>
                <SelectTrigger className="filter-select" data-testid="filter-min-rating"><SelectValue placeholder="Min Rating" /></SelectTrigger>
                <SelectContent><SelectItem value="0">Any Rating</SelectItem><SelectItem value="3">3+ Stars</SelectItem><SelectItem value="4">4+ Stars</SelectItem><SelectItem value="4.5">4.5+ Stars</SelectItem></SelectContent>
              </Select>
              {ctx.currentUser && (
                <Button variant={ctx.galleryFollowingOnly ? "default" : "outline"} size="sm" onClick={() => ctx.setGalleryFollowingOnly(!ctx.galleryFollowingOnly)} data-testid="filter-following-only">
                  <User size={14} />{ctx.galleryFollowingOnly ? "Following" : "All"}
                </Button>
              )}
              <Button size="sm" onClick={ctx.fetchGallery} data-testid="apply-gallery-filters"><Filter size={14} />Apply</Button>
            </div>
          </div>
          <ScrollArea className="gallery-grid-scroll">
            <div className="gallery-grid">
              {ctx.galleryEntries.map((entry) => (
                <Card key={entry.id} className="gallery-card" data-testid={`gallery-entry-${entry.id}`}>
                  {entry.thumbnail && (
                    <div className="gallery-card-thumbnail">
                      <img src={entry.thumbnail} alt={entry.name} />
                    </div>
                  )}
                  <CardHeader className="gallery-card-header"><CardTitle className="gallery-card-title">{entry.name}</CardTitle><CardDescription>{entry.description?.slice(0, 80)}{entry.description?.length > 80 ? "..." : ""}</CardDescription></CardHeader>
                  <CardContent>
                    <div className="gallery-meta"><Badge variant="secondary">{entry.map_size}</Badge><span><Eye size={12} />{entry.views}</span><span><ThumbsUp size={12} />{entry.likes}</span><span><Download size={12} />{entry.downloads}</span></div>
                    <div className="gallery-tags">{(entry.tags || []).map((tag, i) => (<Badge key={i} variant="outline"><Tag size={10} />{tag}</Badge>))}</div>
                    <div className="gallery-rating">
                      {entry.avg_rating ? (<span className="rating-display"><Star size={12} className="star-filled" />{entry.avg_rating} ({entry.review_count || 0})</span>) : (<span className="rating-display text-muted">No reviews</span>)}
                    </div>
                    <div className="gallery-actions">
                      <Button size="sm" onClick={() => ctx.downloadFromGallery(entry.id)}><Download size={14} /> Download</Button>
                      {ctx.currentUser && (<Button size="sm" variant="outline" onClick={() => ctx.forkFromGallery(entry.id)} data-testid={`fork-btn-${entry.id}`}><GitFork size={14} /> Fork</Button>)}
                      <Button size="sm" variant="ghost" onClick={async () => { const axios = (await import("axios")).default; await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/gallery/${entry.id}/like`); ctx.fetchGallery(); }}><ThumbsUp size={14} /></Button>
                      {ctx.currentUser && (<Button size="sm" variant="ghost" onClick={() => { ctx.setSelectedGalleryForReview(entry.id); ctx.fetchReviews(entry.id); ctx.setShowReviewDialog(true); }} data-testid={`review-btn-${entry.id}`}><Star size={14} /> Review</Button>)}
                    </div>
                  </CardContent>
                </Card>
              ))}
              {ctx.galleryEntries.length === 0 && <div className="empty-state"><p>No worlds published yet</p></div>}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Publish */}
      <Dialog open={ctx.showPublishDialog} onOpenChange={ctx.setShowPublishDialog}>
        <DialogContent className="dialog-content" data-testid="publish-dialog">
          <DialogHeader><DialogTitle>Publish to Gallery</DialogTitle></DialogHeader>
          <HiddenDesc>Share your world with the community</HiddenDesc>
          <div className="dialog-form">
            <div className="form-group"><Label>Description</Label><Textarea value={ctx.publishData.description} onChange={(e) => ctx.setPublishData({ ...ctx.publishData, description: e.target.value })} placeholder="Describe your world..." data-testid="publish-description" /></div>
            <div className="form-group"><Label>Creator Name</Label><Input value={ctx.publishData.creator_name} onChange={(e) => ctx.setPublishData({ ...ctx.publishData, creator_name: e.target.value })} placeholder={ctx.currentUser?.name || "Anonymous"} data-testid="publish-creator" /></div>
            <div className="form-group"><Label>Tags (comma separated)</Label><Input value={ctx.publishData.tags} onChange={(e) => ctx.setPublishData({ ...ctx.publishData, tags: e.target.value })} placeholder="adventure, rpg, multiplayer" data-testid="publish-tags" /></div>
            <Button onClick={ctx.publishWorld} disabled={!ctx.publishData.description} data-testid="publish-submit">Publish</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Custom Prefab */}
      <Dialog open={ctx.showCustomPrefabDialog} onOpenChange={ctx.setShowCustomPrefabDialog}>
        <DialogContent className="dialog-content" data-testid="custom-prefab-dialog">
          <DialogHeader><DialogTitle><Package size={20} />Custom Prefabs</DialogTitle></DialogHeader>
          <HiddenDesc>Create and manage custom prefab structures</HiddenDesc>
          <div className="dialog-form">
            <div className="form-group"><Label>Name</Label><Input value={ctx.newPrefab.name} onChange={(e) => ctx.setNewPrefab({ ...ctx.newPrefab, name: e.target.value })} placeholder="My Prefab" /></div>
            <div className="form-group"><Label>Description</Label><Textarea value={ctx.newPrefab.description} onChange={(e) => ctx.setNewPrefab({ ...ctx.newPrefab, description: e.target.value })} /></div>
            <div className="form-group"><Label>Color</Label><Input type="color" value={ctx.newPrefab.color} onChange={(e) => ctx.setNewPrefab({ ...ctx.newPrefab, color: e.target.value })} /></div>
            <div className="form-group"><Label>Tags</Label><Input value={ctx.newPrefab.tags} onChange={(e) => ctx.setNewPrefab({ ...ctx.newPrefab, tags: e.target.value })} placeholder="tag1, tag2" /></div>
            <Button onClick={ctx.createCustomPrefab} disabled={!ctx.newPrefab.name.trim()}>Create Prefab</Button>
          </div>
          {ctx.customPrefabs.length > 0 && (
            <ScrollArea className="custom-prefab-list">{ctx.customPrefabs.map(p => (<div key={p.id} className="custom-prefab-item"><div className="color-dot" style={{ backgroundColor: p.color }} /><span>{p.name}</span></div>))}</ScrollArea>
          )}
        </DialogContent>
      </Dialog>

      {/* Analytics */}
      <Dialog open={ctx.showAnalyticsDialog} onOpenChange={ctx.setShowAnalyticsDialog}>
        <DialogContent className="dialog-content dialog-lg" data-testid="analytics-dialog">
          <DialogHeader><DialogTitle><Activity size={20} />Analytics Dashboard</DialogTitle></DialogHeader>
          <HiddenDesc>View statistics and analytics for your worlds</HiddenDesc>
          {ctx.analyticsData && (
            <div className="analytics-grid">
              <Card><CardHeader><CardTitle className="stat-title">Total Worlds</CardTitle></CardHeader><CardContent><span className="analytics-stat">{ctx.analyticsData.total_worlds}</span></CardContent></Card>
              <Card><CardHeader><CardTitle className="stat-title">Published</CardTitle></CardHeader><CardContent><span className="analytics-stat">{ctx.analyticsData.total_published}</span></CardContent></Card>
              <Card><CardHeader><CardTitle className="stat-title">Custom Prefabs</CardTitle></CardHeader><CardContent><span className="analytics-stat">{ctx.analyticsData.total_custom_prefabs}</span></CardContent></Card>
              <Card><CardHeader><CardTitle className="stat-title">Recent Activity (24h)</CardTitle></CardHeader><CardContent><span className="analytics-stat">{ctx.analyticsData.recent_activity_24h}</span></CardContent></Card>
              {ctx.analyticsData.popular_tags?.length > 0 && (
                <Card className="span-2"><CardHeader><CardTitle className="stat-title"><TrendingUp size={16} />Popular Tags</CardTitle></CardHeader><CardContent><div className="popular-tags">{ctx.analyticsData.popular_tags.map((t, i) => (<Badge key={i} variant="secondary">{t.tag} ({t.count})</Badge>))}</div></CardContent></Card>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Procedural Preview */}
      <Dialog open={ctx.showProceduralPreview} onOpenChange={ctx.setShowProceduralPreview}>
        <DialogContent className="dialog-content dialog-lg" data-testid="procedural-preview-dialog">
          <DialogHeader><DialogTitle><Play size={20} />Procedural Generation Preview</DialogTitle></DialogHeader>
          <HiddenDesc>Watch the step-by-step procedural generation of your world</HiddenDesc>
          <div className="procedural-controls">
            <Button variant={ctx.previewPlaying ? "default" : "outline"} onClick={() => ctx.setPreviewPlaying(!ctx.previewPlaying)}>{ctx.previewPlaying ? <Pause size={16} /> : <Play size={16} />}{ctx.previewPlaying ? "Pause" : "Play"}</Button>
            <Button variant="outline" onClick={() => ctx.setCurrentPreviewStep(Math.min(ctx.proceduralSteps.length - 1, ctx.currentPreviewStep + 1))} disabled={ctx.currentPreviewStep >= ctx.proceduralSteps.length - 1}><SkipForward size={16} />Next</Button>
            <span>Step {ctx.currentPreviewStep + 1}/{ctx.proceduralSteps.length}</span>
            <Progress value={(ctx.currentPreviewStep + 1) / Math.max(1, ctx.proceduralSteps.length) * 100} />
          </div>
          {ctx.proceduralSteps[ctx.currentPreviewStep] && (
            <div className="procedural-step-info"><h4>{ctx.proceduralSteps[ctx.currentPreviewStep].name}</h4><p className="text-muted">{ctx.proceduralSteps[ctx.currentPreviewStep].description}</p><ProceduralPreviewCanvas step={ctx.proceduralSteps[ctx.currentPreviewStep]} /></div>
          )}
        </DialogContent>
      </Dialog>

      {/* Auth */}
      <Dialog open={ctx.showAuthDialog} onOpenChange={ctx.setShowAuthDialog}>
        <DialogContent className="dialog-content" data-testid="auth-dialog">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><UserCircle size={20} />{ctx.authMode === "login" ? "Sign In" : "Create Account"}</DialogTitle></DialogHeader>
          <HiddenDesc>{ctx.authMode === "login" ? "Sign in to your account" : "Create a new account to save and share worlds"}</HiddenDesc>
          <div className="dialog-form">
            {ctx.authError && <div className="auth-error" data-testid="auth-error">{ctx.authError}</div>}
            {ctx.authMode === "register" && (<div className="form-group"><Label>Name</Label><Input value={ctx.authForm.name} onChange={(e) => ctx.setAuthForm({ ...ctx.authForm, name: e.target.value })} placeholder="Your name" data-testid="auth-name-input" /></div>)}
            <div className="form-group"><Label>Email</Label><Input type="email" value={ctx.authForm.email} onChange={(e) => ctx.setAuthForm({ ...ctx.authForm, email: e.target.value })} placeholder="you@example.com" data-testid="auth-email-input" /></div>
            <div className="form-group"><Label>Password</Label><Input type="password" value={ctx.authForm.password} onChange={(e) => ctx.setAuthForm({ ...ctx.authForm, password: e.target.value })} placeholder="Enter password" data-testid="auth-password-input" onKeyDown={(e) => e.key === "Enter" && (ctx.authMode === "login" ? ctx.handleLogin() : ctx.handleRegister())} /></div>
            <Button onClick={ctx.authMode === "login" ? ctx.handleLogin : ctx.handleRegister} disabled={ctx.authLoading || !ctx.authForm.email || !ctx.authForm.password} data-testid="auth-submit-btn">
              {ctx.authLoading ? <Loader2 className="animate-spin" size={16} /> : (ctx.authMode === "login" ? <LogIn size={16} /> : <UserCircle size={16} />)}{ctx.authMode === "login" ? "Sign In" : "Register"}
            </Button>
            <div className="auth-switch">
              {ctx.authMode === "login" ? (<span>Don't have an account? <button className="link-btn" onClick={() => { ctx.setAuthMode("register"); ctx.setAuthError(""); }} data-testid="switch-to-register">Register</button></span>) : (<span>Already have an account? <button className="link-btn" onClick={() => { ctx.setAuthMode("login"); ctx.setAuthError(""); }} data-testid="switch-to-login">Sign In</button></span>)}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Profile */}
      <Dialog open={ctx.showProfileDialog} onOpenChange={ctx.setShowProfileDialog}>
        <DialogContent className="dialog-content dialog-lg" data-testid="profile-dialog">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><User size={20} />My Profile</DialogTitle></DialogHeader>
          <HiddenDesc>View and edit your profile information</HiddenDesc>
          <div className="profile-container">
            <div className="profile-info">
              <label className="profile-avatar-upload" data-testid="profile-avatar-upload">
                <input
                  type="file"
                  accept="image/*"
                  className="sr-only"
                  onChange={async (e) => {
                    const file = e.target.files?.[0];
                    if (!file) return;
                    const formData = new FormData();
                    formData.append("file", file);
                    try {
                      const axios = (await import("axios")).default;
                      const { API } = await import("@/config");
                      const res = await axios.post(`${API}/users/avatar`, formData, { withCredentials: true, headers: { "Content-Type": "multipart/form-data" } });
                      ctx.setEditProfile({ ...ctx.editProfile, avatar_url: res.data.avatar_url });
                      ctx.fetchProfile(ctx.currentUser.id);
                      ctx.checkAuth();
                    } catch (err) {
                      alert(err.response?.data?.detail || "Upload failed");
                    }
                  }}
                />
                <div className="profile-avatar">
                  {(ctx.profileData?.avatar_url || ctx.currentUser?.avatar_url) ? (
                    <img src={ctx.profileData?.avatar_url || ctx.currentUser?.avatar_url} alt="Avatar" className="profile-avatar-img" />
                  ) : (
                    <UserCircle size={64} />
                  )}
                  <div className="profile-avatar-overlay"><Camera size={18} /></div>
                </div>
              </label>
              <div className="profile-details">
                <h3 data-testid="profile-name">{ctx.profileData?.name || ctx.currentUser?.name || "User"}</h3>
                <p className="text-muted">{ctx.currentUser?.email}</p>
                <p className="profile-bio">{ctx.profileData?.bio || "No bio set"}</p>
                <p className="text-muted profile-role">Role: {ctx.profileData?.role || ctx.currentUser?.role || "user"}</p>
              </div>
            </div>
            {ctx.profileData && (
              <div className="profile-stats">
                <div className="stat-card"><span className="stat-value" data-testid="profile-worlds-count">{ctx.profileData.worlds_count}</span><span className="stat-label">Worlds</span></div>
                <div className="stat-card"><span className="stat-value">{ctx.profileData.published_count}</span><span className="stat-label">Published</span></div>
                <div className="stat-card"><span className="stat-value">{ctx.profileData.total_downloads}</span><span className="stat-label">Downloads</span></div>
                <div className="stat-card"><span className="stat-value">{ctx.profileData.total_likes}</span><span className="stat-label">Likes</span></div>
                <div className="stat-card"><span className="stat-value">{ctx.profileData.followers_count || 0}</span><span className="stat-label">Followers</span></div>
                <div className="stat-card"><span className="stat-value">{ctx.profileData.following_count || 0}</span><span className="stat-label">Following</span></div>
              </div>
            )}
            <div className="profile-edit"><h4>Edit Profile</h4>
              <div className="form-group"><Label>Name</Label><Input value={ctx.editProfile.name} onChange={(e) => ctx.setEditProfile({ ...ctx.editProfile, name: e.target.value })} data-testid="edit-profile-name" /></div>
              <div className="form-group"><Label>Bio</Label><Textarea value={ctx.editProfile.bio} onChange={(e) => ctx.setEditProfile({ ...ctx.editProfile, bio: e.target.value })} placeholder="Tell us about yourself..." data-testid="edit-profile-bio" /></div>
              <Button onClick={ctx.updateProfile} data-testid="save-profile-btn"><Save size={16} /> Save Changes</Button>
            </div>
            <button
              className="manage-sub-link"
              onClick={() => { ctx.setShowProfileDialog(false); ctx.setShowSubscriptionDialog(true); }}
              data-testid="profile-manage-sub-link"
            >
              Manage subscription
            </button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Version History */}
      <Dialog open={ctx.showVersionDialog} onOpenChange={ctx.setShowVersionDialog}>
        <DialogContent className="dialog-content dialog-lg" data-testid="version-dialog">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><History size={20} />Version History</DialogTitle></DialogHeader>
          <HiddenDesc>Manage saved versions of your world</HiddenDesc>
          <div className="version-container">
            <div className="version-actions"><Button onClick={ctx.createVersion} data-testid="create-version-btn"><Plus size={16} /> Save Current Version</Button><span className="text-muted">{ctx.worldVersions.length} version(s) saved</span></div>
            <ScrollArea className="version-list">
              {ctx.worldVersions.length === 0 ? (
                <div className="version-empty"><History size={40} className="opacity-30" /><p>No versions saved yet</p><p className="text-muted">Create a snapshot to track your progress</p></div>
              ) : (
                ctx.worldVersions.map((v) => (
                  <div key={v.id} className="version-item" data-testid={`version-${v.version_number}`}>
                    <div className="version-info"><span className="version-name">{v.name}</span><span className="version-date text-muted">{new Date(v.created_at).toLocaleString()}</span></div>
                    <Button size="sm" variant="outline" onClick={() => ctx.restoreVersion(v.id)} data-testid={`restore-version-${v.version_number}`}><RefreshCw size={14} /> Restore</Button>
                  </div>
                ))
              )}
            </ScrollArea>
          </div>
        </DialogContent>
      </Dialog>

      {/* Reviews */}
      <Dialog open={ctx.showReviewDialog} onOpenChange={ctx.setShowReviewDialog}>
        <DialogContent className="dialog-content dialog-lg" data-testid="review-dialog">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><Star size={20} />World Reviews</DialogTitle></DialogHeader>
          <HiddenDesc>Read and write reviews for this world</HiddenDesc>
          <div className="reviews-container">
            <div className="review-form"><h4>Leave a Review</h4>
              <div className="rating-input" data-testid="rating-input">
                {[1, 2, 3, 4, 5].map((star) => (<button key={star} className={`star-btn ${star <= ctx.newReview.rating ? "star-active" : ""}`} onClick={() => ctx.setNewReview({ ...ctx.newReview, rating: star })} data-testid={`star-${star}`}><Star size={24} /></button>))}
              </div>
              <Textarea value={ctx.newReview.comment} onChange={(e) => ctx.setNewReview({ ...ctx.newReview, comment: e.target.value })} placeholder="Write your review..." data-testid="review-comment-input" />
              <Button onClick={ctx.createReview} disabled={!ctx.newReview.comment} data-testid="submit-review-btn"><Send size={16} /> Submit Review</Button>
            </div>
            <div className="reviews-list"><h4>Reviews ({ctx.reviews.length})</h4>
              <ScrollArea className="reviews-scroll">
                {ctx.reviews.length === 0 ? (<div className="reviews-empty"><Star size={32} className="opacity-30" /><p>No reviews yet. Be the first!</p></div>) : (
                  ctx.reviews.map((review) => (
                    <div key={review.id} className="review-item" data-testid={`review-${review.id}`}>
                      <div className="review-header"><span className="review-user">{review.user_name}</span><span className="review-stars">{Array.from({ length: 5 }, (_, i) => (<Star key={i} size={12} className={i < review.rating ? "star-filled" : "star-empty"} />))}</span></div>
                      <p className="review-comment">{review.comment}</p>
                      <span className="review-date text-muted">{new Date(review.created_at).toLocaleDateString()}</span>
                    </div>
                  ))
                )}
              </ScrollArea>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Notifications Panel */}
      {ctx.showNotifications && ctx.currentUser && (
        <div className="notifications-panel" data-testid="notifications-panel">
          <div className="notifications-header">
            <h4><Bell size={14} /> Notifications</h4>
            {ctx.unreadCount > 0 && <button className="link-btn" onClick={ctx.markAllRead}>Mark all read</button>}
          </div>
          <ScrollArea className="notifications-list">
            {ctx.notifications.length === 0 ? (
              <div className="empty-state"><p>No notifications</p></div>
            ) : (
              ctx.notifications.map((n, i) => (
                <div key={i} className={`notification-item ${n.read ? "" : "unread"}`}>
                  <NotificationContent notification={n} />
                  <span className="notification-time">{new Date(n.created_at).toLocaleDateString()}</span>
                </div>
              ))
            )}
          </ScrollArea>
        </div>
      )}

      {/* User Search Dialog */}
      <Dialog open={ctx.showUserSearchDialog} onOpenChange={ctx.setShowUserSearchDialog}>
        <DialogContent className="dialog-content dialog-lg" data-testid="user-search-dialog">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><Search size={20} />Find Users</DialogTitle></DialogHeader>
          <DialogDescription className="sr-only">Search for users to follow</DialogDescription>
          <div className="dialog-form">
            <div className="search-bar">
              <Input value={ctx.userSearchQuery} onChange={(e) => { ctx.setUserSearchQuery(e.target.value); ctx.searchUsers(e.target.value); }} placeholder="Search by name or email..." data-testid="user-search-input" />
            </div>
            {ctx.userSearchResults.length > 0 && (
              <div className="user-search-results">
                <h4>Results</h4>
                {ctx.userSearchResults.map((u) => (
                  <div key={u.id} className="user-search-item" data-testid={`search-user-${u.id}`}>
                    <div className="user-search-info">
                      <UserCircle size={28} className="text-muted" />
                      <div><span className="user-search-name">{u.name}</span><span className="user-search-bio text-muted">{u.bio || u.role}</span></div>
                    </div>
                    {u.is_following ? (
                      <Button size="sm" variant="outline" onClick={() => { ctx.unfollowUser(u.id); ctx.searchUsers(ctx.userSearchQuery); }} data-testid={`unfollow-${u.id}`}><UserMinus size={14} />Unfollow</Button>
                    ) : (
                      <Button size="sm" onClick={() => { ctx.followUser(u.id); ctx.searchUsers(ctx.userSearchQuery); }} data-testid={`follow-${u.id}`}><UserPlus size={14} />Follow</Button>
                    )}
                  </div>
                ))}
              </div>
            )}
            {ctx.suggestedUsers.length > 0 && (
              <div className="suggested-users">
                <h4>Suggested Users</h4>
                {ctx.suggestedUsers.map((u) => (
                  <div key={u.id} className="user-search-item" data-testid={`suggested-${u.id}`}>
                    <div className="user-search-info">
                      <UserCircle size={28} className="text-muted" />
                      <div>
                        <span className="user-search-name">{u.name}</span>
                        <span className="user-search-bio text-muted">{u.published_count} worlds &middot; {u.total_likes} likes</span>
                      </div>
                    </div>
                    <Button size="sm" onClick={() => ctx.followUser(u.id)} data-testid={`follow-suggested-${u.id}`}><UserPlus size={14} />Follow</Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Activity Feed Dialog */}
      <Dialog open={ctx.showActivityFeed} onOpenChange={ctx.setShowActivityFeed}>
        <DialogContent className="dialog-content dialog-lg" data-testid="activity-feed-dialog">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><Activity size={20} />Activity Feed</DialogTitle></DialogHeader>
          <DialogDescription className="sr-only">Recent activity from users you follow</DialogDescription>
          <ScrollArea className="activity-feed-scroll">
            {ctx.activityFeed.length === 0 ? (
              <div className="empty-state">
                <Activity size={32} className="opacity-30" />
                <p>No activity yet</p>
                <p className="text-muted">Follow users to see their activity here</p>
              </div>
            ) : (
              ctx.activityFeed.map((a, i) => (
                <div key={i} className="activity-item" data-testid={`activity-${i}`}>
                  <div className="activity-icon">
                    {a.type === "publication" ? <Upload size={16} /> : <Star size={16} />}
                  </div>
                  <div className="activity-content">
                    {a.type === "publication" ? (
                      <><strong>{a.user_name}</strong> published <strong>{a.data.world_name}</strong><p className="text-muted">{a.data.description}</p><div className="activity-meta"><Badge variant="secondary">{a.data.map_size}</Badge><span>{a.data.likes} likes</span><span>{a.data.downloads} downloads</span></div></>
                    ) : (
                      <><strong>{a.user_name}</strong> reviewed a world ({a.data.rating}/5)<p className="text-muted">{a.data.comment}</p></>
                    )}
                    <span className="activity-time text-muted">{new Date(a.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))
            )}
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Collaborators Dialog */}
      <Dialog open={ctx.showCollabDialog} onOpenChange={ctx.setShowCollabDialog}>
        <DialogContent className="dialog-content dialog-lg" data-testid="collaborators-dialog">
          <DialogHeader><DialogTitle className="flex items-center gap-2"><UserPlus size={20} />World Collaborators</DialogTitle></DialogHeader>
          <DialogDescription className="sr-only">Manage who can edit or view this world</DialogDescription>
          <div className="collab-manager">
            {ctx.worldCollaborators.owner && (
              <div className="collab-owner">
                <div className="collab-user-info"><Shield size={16} className="text-amber-400" /><span className="collab-user-name">{ctx.worldCollaborators.owner.name}</span><Badge>Owner</Badge></div>
              </div>
            )}
            <div className="collab-invite">
              <h4>Invite Collaborator</h4>
              <div className="collab-invite-form">
                <div className="collab-search-wrapper">
                  <Input value={ctx.collabInviteEmail} onChange={(e) => { ctx.setCollabInviteEmail(e.target.value); if (e.target.value.length >= 2) ctx.searchUsers(e.target.value); }} placeholder="Search user by name..." data-testid="collab-invite-input" />
                  {ctx.collabInviteEmail.length >= 2 && ctx.userSearchResults.length > 0 && (
                    <div className="collab-search-dropdown" data-testid="collab-search-dropdown">
                      {ctx.userSearchResults.slice(0, 5).map((u) => (
                        <button key={u.id} className="collab-search-item" onClick={() => { ctx.addCollaborator(u.id, ctx.collabInviteRole); ctx.setCollabInviteEmail(""); }} data-testid={`collab-select-${u.id}`}>
                          <UserCircle size={18} className="text-muted" />
                          <div className="collab-search-item-info">
                            <span className="collab-search-name">{u.name}</span>
                            <span className="collab-search-email">{u.email || u.role}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                <Select value={ctx.collabInviteRole} onValueChange={ctx.setCollabInviteRole}>
                  <SelectTrigger className="collab-role-select" data-testid="collab-role-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="viewer"><div className="collab-role-option"><Eye size={14} /><div><span>Viewer</span><span className="collab-role-desc">Can view but not edit</span></div></div></SelectItem>
                    <SelectItem value="editor"><div className="collab-role-option"><Pencil size={14} /><div><span>Editor</span><span className="collab-role-desc">Can edit zones and prefabs</span></div></div></SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={async () => {
                  if (!ctx.collabInviteEmail) return;
                  const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/users/search?q=${ctx.collabInviteEmail}`, { credentials: "include" });
                  const data = await res.json();
                  if (data.users?.length > 0) { ctx.addCollaborator(data.users[0].id, ctx.collabInviteRole); ctx.setCollabInviteEmail(""); }
                  else alert("User not found");
                }} data-testid="collab-invite-btn"><UserPlus size={16} />Add</Button>
              </div>
            </div>
            <div className="collab-list">
              <h4>Collaborators ({ctx.worldCollaborators.collaborators.length})</h4>
              {ctx.worldCollaborators.collaborators.length === 0 ? (
                <div className="collab-empty-state">
                  <Users size={28} className="opacity-30" />
                  <p className="text-muted">No collaborators yet. Search for users above to invite them.</p>
                </div>
              ) : (
                ctx.worldCollaborators.collaborators.map((c) => (
                  <div key={c.user_id} className="collab-item" data-testid={`collab-${c.user_id}`}>
                    <div className="collab-user-info">
                      <UserCircle size={20} />
                      <div className="collab-user-details">
                        <span className="collab-user-name">{c.name}</span>
                        <span className="collab-user-role-label">{c.role === "editor" ? "Can edit" : "View only"}</span>
                      </div>
                    </div>
                    <div className="collab-item-actions">
                      <Select value={c.role} onValueChange={(v) => ctx.updateCollaboratorRole(c.user_id, v)}>
                        <SelectTrigger className="collab-role-mini"><SelectValue /></SelectTrigger>
                        <SelectContent><SelectItem value="viewer">Viewer</SelectItem><SelectItem value="editor">Editor</SelectItem></SelectContent>
                      </Select>
                      <Button size="icon" variant="ghost" onClick={() => ctx.removeCollaborator(c.user_id)} data-testid={`remove-collab-${c.user_id}`}><Trash2 size={14} /></Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

function NotificationContent({ notification }) {
  const { type, data } = notification;
  switch (type) {
    case "new_follower": return <span><strong>{data.follower_name}</strong> started following you</span>;
    case "new_publication": return <span><strong>{data.publisher_name}</strong> published <strong>{data.world_name}</strong></span>;
    case "world_liked": return <span><strong>{data.liker_name}</strong> liked <strong>{data.world_name}</strong></span>;
    case "world_downloaded": return <span><strong>{data.downloader_name}</strong> downloaded <strong>{data.world_name}</strong></span>;
    case "new_review": return <span><strong>{data.reviewer_name}</strong> reviewed <strong>{data.world_name}</strong> ({data.rating}/5)</span>;
    case "world_forked": return <span><strong>{data.forker_name}</strong> forked <strong>{data.world_name}</strong></span>;
    case "collab_invite": return <span><strong>{data.inviter_name}</strong> invited you as <strong>{data.role}</strong> on <strong>{data.world_name}</strong></span>;
    default: return <span>New notification</span>;
  }
}

// ========== Canvas Sub-Components ==========
function Preview3DCanvas({ data }) {
  const canvasRef = useRef(null);
  useEffect(() => {
    if (!canvasRef.current || !data) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const { dimensions, height_map, zones, terrain } = data;
    const cellSize = Math.min(600 / dimensions.width, 400 / dimensions.height);
    canvas.width = dimensions.width * cellSize;
    canvas.height = dimensions.height * cellSize;
    const zoneMap = {};
    zones.forEach(z => { zoneMap[`${z.x}-${z.y}`] = z; });
    for (let y = 0; y < dimensions.height; y++) {
      for (let x = 0; x < dimensions.width; x++) {
        const height = height_map[y]?.[x] || 0.5;
        const zone = zoneMap[`${x}-${y}`];
        let baseColor;
        if (zone) {
          const zoneColors = { emerald_grove: [16, 185, 129], borea: [6, 182, 212], desert: [245, 158, 11], arctic: [226, 232, 240], corrupted: [139, 92, 246] };
          baseColor = zoneColors[zone.type] || [107, 114, 128];
        } else {
          baseColor = height < terrain.ocean_level ? [30, 64, 175] : [71, 85, 105];
        }
        const brightness = 0.5 + height * 0.5;
        ctx.fillStyle = `rgb(${Math.min(255, Math.floor(baseColor[0] * brightness))}, ${Math.min(255, Math.floor(baseColor[1] * brightness))}, ${Math.min(255, Math.floor(baseColor[2] * brightness))})`;
        ctx.fillRect(x * cellSize, y * cellSize, cellSize, cellSize);
      }
    }
    data.prefabs.forEach(p => {
      ctx.fillStyle = '#fff'; ctx.beginPath();
      ctx.arc(p.position.x * cellSize + cellSize/2, p.position.y * cellSize + cellSize/2, cellSize/3, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [data]);
  return (<div className="preview-3d-container"><canvas ref={canvasRef} className="preview-3d-canvas" /><div className="preview-3d-info"><p>Height-mapped terrain view with zone coloring</p><p className="text-muted">White dots indicate structure locations</p></div></div>);
}

function ProceduralPreviewCanvas({ step }) {
  const canvasRef = useRef(null);
  useEffect(() => {
    if (!canvasRef.current || !step) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const size = 32; const cellSize = 12;
    canvas.width = size * cellSize; canvas.height = size * cellSize;
    ctx.fillStyle = '#1A1D2A'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = '#2D3748';
    for (let i = 0; i <= size; i++) { ctx.beginPath(); ctx.moveTo(i * cellSize, 0); ctx.lineTo(i * cellSize, size * cellSize); ctx.stroke(); ctx.beginPath(); ctx.moveTo(0, i * cellSize); ctx.lineTo(size * cellSize, i * cellSize); ctx.stroke(); }
    const zoneColors = { emerald_grove: '#10B981', borea: '#06B6D4', desert: '#F59E0B', arctic: '#E2E8F0', corrupted: '#8B5CF6' };
    (step.zones || []).forEach(z => { ctx.fillStyle = zoneColors[z.type] || '#6B7280'; ctx.globalAlpha = 0.6; ctx.fillRect(z.x * cellSize, z.y * cellSize, cellSize, cellSize); ctx.globalAlpha = 1; });
    (step.prefabs || []).forEach(p => { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(p.x * cellSize + cellSize/2, p.y * cellSize + cellSize/2, 3, 0, Math.PI * 2); ctx.fill(); });
  }, [step]);
  return <canvas ref={canvasRef} className="procedural-canvas" />;
}
