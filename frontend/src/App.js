import "@/App.css";
import { AppProvider, useApp } from "@/contexts/AppContext";
import { Header } from "@/components/app/Header";
import { Sidebar } from "@/components/app/Sidebar";
import { AIPanel } from "@/components/app/AIPanel";
import { MapArea } from "@/components/app/MapArea";
import { AppDialogs } from "@/components/app/Dialogs";
import { CollabChat } from "@/components/app/CollabChat";

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

  return (
    <div className="app-container">
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
