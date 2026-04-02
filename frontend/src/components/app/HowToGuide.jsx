import { useState, useEffect } from "react";
import { useApp } from "@/contexts/AppContext";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Map, Wand2, Users, Download, Crown, Zap, Sparkles, ChevronLeft, ChevronRight, Rocket } from "lucide-react";

const STEPS = [
  {
    icon: Rocket,
    title: "Welcome to Hyt Orbis",
    color: "#10b981",
    content: (
      <>
        <p>Build stunning 2D game worlds with an intuitive editor, AI assistance, and real-time collaboration.</p>
        <p>This quick guide will walk you through the key features. Let's get started!</p>
      </>
    ),
  },
  {
    icon: Map,
    title: "Creating Worlds",
    color: "#3b82f6",
    content: (
      <>
        <p><strong>Create a new world</strong> from the left sidebar using the + button. Choose a map size (up to 512x512) and seed.</p>
        <p><strong>Paint terrain</strong> by selecting a zone type and clicking/dragging on the map. Use the tools panel to switch between brush sizes.</p>
        <p><strong>Place prefabs</strong> like trees, buildings, and structures by selecting from the prefab palette and clicking on the map.</p>
      </>
    ),
  },
  {
    icon: Wand2,
    title: "AI World Generation",
    color: "#8b5cf6",
    content: (
      <>
        <p><strong>AI Chat</strong> — Open the AI panel on the right and describe what you want. The AI will suggest terrain layouts, zone placement, and prefab ideas.</p>
        <p><strong>Auto-Generate</strong> — Click the wand icon and describe your world in plain text. The AI builds the entire world for you.</p>
        <p>Choose between GPT-5.2, Claude, or Gemini as your AI provider.</p>
        <div className="howto-badge-row">
          <span className="howto-badge howto-badge-premium"><Crown size={12} /> Creator / Developer Plan</span>
        </div>
      </>
    ),
  },
  {
    icon: Users,
    title: "Collaboration",
    color: "#f59e0b",
    content: (
      <>
        <p><strong>Invite collaborators</strong> to edit your world in real-time. Share the collaboration link from the header.</p>
        <p><strong>Live chat</strong> with collaborators while building together. See each other's cursors and edits instantly.</p>
        <p><strong>Gallery</strong> — Publish your world to the community gallery for others to explore, like, and fork.</p>
        <div className="howto-badge-row">
          <span className="howto-badge howto-badge-premium"><Crown size={12} /> Creator / Developer Plan</span>
        </div>
      </>
    ),
  },
  {
    icon: Download,
    title: "Export & Install",
    color: "#ef4444",
    content: (
      <>
        <p><strong>Export formats:</strong> JSON, Hytale config, Prefab, and JAR mod package.</p>
        <p><strong>Install to Game</strong> — Generate a complete install package (ZIP) with your world files and step-by-step instructions. Just extract and drop into your game folder.</p>
        <p><strong>Version history</strong> — Save snapshots of your world and restore any previous version.</p>
        <div className="howto-badge-row">
          <span className="howto-badge howto-badge-premium"><Crown size={12} /> Install to Game: Creator / Developer Plan</span>
        </div>
      </>
    ),
  },
  {
    icon: Crown,
    title: "Upgrade Your Plan",
    color: "#f59e0b",
    content: (
      <>
        <div className="howto-plans">
          <div className="howto-plan">
            <div className="howto-plan-header">
              <Zap size={20} style={{ color: "#9ca3af" }} />
              <span>Explorer (Free)</span>
            </div>
            <ul>
              <li>5 worlds, 128x128 max</li>
              <li>JSON & Prefab exports</li>
              <li>Community gallery</li>
            </ul>
          </div>
          <div className="howto-plan howto-plan-highlight">
            <div className="howto-plan-header">
              <Sparkles size={20} style={{ color: "#10b981" }} />
              <span>Creator ($9/mo)</span>
            </div>
            <ul>
              <li>Unlimited worlds, 512x512</li>
              <li>AI generation</li>
              <li>Real-time collaboration</li>
              <li>Install to Game</li>
            </ul>
          </div>
          <div className="howto-plan">
            <div className="howto-plan-header">
              <Crown size={20} style={{ color: "#f59e0b" }} />
              <span>Developer ($29/mo)</span>
            </div>
            <ul>
              <li>Everything in Creator</li>
              <li>Analytics dashboard</li>
              <li>Priority support</li>
            </ul>
          </div>
        </div>
      </>
    ),
  },
];

export function HowToGuide() {
  const ctx = useApp();
  const [step, setStep] = useState(0);
  const [dontShow, setDontShow] = useState(false);
  const [open, setOpen] = useState(false);

  // Show on first visit (check localStorage)
  useEffect(() => {
    if (ctx.currentUser) {
      const dismissed = localStorage.getItem("howto_dismissed");
      if (!dismissed) {
        setOpen(true);
        setStep(0);
      }
    }
  }, [ctx.currentUser]);

  // Also allow manual open from context
  useEffect(() => {
    if (ctx.showHowToDialog) {
      setOpen(true);
      setStep(0);
    }
  }, [ctx.showHowToDialog]);

  const handleClose = (val) => {
    setOpen(val);
    if (!val) {
      ctx.setShowHowToDialog(false);
      if (dontShow) {
        localStorage.setItem("howto_dismissed", "true");
      }
    }
  };

  const current = STEPS[step];
  const Icon = current.icon;
  const isLast = step === STEPS.length - 1;
  const isFirst = step === 0;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="howto-dialog" data-testid="howto-dialog">
        <DialogHeader>
          <DialogTitle className="sr-only">How to Use Hyt Orbis</DialogTitle>
          <DialogDescription className="sr-only">Step-by-step guide to using the world builder</DialogDescription>
        </DialogHeader>

        <div className="howto-step-indicator">
          {STEPS.map((_, i) => (
            <button
              key={i}
              className={`howto-dot ${i === step ? "active" : ""} ${i < step ? "done" : ""}`}
              onClick={() => setStep(i)}
              data-testid={`howto-dot-${i}`}
            />
          ))}
        </div>

        <div className="howto-body">
          <div className="howto-icon-wrap" style={{ background: `${current.color}15`, color: current.color }}>
            <Icon size={36} />
          </div>
          <h2 className="howto-title">{current.title}</h2>
          <div className="howto-content">{current.content}</div>
        </div>

        <div className="howto-footer">
          <div className="howto-checkbox-row">
            <Checkbox
              id="howto-dismiss"
              checked={dontShow}
              onCheckedChange={setDontShow}
              data-testid="howto-dismiss-checkbox"
            />
            <label htmlFor="howto-dismiss" className="howto-dismiss-label">Don't show this again</label>
          </div>

          <div className="howto-nav">
            {!isFirst && (
              <Button variant="ghost" size="sm" onClick={() => setStep(s => s - 1)} data-testid="howto-prev">
                <ChevronLeft size={16} /> Back
              </Button>
            )}
            {isLast ? (
              <Button size="sm" onClick={() => handleClose(false)} className="howto-done-btn" data-testid="howto-done">
                Get Started
              </Button>
            ) : (
              <Button size="sm" onClick={() => setStep(s => s + 1)} className="howto-next-btn" data-testid="howto-next">
                Next <ChevronRight size={16} />
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
