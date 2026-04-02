import { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { API } from "@/config";
import { ZONE_CONFIG } from "@/config";
import { Button } from "@/components/ui/button";
import { Crown, Map, Layers, Box, Sparkles, Users, Download, UserCircle, ExternalLink, Wand2 } from "lucide-react";

export function SharedView({ shareToken, isEmbed }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const setMetaTag = (name, content) => {
    const attr = name.startsWith("og:") || name.startsWith("twitter:") ? "property" : "name";
    let el = document.querySelector(`meta[${attr}="${name}"]`);
    if (!el) { el = document.createElement("meta"); el.setAttribute(attr, name); document.head.appendChild(el); }
    el.setAttribute("content", content);
  };

  useEffect(() => {
    const fetchShared = async () => {
      try {
        const res = await axios.get(`${API}/shared/${shareToken}`);
        setData(res.data);
        // Set OG meta tags for crawlers that render JS (Discord, Telegram)
        if (res.data?.world) {
          document.title = `${res.data.world.name} — Hyt Orbis World Builder`;
          setMetaTag("og:title", `${res.data.world.name} — Built with Hyt Orbis`);
          setMetaTag("og:description", res.data.world.description || `A ${res.data.stats?.map_size} world with ${res.data.stats?.zones} zones and ${res.data.stats?.prefabs} prefabs`);
          setMetaTag("og:image", res.data.thumbnail || `${window.location.origin}/hytorbis-logo.png`);
          setMetaTag("og:url", window.location.href);
          setMetaTag("og:type", "website");
          setMetaTag("og:site_name", "Hyt Orbis World Builder");
          setMetaTag("twitter:card", "summary_large_image");
          setMetaTag("twitter:title", `${res.data.world.name} — Hyt Orbis`);
          setMetaTag("twitter:description", res.data.world.description || "Check out this world on Hyt Orbis World Builder");
          setMetaTag("twitter:image", res.data.thumbnail || `${window.location.origin}/hytorbis-logo.png`);
        }
      } catch (e) {
        setError(e.response?.status === 404 ? "This world is no longer shared." : "Failed to load shared world.");
      }
      setLoading(false);
    };
    fetchShared();
    return () => { document.title = "Hyt Orbis World Builder"; };
  }, [shareToken]);

  // Build a mini map preview from zone data
  const miniMap = useMemo(() => {
    if (!data?.world?.zones?.length) return null;
    const zones = data.world.zones;
    const w = data.world.map_width || 64;
    const h = data.world.map_height || 64;
    const cellSize = Math.max(1, Math.min(4, Math.floor(280 / Math.max(w, h))));
    return { zones, w, h, cellSize };
  }, [data]);

  if (loading) {
    return (
      <div className="shared-loading">
        <div className="shared-loading-spinner" />
        <span>Loading world...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="shared-error">
        <Map size={48} />
        <h2>{error}</h2>
        <p>The creator may have disabled sharing for this world.</p>
        <a href={window.location.origin} className="shared-cta-btn-link">
          <Button className="shared-cta-btn">Create Your Own World — Free</Button>
        </a>
      </div>
    );
  }

  const { world, creator, stats, thumbnail } = data;

  if (isEmbed) {
    return (
      <div className="shared-embed" data-testid="shared-embed">
        <div className="shared-embed-header">
          <img src="/hytorbis-logo.png" alt="Hyt Orbis" className="shared-embed-logo" />
          <div>
            <h3 className="shared-embed-title">{world.name}</h3>
            <span className="shared-embed-meta">{stats.map_size} — {stats.zones} zones, {stats.prefabs} prefabs</span>
          </div>
        </div>
        <div className="shared-embed-preview">
          {thumbnail ? (
            <img src={thumbnail} alt={world.name} className="shared-embed-thumb" />
          ) : miniMap ? (
            <MiniMapCanvas miniMap={miniMap} />
          ) : (
            <div className="shared-embed-placeholder"><Map size={32} /></div>
          )}
        </div>
        <a href={`${window.location.origin}?share=${shareToken}`} target="_blank" rel="noopener noreferrer" className="shared-embed-footer">
          View on Hyt Orbis World Builder <ExternalLink size={12} />
        </a>
      </div>
    );
  }

  return (
    <div className="shared-page" data-testid="shared-page">
      <div className="shared-bg">
        <div className="shared-bg-grid" />
      </div>

      {/* Header */}
      <header className="shared-header">
        <div className="shared-header-left">
          <img src="/hytorbis-logo.png" alt="Hyt Orbis" className="shared-header-logo" />
          <span className="shared-header-brand">Hyt Orbis</span>
        </div>
        <a href={window.location.origin}>
          <Button className="shared-header-cta" data-testid="shared-header-cta">
            <Sparkles size={14} /> Create Your Own
          </Button>
        </a>
      </header>

      {/* Main content */}
      <main className="shared-main">
        <div className="shared-preview-col">
          {/* World preview */}
          <div className="shared-preview-card" data-testid="shared-preview-card">
            {thumbnail ? (
              <img src={thumbnail} alt={world.name} className="shared-preview-thumb" />
            ) : miniMap ? (
              <MiniMapCanvas miniMap={miniMap} />
            ) : (
              <div className="shared-preview-placeholder">
                <Map size={64} />
                <span>World Preview</span>
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="shared-stats">
            <div className="shared-stat">
              <Layers size={16} />
              <span>{stats.zones} Zones</span>
            </div>
            <div className="shared-stat">
              <Box size={16} />
              <span>{stats.prefabs} Prefabs</span>
            </div>
            <div className="shared-stat">
              <Map size={16} />
              <span>{stats.map_size}</span>
            </div>
          </div>
        </div>

        <div className="shared-info-col">
          {/* World info */}
          <h1 className="shared-world-name" data-testid="shared-world-name">{world.name}</h1>
          {world.description && <p className="shared-world-desc">{world.description}</p>}

          {/* Creator */}
          {creator && (
            <div className="shared-creator" data-testid="shared-creator">
              {creator.avatar_url ? (
                <img src={creator.avatar_url} alt={creator.name} className="shared-creator-avatar" />
              ) : (
                <UserCircle size={32} />
              )}
              <div>
                <span className="shared-creator-name">Built by {creator.name}</span>
                {creator.bio && <span className="shared-creator-bio">{creator.bio}</span>}
              </div>
            </div>
          )}

          {/* Seed info */}
          <div className="shared-meta-row">
            <span className="shared-meta-label">Seed:</span>
            <code className="shared-meta-value">{world.seed}</code>
          </div>

          {/* CTA Section — the "too good to miss" */}
          <div className="shared-cta-card" data-testid="shared-cta-card">
            <div className="shared-cta-glow" />
            <Crown size={24} className="shared-cta-icon" />
            <h2 className="shared-cta-title">Want to build worlds like this?</h2>
            <p className="shared-cta-text">
              Join thousands of creators using AI-powered world generation, real-time collaboration, and one-click game exports.
            </p>
            <ul className="shared-cta-features">
              <li><Wand2 size={14} /> AI generates entire worlds from text prompts</li>
              <li><Users size={14} /> Build together in real-time</li>
              <li><Download size={14} /> Export directly to your game</li>
              <li><Sparkles size={14} /> Start free — no credit card required</li>
            </ul>
            <a href={window.location.origin} className="shared-cta-btn-link">
              <Button className="shared-cta-btn" size="lg" data-testid="shared-cta-btn">
                <Sparkles size={16} /> Start Building — It's Free
              </Button>
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="shared-footer">
        <span>Powered by <strong>Hyt Orbis World Builder</strong></span>
        <a href="https://hytorbisworldbuilder.com">hytorbisworldbuilder.com</a>
      </footer>
    </div>
  );
}

function MiniMapCanvas({ miniMap }) {
  const { zones, w, h, cellSize } = miniMap;
  const canvasW = w * cellSize;
  const canvasH = h * cellSize;

  return (
    <svg width={canvasW} height={canvasH} viewBox={`0 0 ${canvasW} ${canvasH}`} className="shared-mini-map">
      <rect width={canvasW} height={canvasH} fill="#0f1729" rx={8} />
      {zones.map((z, i) => {
        const config = ZONE_CONFIG[z.type];
        return (
          <rect
            key={i}
            x={z.x * cellSize}
            y={z.y * cellSize}
            width={cellSize}
            height={cellSize}
            fill={config?.color || "#4B5563"}
            opacity={0.85}
          />
        );
      })}
    </svg>
  );
}
