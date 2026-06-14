import { createContext } from "react";

export type Message = {
    role: "user" | "assistant";
    content: string;
};

export type AIContextType = {
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
    clientContext: {
        contextName: string | null;
        metadata: any;
    };
    updateClientContext: (contextName: string | null, metadata: any) => void;
};

export const AIContext = createContext<AIContextType | undefined>(undefined);

