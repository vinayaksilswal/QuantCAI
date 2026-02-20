import { createContext, useState, ReactNode } from "react";


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
    activeTool: "quantum-states" | "circuit-builder" | null;
    closeTool: () => void;
    circuitActions: { id: string; action: string; params: any }[];
    ackCircuitAction: (id: string) => void;
    visualizerActions: { id: string; gate: string }[];
    ackVisualizerAction: (id: string) => void;
};

export const AIContext = createContext<AIContextType | undefined>(undefined);

export const AIProvider = ({ children }: { children: ReactNode }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [activeTool, setActiveTool] = useState<"quantum-states" | "circuit-builder" | null>(null);
    const [circuitActions, setCircuitActions] = useState<{ id: string; action: string; params: any }[]>([]);
    const [visualizerActions, setVisualizerActions] = useState<{ id: string; gate: string }[]>([]);


    // const { token } = useAuth(); 

    const toggleChat = () => setIsOpen(!isOpen);

    const closeTool = () => setActiveTool(null);

    const ackCircuitAction = (id: string) => {
        setCircuitActions(prev => prev.filter(a => a.id !== id));
    };

    const ackVisualizerAction = (id: string) => {
        setVisualizerActions(prev => prev.filter(a => a.id !== id));
    };

    const sendMessage = async (content: string) => {
        const token = localStorage.getItem("auth_token");

        // Optimistic update
        const userMsg: Message = { role: "user", content };
        setMessages(prev => [...prev, userMsg]);
        setIsLoading(true);

        if (!token) {
            setMessages(prev => [...prev, {
                role: "assistant",
                content: "Please login first to use the QuantAI Assistant. You can find the login button in the top right corner."
            }]);
            setIsLoading(false);
            return;
        }

        try {
            const historyPayload = messages.map(m => ({ role: m.role, content: m.content }));

            const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ message: content, history: historyPayload }),
            });

            if (response.status === 401) {
                setMessages(prev => [...prev, {
                    role: "assistant",
                    content: "Your session has expired. Please log in again."
                }]);
                return;
            }

            if (!response.ok) throw new Error("Failed to send message");

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            if (!reader) throw new Error("No reader");

            let done = false;
            let currentAiMessage = "";

            // Add initial empty AI message
            setMessages(prev => [...prev, { role: "assistant", content: "" }]);

            while (!done) {
                const { value, done: doneReading } = await reader.read();
                done = doneReading;
                if (value) {
                    const chunkValue = decoder.decode(value);

                    // Parse potential multiple data packets in one chunk
                    const lines = chunkValue.split("\n");
                    for (const line of lines) {
                        if (line.startsWith("data: ")) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                if (data.type === "text") {
                                    currentAiMessage += data.content;
                                    setMessages(prev => {
                                        const next = [...prev];
                                        const last = next[next.length - 1];
                                        if (last && last.role === "assistant") {
                                            last.content = currentAiMessage;
                                        }
                                        return next;
                                    });
                                } else if (data.type === "tool_call") {
                                    const { name, args } = data;
                                    handleToolCall(name, args);
                                }
                            } catch (e) {
                                console.error("Failed to parse stream packet", e, line);
                            }
                        }
                    }
                }
            }

        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, {
                role: "assistant",
                content: "I'm having trouble reaching the quantum backend. Please ensure the server is running or try again in 1 or 2 minutes."
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleToolCall = (name: string, args: any) => {
        console.log("AI Tool Call:", name, args);
        if (name === "open_tool") {
            const tool = args.tool_name;
            if (tool === "quantum-states" || tool === "circuit-builder") {
                setActiveTool(tool);
            }
        } else if (name === "manage_circuit") {
            const id = Math.random().toString(36).substring(7);
            setCircuitActions(prev => [...prev, { id, action: args.action, params: args.params }]);
        } else if (name === "navigate_to_learn") {
            window.dispatchEvent(new CustomEvent("ai-navigate", { detail: { path: "/learn", section: args.section } }));
        } else if (name === "start_tutorial") {
            window.dispatchEvent(new CustomEvent("ai-start-tutorial", { detail: { tutorialId: args.tutorial_id } }));
        } else if (name === "apply_gate_to_visualizer") {
            const id = Math.random().toString(36).substring(7);
            setVisualizerActions(prev => [...prev, { id, gate: args.gate }]);
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
            circuitActions,
            ackCircuitAction,
            visualizerActions,
            ackVisualizerAction
        }}>
            {children}
        </AIContext.Provider>
    );
};

// useAI moved to @/hooks/useAI.ts
