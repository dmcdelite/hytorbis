import { useApp } from "@/contexts/AppContext";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare } from "lucide-react";

export function CollabChat() {
  const ctx = useApp();
  if (!ctx.collabEnabled || !ctx.wsConnected) return null;

  return (
    <div className="collab-chat-panel">
      <div className="collab-chat-header">
        <MessageSquare size={14} />
        <span>Team Chat</span>
        <Badge variant="secondary">{ctx.collabUsers.length}</Badge>
      </div>
      <ScrollArea className="collab-chat-messages">
        {ctx.collabChat.map((msg, i) => (
          <div key={i} className="chat-msg">
            <span className="chat-user">{msg.user.slice(0, 8)}:</span>
            <span>{msg.message}</span>
          </div>
        ))}
      </ScrollArea>
      <Input
        placeholder="Type a message..."
        onKeyDown={(e) => {
          if (e.key === "Enter" && e.target.value) {
            ctx.sendWsMessage("chat", { message: e.target.value });
            ctx.collabChat.push({ user: ctx.userId, message: e.target.value });
            e.target.value = "";
          }
        }}
      />
    </div>
  );
}
