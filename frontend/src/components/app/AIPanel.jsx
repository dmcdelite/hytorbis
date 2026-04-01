import { useApp } from "@/contexts/AppContext";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Bot, Loader2, Send } from "lucide-react";

export function AIPanel() {
  const ctx = useApp();
  if (!ctx.aiPanelOpen) return null;

  return (
    <aside className="sidebar-right" data-testid="ai-panel">
      <div className="ai-header">
        <div className="ai-title">
          <img src="https://images.unsplash.com/photo-1641380184601-06e153dec2fc?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2OTF8MHwxfHNlYXJjaHwyfHxnbG93aW5nJTIwcnVuZSUyMG1hZ2ljfGVufDB8fHx8MTc3NTA3NzMyM3ww&ixlib=rb-4.1.0&q=85" alt="AI" className="ai-avatar" />
          <span>World Architect AI</span>
        </div>
        <Select value={ctx.aiProvider} onValueChange={ctx.setAiProvider}>
          <SelectTrigger className="ai-provider-select" data-testid="ai-provider-select"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="openai">GPT-5.2</SelectItem>
            <SelectItem value="anthropic">Claude</SelectItem>
            <SelectItem value="gemini">Gemini</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <ScrollArea className="ai-messages">
        {ctx.aiMessages.length === 0 ? (
          <div className="ai-welcome">
            <Bot size={32} className="ai-welcome-icon" />
            <p>I can help you design your world!</p>
            <p className="text-muted">Ask for suggestions or use AI Auto-Generate for full map population.</p>
          </div>
        ) : (
          ctx.aiMessages.map((msg, i) => (
            <div key={i} className={`ai-message ${msg.role}`}>
              <div className="ai-message-content">{msg.content}</div>
            </div>
          ))
        )}
        {ctx.aiLoading && (
          <div className="ai-message assistant">
            <div className="ai-message-content"><Loader2 className="animate-spin" size={16} /><span>Thinking...</span></div>
          </div>
        )}
      </ScrollArea>

      <div className="ai-input-area">
        <Textarea
          value={ctx.aiInput}
          onChange={(e) => ctx.setAiInput(e.target.value)}
          placeholder={ctx.currentWorld ? "Ask for suggestions..." : "Create a world first"}
          disabled={!ctx.currentWorld || ctx.aiLoading}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ctx.sendAiMessage(); } }}
          data-testid="ai-input"
        />
        <Button onClick={ctx.sendAiMessage} disabled={!ctx.currentWorld || !ctx.aiInput.trim() || ctx.aiLoading} className="ai-send-btn" data-testid="ai-send-btn">
          <Send size={16} />
        </Button>
      </div>
    </aside>
  );
}
