import { useState, ReactNode } from "react";
import { api, API_BASE } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { AIContext, Message } from './AIContextInstance';

const parseQasm = (qasm: string) => {
    const lines = qasm.split('\n');
    const actions: { action: string; params: any }[] = [];
    
    // Always clear first
    actions.push({ action: 'clear', params: {} });
    
    for (let line of lines) {
        line = line.trim().replace(/;$/, '');
        if (!line || line.startsWith('OPENQASM') || line.startsWith('include') || line.startsWith('qreg') || line.startsWith('creg') || line.startsWith('//') || line.startsWith('barrier')) {
            continue;
        }
        
        // Skip measure gates as they are simulated automatically
        if (line.startsWith('measure')) {
            continue;
        }
        
        // Match 1-qubit gates, e.g. "h q[0]" or "x q[1]"
        const oneQubitMatch = line.match(/^([a-z0-9]+)\s+q\[(\d+)\]$/i);
        if (oneQubitMatch) {
            const gate = oneQubitMatch[1].toLowerCase();
            const qubit = parseInt(oneQubitMatch[2], 10);
            actions.push({
                action: 'add_gate',
                params: { gate, qubit }
            });
            continue;
        }
        
        // Match 2-qubit gates, e.g. "cx q[0],q[1]"
        const twoQubitMatch = line.match(/^([a-z0-9]+)\s+q\[(\d+)\]\s*,\s*q\[(\d+)\]$/i);
        if (twoQubitMatch) {
            const gate = twoQubitMatch[1].toLowerCase();
            const control = parseInt(twoQubitMatch[2], 10);
            const target = parseInt(twoQubitMatch[3], 10);
            actions.push({
                action: 'add_gate',
                params: { gate, control, target }
            });
            continue;
        }
    }
    
    // Always run at the end
    actions.push({ action: 'run', params: {} });
    return actions;
};

export const AIProvider = ({ children }: { children: ReactNode }) => {
    const { user } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [activeTool, setActiveTool] = useState<"quantum-states" | "circuit-builder" | null>(null);
    const [circuitActions, setCircuitActions] = useState<{ id: string; action: string; params: any }[]>([]);
    const [visualizerActions, setVisualizerActions] = useState<{ id: string; gate: string }[]>([]);

    const toggleChat = () => setIsOpen(!isOpen);

    const closeTool = () => setActiveTool(null);

    const ackCircuitAction = (id: string) => {
        setCircuitActions(prev => prev.filter(a => a.id !== id));
    };

    const ackVisualizerAction = (id: string) => {
        setVisualizerActions(prev => prev.filter(a => a.id !== id));
    };

    const sendMessage = async (content: string) => {
        // Optimistic update
        const userMsg: Message = { role: "user", content };
        setMessages(prev => [...prev, userMsg]);
        setIsLoading(true);

        if (!user) {
            setMessages(prev => [...prev, {
                role: "assistant",
                content: "Please login first to use the Assistant. You can find the login button in the top right corner."
            }]);
            setIsLoading(false);
            return;
        }

        try {
            const token = api.getAuthToken();
            const conversationId = localStorage.getItem('tutor_conversation_id') || null;

            const response = await fetch(`${API_BASE}/tutor/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: content,
                    conversation_id: conversationId,
                    current_route: window.location.pathname
                }),
            });

            if (response.status === 401) {
                setMessages(prev => [...prev, {
                    role: "assistant",
                    content: "Your session has expired. Please log in again."
                }]);
                setIsLoading(false);
                return;
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Failed to send message");
            }

            const data = await response.json();
            
            if (data.conversation_id) {
                localStorage.setItem('tutor_conversation_id', data.conversation_id);
            }

            setMessages(prev => [...prev, { role: "assistant", content: data.response }]);

            if (data.intent === "simulation_request" || data.intent === "build_circuit" || data.intent === "simulate") {
                // Extract QASM code
                const qasmRegex = /```qasm\s*([\s\S]*?)\s*```/i;
                const match = data.response.match(qasmRegex);
                let qasmCode = "";
                if (match) {
                    qasmCode = match[1];
                } else if (data.response.includes("OPENQASM")) {
                    const openqasmIndex = data.response.indexOf("OPENQASM");
                    qasmCode = data.response.substring(openqasmIndex);
                }

                if (qasmCode) {
                    // Open the circuit builder tool
                    handleToolCall("open_tool", { tool_name: "circuit-builder" });
                    
                    // Parse QASM lines
                    const parsedActions = parseQasm(qasmCode);
                    
                    // Enqueue actions
                    setCircuitActions(parsedActions.map(act => ({
                        id: Math.random().toString(36).substring(7),
                        action: act.action,
                        params: act.params
                    })));
                } else {
                    handleToolCall("open_tool", { tool_name: "circuit-builder" });
                }
            } else if (data.intent === "interactive_states") {
                handleToolCall("open_tool", { tool_name: "quantum-states" });
            }

        } catch (error: any) {
            console.error(error);
            setMessages(prev => [...prev, {
                role: "assistant",
                content: error.message === "Failed to fetch"
                    ? "I'm having trouble reaching the quantum backend. Please ensure the server is running."
                    : `Error: ${error.message}`
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
