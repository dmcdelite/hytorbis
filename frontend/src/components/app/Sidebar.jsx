import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ZONE_CONFIG, PREFAB_CONFIG } from "@/config";
import {
  FolderOpen, Plus, LayoutTemplate, Upload, Settings, MousePointer,
  Paintbrush, Castle, Move, Wand2, ZoomIn, ZoomOut, Maximize2,
  Save, Share2, FileJson, Download, Layers, Package, Trash2, FolderDown, ExternalLink
} from "lucide-react";

export function Sidebar() {
  const ctx = useApp();

  return (
    <aside className="sidebar-left" data-testid="sidebar-left">
      {/* Worlds */}
      <div className="sidebar-section">
        <div className="section-header">
          <FolderOpen size={16} />
          <span>Worlds</span>
          <div className="section-actions">
            <Button variant="ghost" size="icon" onClick={() => ctx.setShowTemplateDialog(true)} title="From Template" data-testid="template-btn">
              <LayoutTemplate size={16} />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => ctx.setShowImportDialog(true)} title="Import" data-testid="import-btn">
              <Upload size={16} />
            </Button>
            <Button variant="ghost" size="icon" onClick={() => ctx.setShowNewWorldDialog(true)} title="New World" data-testid="new-world-btn">
              <Plus size={16} />
            </Button>
          </div>
        </div>
        <ScrollArea className="worlds-list">
          {ctx.worlds.map((world) => {
            // Lazy-load thumbnail
            if (!ctx.thumbnails[world.id] && world.zones?.length > 0) ctx.fetchThumbnail(world.id);
            return (
              <div key={world.id} className={`world-item ${ctx.currentWorld?.id === world.id ? "active" : ""}`} onClick={() => ctx.loadWorld(world.id)} data-testid={`world-item-${world.id}`}>
                {ctx.thumbnails[world.id] && (
                  <img src={ctx.thumbnails[world.id]} alt="" className="world-item-thumb" />
                )}
                <div className="world-item-info">
                  <span className="world-item-name">{world.name}</span>
                  <span className="world-item-seed">{world.seed} • {world.map_width}x{world.map_height}</span>
                </div>
                <Button variant="ghost" size="icon" className="world-delete-btn" onClick={(e) => { e.stopPropagation(); ctx.deleteWorld(world.id); }} data-testid={`delete-world-${world.id}`}>
                  <Trash2 size={14} />
                </Button>
              </div>
            );
          })}
          {ctx.worlds.length === 0 && (
            <div className="empty-state">
              <p>No worlds yet</p>
              <p className="text-muted">Create or import a world</p>
            </div>
          )}
        </ScrollArea>
      </div>

      {/* Tools */}
      {ctx.currentWorld && (
        <div className="sidebar-section">
          <div className="section-header">
            <Settings size={16} /><span>Tools</span>
          </div>
          <div className="tools-grid">
            <Button variant={ctx.activeTool === "select" ? "default" : "secondary"} className="tool-btn" onClick={() => ctx.setActiveTool("select")} data-testid="tool-select"><MousePointer size={16} />Select</Button>
            <Button variant={ctx.activeTool === "zone" ? "default" : "secondary"} className="tool-btn" onClick={() => ctx.setActiveTool("zone")} data-testid="tool-zone"><Paintbrush size={16} />Zone</Button>
            <Button variant={ctx.activeTool === "prefab" ? "default" : "secondary"} className="tool-btn" onClick={() => ctx.setActiveTool("prefab")} data-testid="tool-prefab"><Castle size={16} />Prefab</Button>
            <Button variant={ctx.activeTool === "pan" ? "default" : "secondary"} className="tool-btn" onClick={() => ctx.setActiveTool("pan")} data-testid="tool-pan"><Move size={16} />Pan</Button>
          </div>
          {ctx.activeTool === "zone" && (
            <div className="tool-options">
              <Label className="tool-label">Zone Type</Label>
              <Select value={ctx.selectedZoneType} onValueChange={ctx.setSelectedZoneType}>
                <SelectTrigger data-testid="zone-type-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.entries(ZONE_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>
                      <div className="select-item-with-color"><div className="color-dot" style={{ backgroundColor: config.color }} />{config.name}</div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {ctx.activeTool === "prefab" && (
            <div className="tool-options">
              <Label className="tool-label">Structure Type</Label>
              <Select value={ctx.selectedPrefabType} onValueChange={ctx.setSelectedPrefabType}>
                <SelectTrigger data-testid="prefab-type-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {Object.entries(PREFAB_CONFIG).map(([key, config]) => {
                    const Icon = config.icon;
                    return (<SelectItem key={key} value={key}><div className="select-item-with-icon"><Icon size={14} />{config.name}</div></SelectItem>);
                  })}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      )}

      {/* AI Auto-Generate */}
      {ctx.currentWorld && (
        <div className="sidebar-section">
          <Button variant="outline" className="auto-gen-btn" onClick={() => ctx.setShowAutoGenDialog(true)} data-testid="auto-generate-btn">
            <Wand2 size={16} />AI Auto-Generate
          </Button>
        </div>
      )}

      {/* Zoom */}
      {ctx.currentWorld && (
        <div className="sidebar-section">
          <div className="section-header"><ZoomIn size={16} /><span>Zoom: {Math.round(ctx.zoom * 100)}%</span></div>
          <div className="zoom-controls">
            <Button variant="secondary" size="icon" onClick={() => ctx.setZoom(z => Math.max(0.1, z - 0.1))} data-testid="zoom-out"><ZoomOut size={16} /></Button>
            <Slider value={[ctx.zoom]} min={0.1} max={2} step={0.1} onValueChange={([v]) => ctx.setZoom(v)} className="zoom-slider" />
            <Button variant="secondary" size="icon" onClick={() => ctx.setZoom(z => Math.min(2, z + 0.1))} data-testid="zoom-in"><ZoomIn size={16} /></Button>
          </div>
          <Button variant="ghost" size="sm" className="fit-btn" onClick={() => ctx.autoZoom(ctx.currentWorld.map_width)}><Maximize2 size={14} />Reset View</Button>
        </div>
      )}

      {/* Actions */}
      {ctx.currentWorld && (
        <div className="sidebar-section sidebar-actions">
          <Button onClick={ctx.saveWorld} disabled={ctx.loading} className="action-btn" data-testid="save-world-btn"><Save size={16} />Save World</Button>
          <div className="export-buttons">
            <Button variant="outline" onClick={() => ctx.setShowPublishDialog(true)} className="publish-btn" data-testid="publish-btn"><Share2 size={16} />Publish</Button>
            <Button variant="outline" onClick={() => ctx.setShowShareDialog(true)} className="share-btn" data-testid="share-world-btn"><ExternalLink size={16} />Share</Button>
          </div>
          <div className="export-buttons">
            <Button variant="secondary" onClick={() => ctx.exportWorld("json")} data-testid="export-json-btn" title="Export as JSON"><FileJson size={16} />JSON</Button>
            <Button variant="secondary" onClick={() => ctx.exportWorld("hytale")} data-testid="export-hytale-btn" title="Export Hytale config"><Download size={16} />Hytale</Button>
          </div>
          <div className="export-buttons">
            <Button variant="secondary" onClick={() => ctx.exportWorld("prefab")} data-testid="export-prefab-btn" title="Export as .prefab.json"><Layers size={16} />Prefab</Button>
            <Button variant="secondary" onClick={() => ctx.exportWorld("jar")} data-testid="export-jar-btn" title="Export as .jar mod package"><Package size={16} />JAR</Button>
          </div>
          <Button variant="outline" onClick={() => ctx.setShowInstallDialog(true)} className="install-game-btn" data-testid="install-to-game-btn">
            <FolderDown size={16} />Install to Game
          </Button>
        </div>
      )}
    </aside>
  );
}
