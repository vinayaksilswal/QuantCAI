import { useState, useEffect, useCallback, ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { api, API_BASE } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { AIContext, Message, ActionButton } from './AIContextInstance';

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
    const location = useLocation();
    const [isOpen, setIsOpen] = useState<boolean>(() => {
        if (typeof window !== "undefined") {
            return localStorage.getItem("quantai_chat_open") === "true";
        }
        return false;
    });
    const [messages, setMessages] = useState<Message[]>(() => {
        if (typeof window !== "undefined") {
            const saved = localStorage.getItem("quantai_chat_messages");
            return saved ? JSON.parse(saved) : [];
        }
        return [];
    });
    const [isLoading, setIsLoading] = useState(false);
    const [activeTool, setActiveTool] = useState<"quantum-states" | "circuit-builder" | "pqc-scanner" | null>(null);
    const [circuitActions, setCircuitActions] = useState<{ id: string; action: string; params: any }[]>([]);
    const [visualizerActions, setVisualizerActions] = useState<{ id: string; gate: string }[]>([]);
    const [clientContext, setClientContext] = useState<{ contextName: string | null; metadata: any }>({
        contextName: null,
        metadata: {}
    });
    const [dynamicSuggestions, setDynamicSuggestions] = useState<string[]>([]);
    const [welcomeMessage, setWelcomeMessage] = useState<string>("");

    useEffect(() => {
        localStorage.setItem("quantai_chat_open", String(isOpen));
    }, [isOpen]);

    useEffect(() => {
        localStorage.setItem("quantai_chat_messages", JSON.stringify(messages));
    }, [messages]);

    // Auto-detect context from route changes
    useEffect(() => {
        const path = location.pathname;
        let contextName: string | null = null;

        if (path.startsWith("/learn") || path.startsWith("/quantum-computing")) {
            contextName = "learn";
        } else if (path.startsWith("/circuit-builder")) {
            contextName = "circuit-builder";
        } else if (path.startsWith("/quantum-simulator") || path.startsWith("/sandbox")) {
            contextName = "qasm-ide";
        } else if (path.startsWith("/quantum-states")) {
            contextName = "quantum-states";
        } else if (path.startsWith("/pqc-scanner") || path.startsWith("/repo-scanner")) {
            contextName = "pqc-scanner";
        } else if (path.startsWith("/enterprise")) {
            contextName = "enterprise";
        } else if (path.startsWith("/tools")) {
            contextName = "tools";
        }

        setClientContext(prev => {
            const newMeta = { ...prev.metadata, current_route: path };
            return { contextName, metadata: newMeta };
        });
    }, [location.pathname]);

    const toggleChat = () => setIsOpen(!isOpen);

    const closeTool = () => setActiveTool(null);

    const ackCircuitAction = (id: string) => {
        setCircuitActions(prev => prev.filter(a => a.id !== id));
    };

    const ackVisualizerAction = (id: string) => {
        setVisualizerActions(prev => prev.filter(a => a.id !== id));
    };

    const updateClientContext = useCallback((contextName: string | null, metadata: any) => {
        setClientContext(prev => {
            if (prev.contextName === contextName) {
                // Shallow equality check
                const prevKeys = Object.keys(prev.metadata || {});
                const nextKeys = Object.keys(metadata || {});
                let isMetadataEqual = prevKeys.length === nextKeys.length;
                if (isMetadataEqual) {
                    for (const key of prevKeys) {
                        if (prev.metadata[key] !== metadata[key]) {
                            isMetadataEqual = false;
                            break;
                        }
                    }
                }
                if (isMetadataEqual) return prev;
            }
            return { contextName, metadata: { ...metadata, current_route: location.pathname } };
        });
    }, [location.pathname]);

    const sendMessage = async (content: string) => {
        // Optimistic update
        const userMsg: Message = { role: "user", content };
        const updatedMessages = [...messages, userMsg];
        setMessages(updatedMessages);
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

            const response = await fetch(`${API_BASE}/api/v1/quantai/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: content,
                    conversation_id: conversationId,
                    context: clientContext.contextName,
                    client_context: clientContext.metadata,
                    current_route: location.pathname,
                }),
            });

            if (response.status === 402) {
                setMessages(prev => [...prev, {
                    role: "assistant",
                    content: "⚠️ **Payment Required**: Insufficient wallet balance. Please add credits to your wallet in the Developer Console to continue."
                }]);
                setIsLoading(false);
                return;
            }

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

            // Read streaming response
            const reader = response.body?.getReader();
            const decoder = new TextDecoder("utf-8");
            let assistantContent = "";

            setMessages(prev => [...prev, { role: "assistant", content: "" }]);

            if (reader) {
                let buffer = "";
                while (true) {
                    const { value, done } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split("\n");
                    // Keep the last part of split if it is incomplete
                    buffer = lines.pop() || "";

                    for (const line of lines) {
                        const cleanLine = line.trim();
                        if (cleanLine.startsWith("data: ")) {
                            try {
                                const payloadStr = cleanLine.substring(6);
                                if (payloadStr === "[DONE]") continue;

                                const data = JSON.parse(payloadStr);
                                if (data.type === "text") {
                                    assistantContent += data.content;
                                    setMessages(prev => {
                                        const next = [...prev];
                                        if (next.length > 0) {
                                            next[next.length - 1] = {
                                                role: "assistant",
                                                content: assistantContent
                                            };
                                        }
                                        return next;
                                    });
                                } else if (data.type === "tool_call") {
                                    handleToolCall(data.name, data.args);
                                } else if (data.type === "meta") {
                                    if (data.conversation_id) {
                                        localStorage.setItem('tutor_conversation_id', data.conversation_id);
                                    }
                                    // Update dynamic suggestions from backend
                                    if (data.suggestions) {
                                        setDynamicSuggestions(data.suggestions);
                                    }
                                    if (data.welcome_message) {
                                        setWelcomeMessage(data.welcome_message);
                                    }
                                } else if (data.conversation_id) {
                                    localStorage.setItem('tutor_conversation_id', data.conversation_id);
                                }
                            } catch (e) {
                                // Ignore parsing errors for incomplete JSON
                            }
                        }
                    }
                }
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
            if (tool === "quantum-states" || tool === "circuit-builder" || tool === "pqc-scanner") {
                setActiveTool(tool);
            }
        } else if (name === "manage_circuit") {
            const id = Math.random().toString(36).substring(7);
            setCircuitActions(prev => [...prev, { id, action: args.action, params: args.params }]);
        } else if (name === "navigate_to_page") {
            const path = args.path || "/";
            const section = args.section || "";
            window.dispatchEvent(new CustomEvent("ai-navigate", { detail: { path, section } }));
        } else if (name === "navigate_to_learn") {
            // Legacy support
            window.dispatchEvent(new CustomEvent("ai-navigate", { detail: { path: "/learn", section: args.section } }));
        } else if (name === "suggest_learning_path") {
            // Show as a contextual message with navigation action
            const topic = args.current_topic || "";
            window.dispatchEvent(new CustomEvent("ai-learning-path", { detail: { currentTopic: topic } }));
        } else if (name === "explain_quiz_hint") {
            // The AI response already contains the hint — this is for tracking
            console.log("Quiz hint requested for:", args.page, "q:", args.question_index);
        } else if (name === "show_circuit_template") {
            window.dispatchEvent(new CustomEvent("ai-load-template", { detail: { templateName: args.template_name } }));
            // Also navigate to circuit builder if not already there
            if (!location.pathname.startsWith("/circuit-builder")) {
                window.dispatchEvent(new CustomEvent("ai-navigate", { detail: { path: "/circuit-builder" } }));
            }
        } else if (name === "start_tutorial") {
            window.dispatchEvent(new CustomEvent("ai-start-tutorial", { detail: { tutorialId: args.tutorial_id } }));
        } else if (name === "apply_gate_to_visualizer") {
            const id = Math.random().toString(36).substring(7);
            setVisualizerActions(prev => [...prev, { id, gate: args.gate }]);
        } else if (name === "run_pqc_scan") {
            window.dispatchEvent(new CustomEvent("ai-run-pqc", { detail: { target: args.target_url } }));
            // Navigate to scanner if not there
            if (!location.pathname.startsWith("/pqc-scanner")) {
                window.dispatchEvent(new CustomEvent("ai-navigate", { detail: { path: "/pqc-scanner" } }));
            }
        } else if (name === "recommend_enterprise_action") {
            const actionType = args.action_type;
            if (actionType === "email") {
                // Append an action button to the last assistant message
                setMessages(prev => {
                    const next = [...prev];
                    const lastMsg = next[next.length - 1];
                    if (lastMsg && lastMsg.role === "assistant") {
                        lastMsg.actions = [
                            ...(lastMsg.actions || []),
                            {
                                label: "📧 Email Enterprise Team",
                                type: "email",
                                email: "quantc.info@gmail.com",
                                subject: "QuantCAI Enterprise Inquiry",
                            }
                        ];
                    }
                    return next;
                });
            } else if (actionType === "demo") {
                setMessages(prev => {
                    const next = [...prev];
                    const lastMsg = next[next.length - 1];
                    if (lastMsg && lastMsg.role === "assistant") {
                        lastMsg.actions = [
                            ...(lastMsg.actions || []),
                            {
                                label: "🎯 Request Custom Demo",
                                type: "navigate",
                                path: "/enterprise",
                            }
                        ];
                    }
                    return next;
                });
            } else if (actionType === "register_org") {
                setMessages(prev => {
                    const next = [...prev];
                    const lastMsg = next[next.length - 1];
                    if (lastMsg && lastMsg.role === "assistant") {
                        lastMsg.actions = [
                            ...(lastMsg.actions || []),
                            {
                                label: "🏢 Register Organization",
                                type: "navigate",
                                path: "/signup?plan=enterprise",
                            }
                        ];
                    }
                    return next;
                });
            } else if (actionType === "cli_info") {
                setMessages(prev => {
                    const next = [...prev];
                    const lastMsg = next[next.length - 1];
                    if (lastMsg && lastMsg.role === "assistant") {
                        lastMsg.actions = [
                            ...(lastMsg.actions || []),
                            {
                                label: "📧 Get CLI Scanner License",
                                type: "email",
                                email: "quantc.info@gmail.com",
                                subject: "QuantCAI CLI Scanner License Request",
                            },
                            {
                                label: "🏢 Enterprise Details",
                                type: "navigate",
                                path: "/enterprise",
                            }
                        ];
                    }
                    return next;
                });
            }
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
            ackVisualizerAction,
            clientContext,
            updateClientContext,
            dynamicSuggestions,
            welcomeMessage,
        }}>
            {children}
        </AIContext.Provider>
    );
};

// useAI moved to @/hooks/useAI.ts
