import { useState, useEffect, useRef } from "react";
import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { ZONE_CONFIG, PREFAB_CONFIG, BIOME_CONFIG } from "@/config";
import { Wand2, Plus, LayoutTemplate, Upload, Mountain, Layers, Trash2 } from "lucide-react";

// ========== Map Canvas (virtualized) ==========
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
      setVisibleRange({
        startX: Math.max(0, Math.floor(-pan.x / scaledCellSize) - buffer),
        endX: Math.min(world.map_width, Math.ceil((rect.width - pan.x) / scaledCellSize) + buffer),
        startY: Math.max(0, Math.floor(-pan.y / scaledCellSize) - buffer),
        endY: Math.min(world.map_height, Math.ceil((rect.height - pan.y) / scaledCellSize) + buffer),
      });
    };
    updateVisibleRange();
    window.addEventListener('resize', updateVisibleRange);
    return () => window.removeEventListener('resize', updateVisibleRange);
  }, [pan, zoom, scaledCellSize, world.map_width, world.map_height]);

  const zoneMap = {};
  world.zones.forEach(zone => { zoneMap[`${zone.x}-${zone.y}`] = zone; });
  const prefabMap = {};
  world.prefabs.forEach(prefab => { const key = `${prefab.x}-${prefab.y}`; if (!prefabMap[key]) prefabMap[key] = []; prefabMap[key].push(prefab); });

  const visibleCells = [];
  for (let y = visibleRange.startY; y < visibleRange.endY; y++) {
    for (let x = visibleRange.startX; x < visibleRange.endX; x++) {
      const key = `${x}-${y}`;
      const zone = zoneMap[key];
      const prefabs = prefabMap[key] || [];
      const isSelected = selectedElement && ((selectedElement.type === "zone" && zone?.id === selectedElement.data.id) || (selectedElement.type === "prefab" && prefabs.some(p => p.id === selectedElement.data.id)));
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
      <div ref={containerRef} className="map-viewport"
        onMouseDown={(e) => handleMouseEvent(e, 'down')}
        onMouseMove={(e) => handleMouseEvent(e, 'move')}
        onMouseUp={(e) => handleMouseEvent(e, 'up')}
        onMouseLeave={(e) => handleMouseEvent(e, 'up')}
        style={{ cursor: activeTool === 'pan' ? 'grab' : activeTool === 'select' ? 'default' : 'crosshair' }}
      >
        <div className="map-grid-container" style={{
          width: world.map_width * scaledCellSize, height: world.map_height * scaledCellSize,
          transform: `translate(${pan.x}px, ${pan.y}px)`,
          backgroundSize: `${scaledCellSize}px ${scaledCellSize}px`,
          backgroundImage: `linear-gradient(to right, var(--border-default) 1px, transparent 1px), linear-gradient(to bottom, var(--border-default) 1px, transparent 1px)`
        }}>
          {visibleCells.map(({ x, y, key, zone, prefabs, isSelected }) => {
            const ZoneIcon = zone ? ZONE_CONFIG[zone.type]?.icon : null;
            return (
              <div key={key} className={`map-cell-abs ${isSelected ? 'selected' : ''}`} style={{
                left: x * scaledCellSize, top: y * scaledCellSize, width: scaledCellSize, height: scaledCellSize,
                backgroundColor: zone ? `${ZONE_CONFIG[zone.type]?.color}50` : 'transparent',
                borderColor: isSelected ? '#fff' : (zone ? ZONE_CONFIG[zone.type]?.color : 'transparent')
              }} data-testid={`cell-${x}-${y}`}>
                {zone && scaledCellSize > 16 && (
                  <div className="cell-content">{ZoneIcon && <ZoneIcon size={Math.min(14, scaledCellSize * 0.5)} style={{ color: ZONE_CONFIG[zone.type]?.color }} />}</div>
                )}
                {prefabs.map((prefab) => {
                  const PrefabIcon = PREFAB_CONFIG[prefab.type]?.icon;
                  return (<div key={prefab.id} className="cell-prefab-marker">{PrefabIcon && scaledCellSize > 12 && <PrefabIcon size={Math.min(12, scaledCellSize * 0.4)} />}</div>);
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
            <div key={key} className="legend-item"><div className="color-dot" style={{ backgroundColor: config.color }} /><span>{config.name}</span></div>
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

// ========== Terrain Panel ==========
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
            <div className="control-header"><Label>{label}</Label><span className="control-value">{(terrain?.[key] || def).toFixed(2)}</span></div>
            <Slider value={[terrain?.[key] || def]} min={min} max={max} step={0.05} onValueChange={([v]) => onUpdate(key, v)} />
          </div>
        ))}
      </div>
    </div>
  );
}

// ========== Zone Properties ==========
function ZonePropertiesPanel({ zone, onUpdate, onUpdateBiomes, onDelete }) {
  const zoneConfig = ZONE_CONFIG[zone.type];
  const availableBiomes = Object.entries(BIOME_CONFIG).filter(([_, b]) => b.zones.includes(zone.type));
  const toggleBiome = (biomeId) => {
    const currentBiomes = zone.biomes || [];
    const idx = currentBiomes.findIndex(b => b.type === biomeId);
    if (idx >= 0) onUpdateBiomes(zone.id, currentBiomes.filter((_, i) => i !== idx));
    else onUpdateBiomes(zone.id, [...currentBiomes, { type: biomeId, density: 0.5, variation: 0.3 }]);
  };
  const updateBiomeSetting = (biomeId, key, value) => {
    onUpdateBiomes(zone.id, (zone.biomes || []).map(b => b.type === biomeId ? { ...b, [key]: value } : b));
  };

  return (
    <div className="properties-panel">
      <div className="property-group"><Label>Zone Type</Label><div className="zone-type-display"><div className="color-dot large" style={{ backgroundColor: zoneConfig.color }} /><span>{zoneConfig.name}</span></div></div>
      <div className="property-group"><Label>Position</Label><div className="position-display">X: {zone.x}, Y: {zone.y}</div></div>
      <div className="property-group">
        <Label>Difficulty (1-10)</Label>
        <div className="slider-with-value"><Slider value={[zone.difficulty || 1]} min={1} max={10} step={1} onValueChange={([v]) => onUpdate(zone.id, 'difficulty', v)} /><span className="slider-value">{zone.difficulty || 1}</span></div>
      </div>
      <div className="property-group">
        <Label className="flex items-center gap-2"><Layers size={14} />Biomes</Label>
        <div className="biome-list">
          {availableBiomes.map(([biomeId, biomeConfig]) => {
            const isActive = zone.biomes?.some(b => b.type === biomeId);
            const biomeData = zone.biomes?.find(b => b.type === biomeId);
            return (
              <div key={biomeId} className={`biome-item ${isActive ? 'active' : ''}`}>
                <div className="biome-header" onClick={() => toggleBiome(biomeId)}><div className="color-dot" style={{ backgroundColor: biomeConfig.color }} /><span>{biomeConfig.name}</span><input type="checkbox" checked={isActive} readOnly /></div>
                {isActive && biomeData && (
                  <div className="biome-settings"><div className="biome-slider"><span>Density</span><Slider value={[biomeData.density || 0.5]} min={0} max={1} step={0.1} onValueChange={([v]) => updateBiomeSetting(biomeId, 'density', v)} /><span>{(biomeData.density || 0.5).toFixed(1)}</span></div></div>
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

// ========== Prefab Properties ==========
function PrefabPropertiesPanel({ prefab, onUpdate, onDelete }) {
  const prefabConfig = PREFAB_CONFIG[prefab.type];
  const Icon = prefabConfig.icon;
  return (
    <div className="properties-panel">
      <div className="property-group"><Label>Structure Type</Label><div className="prefab-type-display"><Icon size={18} /><span>{prefabConfig.name}</span></div></div>
      <div className="property-group"><Label>Position</Label><div className="position-display">X: {prefab.x}, Y: {prefab.y}</div></div>
      <div className="property-group"><Label>Rotation</Label>
        <Select value={String(prefab.rotation || 0)} onValueChange={(v) => onUpdate(prefab.id, 'rotation', parseInt(v))}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="0">0°</SelectItem><SelectItem value="90">90°</SelectItem><SelectItem value="180">180°</SelectItem><SelectItem value="270">270°</SelectItem></SelectContent></Select>
      </div>
      <div className="property-group"><Label>Scale</Label><div className="slider-with-value"><Slider value={[prefab.scale || 1]} min={0.5} max={2} step={0.1} onValueChange={([v]) => onUpdate(prefab.id, 'scale', v)} /><span className="slider-value">{(prefab.scale || 1).toFixed(1)}x</span></div></div>
      <Button variant="destructive" onClick={onDelete} className="delete-btn"><Trash2 size={16} />Delete Structure</Button>
    </div>
  );
}

// ========== Main MapArea ==========
export function MapArea() {
  const ctx = useApp();

  return (
    <>
      <main className="canvas-area" data-testid="canvas-area">
        {ctx.currentWorld ? (
          <>
            <MapCanvas
              world={ctx.currentWorld}
              onMouseDown={ctx.handleMapMouseDown}
              onMouseMove={ctx.handleMapMouseMove}
              onMouseUp={ctx.handleMapMouseUp}
              activeTool={ctx.activeTool}
              zoom={ctx.zoom}
              pan={ctx.pan}
              selectedElement={ctx.selectedElement}
            />
            <TerrainPanel terrain={ctx.currentWorld.terrain} onUpdate={ctx.updateTerrain} />
          </>
        ) : (
          <div className="empty-canvas">
            <div className="empty-canvas-content">
              <img src="https://images.pexels.com/photos/9977648/pexels-photo-9977648.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940" alt="World" className="empty-canvas-bg" />
              <div className="empty-canvas-overlay">
                <Wand2 size={48} className="empty-icon" />
                <h2>Create Your World</h2>
                <p>Build worlds up to 512x512 tiles</p>
                <div className="empty-actions">
                  <Button onClick={() => ctx.setShowNewWorldDialog(true)} data-testid="create-first-world-btn"><Plus size={16} />New World</Button>
                  <Button variant="outline" onClick={() => ctx.setShowTemplateDialog(true)}><LayoutTemplate size={16} />From Template</Button>
                  <Button variant="outline" onClick={() => ctx.setShowImportDialog(true)}><Upload size={16} />Import</Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Properties Sheet */}
      <Sheet open={ctx.propertiesOpen} onOpenChange={ctx.setPropertiesOpen}>
        <SheetContent className="properties-sheet">
          <SheetHeader><SheetTitle>{ctx.selectedElement?.type === "zone" ? "Zone Properties" : "Structure Properties"}</SheetTitle></SheetHeader>
          {ctx.selectedElement?.type === "zone" && (
            <ZonePropertiesPanel zone={ctx.selectedElement.data} onUpdate={ctx.updateZoneProperty} onUpdateBiomes={ctx.updateZoneBiomes} onDelete={ctx.deleteZone} />
          )}
          {ctx.selectedElement?.type === "prefab" && (
            <PrefabPropertiesPanel prefab={ctx.selectedElement.data} onUpdate={ctx.updatePrefabProperty} onDelete={ctx.deletePrefab} />
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
