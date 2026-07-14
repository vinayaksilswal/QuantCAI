import { createContext } from "react";

export type Message = {
    role: "user" | "assistant";
    content: string;
    // Rich response metadata for inline action buttons
    actions?: ActionButton[];
};

export type ActionButton = {
    label: string;
    type: "navigate" | "email" | "tool" | "upgrade";
    path?: string;
    email?: string;
    subject?: string;
    toolName?: string;
    icon?: string;
};

export type AIContextType = {
    isOpen: boolean;
    toggleChat: () => void;
    messages: Message[];
    sendMessage: (message: string) => Promise<void>;
    isLoading: boolean;
    activeTool: "quantum-states" | "circuit-builder" | "pqc-scanner" | null;
    closeTool: () => void;
    circuitActions: { id: string; action: string; params: any }[];
    ackCircuitAction: (id: string) => void;
    visualizerActions: { id: string; gate: string }[];
    ackVisualizerAction: (id: string) => void;
    clientContext: {
        contextName: string | null;
        metadata: any;
    };
    updateClientContext: (contextName: string | null, metadata: any) => void;
    // Enterprise-grade additions
    dynamicSuggestions: string[];
    welcomeMessage: string;
};

export const AIContext = createContext<AIContextType | undefined>(undefined);
