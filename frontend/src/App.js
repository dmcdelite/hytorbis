import "@/App.css";
import { AppProvider, useApp } from "@/contexts/AppContext";
import { Header } from "@/components/app/Header";
import { Sidebar } from "@/components/app/Sidebar";
import { AIPanel } from "@/components/app/AIPanel";
import { MapArea } from "@/components/app/MapArea";
import { AppDialogs } from "@/components/app/Dialogs";
import { CollabChat } from "@/components/app/CollabChat";
import { useEffect, useRef } from "react";

const DESIGN_WIDTH = 1440;

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

function AppContent() {
  const ctx = useApp();
  const mobileSidebar = ctx.mobileSidebarOpen;
  const mobileAi = ctx.mobileAiPanelOpen;
  const anyOpen = mobileSidebar || mobileAi;
  const containerRef = useRef(null);

  useEffect(() => {
    const scaleApp = () => {
      const el = containerRef.current;
      if (!el) return;
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      if (vw >= DESIGN_WIDTH) {
        el.style.transform = "none";
        el.style.width = "100vw";
        el.style.height = "100vh";
      } else {
        const scale = vw / DESIGN_WIDTH;
        el.style.transform = `scale(${scale})`;
        el.style.transformOrigin = "top left";
        el.style.width = `${DESIGN_WIDTH}px`;
        el.style.height = `${vh / scale}px`;
      }
    };
    scaleApp();
    window.addEventListener("resize", scaleApp);
    return () => window.removeEventListener("resize", scaleApp);
  }, []);

  return (
    <div className="app-container" ref={containerRef}>
      <Header />
      <div className="main-content">
        <div className={`sidebar-left-wrapper${mobileSidebar ? " mobile-open" : ""}`}>
          <Sidebar />
        </div>
        <MapArea />
        <div className={`sidebar-right-wrapper${mobileAi ? " mobile-open" : ""}`}>
          <AIPanel />
        </div>
      </div>
      {anyOpen && <div className={`mobile-overlay${anyOpen ? " visible" : ""}`} onClick={() => { ctx.setMobileSidebarOpen(false); ctx.setMobileAiPanelOpen(false); }} />}
      <AppDialogs />
      <CollabChat />
    </div>
  );
}

export default App;
