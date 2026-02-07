import { createContext, useContext, useState, ReactNode } from "react";
import { useAuth } from "./AuthContext";

type Message = {
    role: "user" | "assistant";
    content: string;
};

type AIContextType = {
    isOpen: boolean;
    toggleChat: () => void;
    messages: Message[];
    sendMessage: (message: string) => Promise<void>;
    isLoading: boolean;
    activeTool: "quantum-state" | "circuit-builder" | null;
    closeTool: () => void;
    circuitAction: { action: string; params: any } | null;
    ackCircuitAction: () => void;
};

const AIContext = createContext<AIContextType | undefined>(undefined);

export const AIProvider = ({ children }: { children: ReactNode }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [activeTool, setActiveTool] = useState<"quantum-state" | "circuit-builder" | null>(null);
    const [circuitAction, setCircuitAction] = useState<{ action: string; params: any } | null>(null);


    // const { token } = useAuth(); 

    const toggleChat = () => setIsOpen(!isOpen);

    const closeTool = () => setActiveTool(null);

    const ackCircuitAction = () => setCircuitAction(null);

    const sendMessage = async (content: string) => {
        // Optimistic update
        const newHistory = [...messages, { role: "user" as const, content }];
        setMessages(newHistory);
        setIsLoading(true);

        try {
            // Prepare history for backend (excluding local-only messages ideally, but for now sending all)
            const historyPayload = messages.map(m => ({ role: m.role, content: m.content }));

            const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("auth_token")}` // or use token from context
                },
                body: JSON.stringify({ message: content, history: historyPayload }),
            });

            if (!response.ok) {
                throw new Error("Failed to send message");
            }

            const data = await response.json();
            const aiResponse = data.response;

            // Parse tool calls from response
            // Expected format: "TOOL_OPEN:quantum-state" or "CIRCUIT_ACTION:{...}" or plain text
            // Note: The LLM might return mixture. For now handling strict prefixes or simple text.
            // A more robust parser would handle "Sure, opening it now. TOOL_OPEN:..."

            let cleanResponse = aiResponse;

            if (aiResponse.includes("TOOL_OPEN:")) {
                const parts = aiResponse.split("TOOL_OPEN:");
                const toolName = parts[1].trim().split(" ")[0]; // basic extraction
                if (toolName.includes("quantum-state")) setActiveTool("quantum-state");
                if (toolName.includes("circuit-builder")) setActiveTool("circuit-builder");
                // Remove the command specifically if we want to hide it, or just leave it.
                // Let's leave it for now or clean it up if it's just the command.
                if (parts[0].trim() === "") cleanResponse = "Opening " + toolName + "...";
            }

            if (aiResponse.includes("CIRCUIT_ACTION:")) {
                const parts = aiResponse.split("CIRCUIT_ACTION:");
                try {
                    const actionJson = JSON.parse(parts[1].trim());
                    setCircuitAction(actionJson);
                    if (parts[0].trim() === "") cleanResponse = "Executing circuit action...";
                } catch (e) {
                    console.error("Failed to parse circuit action", e);
                }
            }

            setMessages(prev => [...prev, { role: "assistant", content: cleanResponse }]);
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error. Please try again." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <AIContext.Provider value={{
            isOpen,
            toggleChat,
            messages,
            sendMessage,
            isLoading,
            activeTool,
            closeTool,
            circuitAction,
            ackCircuitAction
        }}>
            {children}
        </AIContext.Provider>
    );
};

export const useAI = () => {
    const context = useContext(AIContext);
    if (context === undefined) {
        throw new Error("useAI must be used within an AIProvider");
    }
    return context;
};
