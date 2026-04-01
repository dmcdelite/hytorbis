import "@/App.css";
import { AppProvider } from "@/contexts/AppContext";
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
  return (
    <div className="app-container">
      <Header />
      <div className="main-content">
        <Sidebar />
        <MapArea />
        <AIPanel />
      </div>
      <AppDialogs />
      <CollabChat />
    </div>
  );
}

export default App;
