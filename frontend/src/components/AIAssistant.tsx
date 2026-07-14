import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAI } from "../hooks/useAI";
import { useAuth } from "../hooks/useAuth";
import { useSubscription } from "@/context/SubscriptionContext";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { MessageCircle, X, Send, Bot, User, Shield, ArrowRight, Mail, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "./ui/card";
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import type { ActionButton } from "@/context/AIContextInstance";

export const AIAssistant = () => {
    const { isOpen, toggleChat, messages, sendMessage, isLoading, activeTool, closeTool, dynamicSuggestions, welcomeMessage } = useAI();
    const { subscriptionPlan } = useAuth();
    const { tier, usage, refreshEntitlements } = useSubscription();
    const [input, setInput] = useState("");
    const isFreeUser = tier === 'FREE';
    const chatLimitReached = isFreeUser && usage.daily_ai_chats >= 10;
    const scrollRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();
    const location = useLocation();

    const isScannerRoute = location.pathname.includes('/pqc-scanner') || location.pathname.includes('/enterprise');
    const isSandboxRoute = location.pathname === '/sandbox';
    const isEnterprise = (subscriptionPlan === 'enterprise' && !isSandboxRoute) || isScannerRoute;

    // Tool Navigation Handler
    useEffect(() => {
        if (!activeTool) return;

        if (activeTool === "quantum-states") {
            navigate("/quantum-states");
            closeTool();
        } else if (activeTool === "circuit-builder") {
            navigate("/circuit-builder");
            closeTool();
        } else if (activeTool === "pqc-scanner") {
            navigate("/pqc-scanner");
            closeTool();
        }
    }, [activeTool, navigate, closeTool]);

    // Handle external custom events from AI context
    useEffect(() => {
        const handleNavigate = (e: any) => {
            const { path, section } = e.detail;
            navigate(path + (section ? `#${section}` : ""));
        };

        const handleStartTutorial = (e: any) => {
            const { tutorialId } = e.detail;
            navigate("/circuit-builder");
            localStorage.setItem("pending_tutorial", tutorialId);
        };

        const handleLoadTemplate = (e: any) => {
            const { templateName } = e.detail;
            localStorage.setItem("pending_template", templateName);
        };

        window.addEventListener("ai-navigate", handleNavigate);
        window.addEventListener("ai-start-tutorial", handleStartTutorial);
        window.addEventListener("ai-load-template", handleLoadTemplate);

        return () => {
            window.removeEventListener("ai-navigate", handleNavigate);
            window.removeEventListener("ai-start-tutorial", handleStartTutorial);
            window.removeEventListener("ai-load-template", handleLoadTemplate);
        };
    }, [navigate]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, isOpen]);

    const handleSend = async () => {
        if (!input.trim()) return;

        if (isFreeUser && usage.daily_ai_chats >= 10) {
            window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'chats' } }));
            return;
        }

        const msg = input;
        setInput("");
        try {
            await sendMessage(msg);
            setTimeout(() => refreshEntitlements(), 1000);
        } catch (err) {
            console.error(err);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleActionButton = (action: ActionButton) => {
        if (action.type === "navigate" && action.path) {
            navigate(action.path);
        } else if (action.type === "email" && action.email) {
            const subject = encodeURIComponent(action.subject || "QuantCAI Inquiry");
            window.open(`mailto:${action.email}?subject=${subject}`, '_blank');
        } else if (action.type === "tool" && action.toolName) {
            if (action.toolName === "circuit-builder" || action.toolName === "quantum-states" || action.toolName === "pqc-scanner") {
                navigate(`/${action.toolName}`);
            }
        } else if (action.type === "upgrade") {
            window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'feature' } }));
        }
    };

    // Get context-aware suggestions (prefer dynamic from backend, fallback to static)
    const suggestions = dynamicSuggestions.length > 0
        ? dynamicSuggestions
        : (isEnterprise
            ? ["Compute PQC Readiness Score", "Scan for RSA-2048/ECC-256", "Draft remediation roadmap"]
            : (() => {
                const path = location.pathname;
                if (path.startsWith("/circuit-builder")) return ["Explain my circuit", "Build a Bell State", "Optimize gate count"];
                if (path.startsWith("/pqc-scanner")) return ["What is PQC?", "Explain FIPS 203", "How to migrate from RSA?"];
                if (path.startsWith("/learn/qubits")) return ["Explain superposition", "What is the Bloch sphere?", "Quiz me!"];
                if (path.startsWith("/learn/gates")) return ["What does Hadamard do?", "Build a Bell State", "Show me CNOT"];
                if (path.startsWith("/learn/pqc")) return ["What is ML-KEM?", "How does Shor's algorithm work?", "Scan a domain"];
                if (path.startsWith("/learn")) return ["What is a qubit?", "Start learning path", "Show circuit builder"];
                if (path.startsWith("/quantum-states")) return ["Apply Hadamard gate", "What is superposition?", "Explain Bloch sphere"];
                if (path.startsWith("/enterprise")) return ["CLI scanner details", "On-prem deployment", "Contact the team"];
                return ["Explain Bell States", "Open Circuit Builder", "How do qubits work?"];
            })()
        );

    // Smart welcome message
    const welcome = welcomeMessage || (isEnterprise
        ? "I am the Large Quantitative Model. Ask me to compute PQC Readiness Scores, map cryptographic dependencies, or draft remediation plans."
        : (() => {
            const path = location.pathname;
            if (path.startsWith("/circuit-builder")) return "Ready to build quantum circuits! I can design, explain, and optimize. Try asking me to build a Bell State.";
            if (path.startsWith("/pqc-scanner")) return "I can assess domains for quantum-vulnerable cryptography. Enter a domain or ask about PQC standards.";
            if (path.startsWith("/learn/qubits")) return "I see you're studying **Qubits**! Ask me anything about superposition, measurement, or the Bloch sphere.";
            if (path.startsWith("/learn/gates")) return "Exploring **Quantum Gates**! I can explain any gate, demonstrate on the visualizer, or help you build circuits.";
            if (path.startsWith("/learn/pqc")) return "Learning about **Post-Quantum Cryptography**! I can explain NIST standards, scan domains, or discuss migration strategies.";
            if (path.startsWith("/learn")) return "Welcome to the quantum learning journey! I'm your personal tutor — ask me anything or let me guide you step by step.";
            if (path.startsWith("/quantum-states")) return "I can demonstrate gate effects on the Bloch Sphere. Try asking me to apply a Hadamard gate!";
            if (path.startsWith("/enterprise")) return "I can walk you through our enterprise offerings — CLI scanner, on-prem deployment, compliance suite, and custom SLAs.";
            return "I'm your quantum assistant. Ask me to explain concepts, build circuits, or guide you through tutorials.";
        })()
    );

    return (
        <>
            {/* Floating Button */}
            <div className="fixed bottom-4 right-4 z-50">
                <Button
                    onClick={toggleChat}
                    size="lg"
                    className={cn(
                        "rounded-full h-14 w-14 shadow-[0_0_20px_rgba(59,130,246,0.5)] transition-all duration-500 hover:scale-110 active:scale-95",
                        isOpen ? "scale-0 opacity-0 rotate-90" : "scale-100 opacity-100 rotate-0",
                        isEnterprise
                            ? "bg-gradient-to-tr from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-slate-950 border-0"
                            : "bg-gradient-to-tr from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white border-0"
                    )}
                >
                    {isEnterprise ? <Shield className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
                    <span className="sr-only">Talk to AI</span>
                </Button>
            </div>

            {/* Chat Interface */}
            <div
                className={cn(
                    "fixed bottom-4 right-4 z-50 transition-all duration-500 origin-bottom-right",
                    isOpen
                        ? "scale-100 opacity-100 translate-y-0"
                        : "scale-90 opacity-0 translate-y-8 pointer-events-none"
                )}
            >
                <Card className="w-[380px] h-[600px] shadow-[0_20px_50px_rgba(0,0,0,0.5)] border-white/10 flex flex-col backdrop-blur-2xl bg-slate-900/80 overflow-hidden rounded-3xl">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-purple-500/10 pointer-events-none" />

                    <CardHeader className="flex flex-row items-center justify-between pb-3 border-b border-white/5 relative z-10 bg-white/5">
                        <div className="flex items-center gap-3">
                            <div className={cn("p-2 rounded-xl", isEnterprise ? "bg-emerald-500/20" : "bg-blue-500/20")}>
                                {isEnterprise ? <Shield className="h-5 w-5 text-emerald-400" /> : <Bot className="h-5 w-5 text-blue-400" />}
                            </div>
                            <div>
                                <CardTitle className="text-base font-bold tracking-tight">
                                    {isEnterprise ? "LQM Compliance" : "QuantAI"}
                                </CardTitle>
                                <div className="flex items-center gap-1.5">
                                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
                                    <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Online</span>
                                </div>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={toggleChat}
                            className="h-8 w-8 -mr-2 text-muted-foreground hover:text-white hover:bg-white/10 rounded-full"
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </CardHeader>

                    <CardContent className="flex-1 p-0 overflow-hidden relative z-10">
                        <ScrollArea className="h-full px-4 pt-4">
                            <div className="flex flex-col gap-6 pb-6">
                                {messages.length === 0 && (
                                    <div className="text-center my-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                        <div className="relative inline-block mb-6">
                                            <div className="absolute inset-0 bg-blue-500/20 blur-2xl rounded-full" />
                                            <div className={cn("relative h-20 w-20 mx-auto rounded-3xl flex items-center justify-center shadow-xl rotate-3",
                                                isEnterprise ? "bg-gradient-to-tr from-emerald-600 to-teal-600" : "bg-gradient-to-tr from-blue-600 to-purple-600"
                                            )}>
                                                {isEnterprise ? <Shield className="h-10 w-10 text-slate-950" /> : <Bot className="h-10 w-10 text-white" />}
                                            </div>
                                        </div>
                                        <h3 className="text-xl font-bold mb-2">
                                            {isEnterprise ? "LQM Compliance Suite" : "QuantAI"}
                                        </h3>
                                        <p className="text-sm text-muted-foreground max-w-[280px] mx-auto leading-relaxed">
                                            {welcome}
                                        </p>

                                        <div className="grid grid-cols-1 gap-2 mt-8 max-w-[280px] mx-auto">
                                            {suggestions.map((suggestion) => (
                                                <button
                                                    key={suggestion}
                                                    onClick={() => {
                                                        setInput(suggestion);
                                                        // Auto-send on suggestion click
                                                        setTimeout(() => {
                                                            sendMessage(suggestion);
                                                        }, 100);
                                                    }}
                                                    className={cn("text-xs text-left p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 transition-all duration-200 font-medium hover:scale-[1.02] active:scale-[0.98]",
                                                        isEnterprise ? "text-emerald-300 hover:border-emerald-500/30" : "text-blue-300 hover:border-blue-500/30"
                                                    )}
                                                >
                                                    {suggestion}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {messages.map((msg, i) => (
                                    <div
                                        key={i}
                                        className={cn(
                                            "flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300",
                                            msg.role === "user" ? "items-end" : "items-start"
                                        )}
                                    >
                                        <div
                                            className={cn(
                                                "flex gap-2.5 max-w-[90%]",
                                                msg.role === "user" ? "flex-row-reverse" : "flex-row"
                                            )}
                                        >
                                            <div
                                                className={cn(
                                                    "h-7 w-7 rounded-lg flex items-center justify-center shrink-0 mt-1 shadow-md",
                                                    msg.role === "user"
                                                        ? (isEnterprise ? "bg-emerald-600 text-slate-950" : "bg-blue-600 text-white")
                                                        : (isEnterprise ? "bg-slate-805 border border-white/10 text-emerald-400" : "bg-slate-800 border border-white/10 text-blue-400")
                                                )}
                                            >
                                                {msg.role === "user" ? <User className="h-3.5 w-3.5" /> : (isEnterprise ? <Shield className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />)}
                                            </div>
                                            <div className="flex flex-col gap-2">
                                                <div
                                                    className={cn(
                                                        "px-4 py-3 rounded-2xl text-[13.5px] leading-relaxed relative",
                                                        msg.role === "user"
                                                            ? (isEnterprise ? "bg-emerald-600 text-slate-950 rounded-tr-none shadow-emerald-900/20" : "bg-blue-600 text-white rounded-tr-none shadow-blue-900/20") + " shadow-lg"
                                                            : "bg-white/5 text-slate-200 rounded-tl-none border border-white/5 shadow-sm"
                                                    )}
                                                >
                                                    {msg.content ? (
                                                        <div className="prose prose-invert prose-sm max-w-none">
                                                            <ReactMarkdown
                                                                remarkPlugins={[remarkMath]}
                                                                rehypePlugins={[rehypeKatex]}
                                                                components={{
                                                                    p: ({ children }) => <p className="m-0 last:mb-0 mb-3">{children}</p>,
                                                                    code: ({ children }) => <code className={cn("rounded-md px-1.5 py-0.5 font-mono text-xs", isEnterprise ? "bg-white/10 text-emerald-300" : "bg-white/10 text-blue-300")}>{children}</code>,
                                                                    strong: ({ children }) => <strong className="font-bold text-white">{children}</strong>,
                                                                }}
                                                            >
                                                                {msg.content}
                                                            </ReactMarkdown>
                                                        </div>
                                                    ) : (
                                                        isLoading && i === messages.length - 1 ? (
                                                            <div className="flex gap-1.5 h-6 items-center px-1">
                                                                <span className={cn("w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:-0.3s]", isEnterprise ? "bg-emerald-400" : "bg-blue-400")}></span>
                                                                <span className={cn("w-1.5 h-1.5 rounded-full animate-bounce [animation-delay:-0.15s]", isEnterprise ? "bg-emerald-400" : "bg-blue-400")}></span>
                                                                <span className={cn("w-1.5 h-1.5 rounded-full animate-bounce", isEnterprise ? "bg-emerald-400" : "bg-blue-400")}></span>
                                                            </div>
                                                        ) : null
                                                    )}
                                                </div>

                                                {/* Inline Action Buttons */}
                                                {msg.role === "assistant" && msg.actions && msg.actions.length > 0 && (
                                                    <div className="flex flex-wrap gap-1.5 mt-1">
                                                        {msg.actions.map((action, actionIdx) => (
                                                            <button
                                                                key={actionIdx}
                                                                onClick={() => handleActionButton(action)}
                                                                className={cn(
                                                                    "inline-flex items-center gap-1.5 text-[11px] font-bold px-3 py-1.5 rounded-lg transition-all duration-200 hover:scale-[1.03] active:scale-[0.97]",
                                                                    action.type === "email"
                                                                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30"
                                                                        : action.type === "navigate"
                                                                            ? "bg-blue-500/20 text-blue-300 border border-blue-500/30 hover:bg-blue-500/30"
                                                                            : action.type === "upgrade"
                                                                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30 hover:bg-amber-500/30"
                                                                                : "bg-purple-500/20 text-purple-300 border border-purple-500/30 hover:bg-purple-500/30"
                                                                )}
                                                            >
                                                                {action.type === "email" ? <Mail className="h-3 w-3" /> :
                                                                 action.type === "navigate" ? <ArrowRight className="h-3 w-3" /> :
                                                                 <ExternalLink className="h-3 w-3" />}
                                                                {action.label}
                                                            </button>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <span className="text-[10px] text-muted-foreground/60 font-medium tracking-wide">
                                            {msg.role === "user" ? "You" : (isEnterprise ? "LQM" : "QuantAI")}
                                        </span>
                                    </div>
                                ))}

                                <div ref={scrollRef} />
                            </div>
                        </ScrollArea>

                        {chatLimitReached && (
                            <div className="mx-4 mb-2 p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 font-mono text-center flex flex-col gap-1.5 animate-in fade-in slide-in-from-bottom-2">
                                <span className="font-bold uppercase tracking-wider">🔒 Daily Limit Reached</span>
                                <span>You have reached your 10 free daily chats. Upgrade to Pro for unlimited contextual queries.</span>
                                <button
                                    type="button"
                                    onClick={() => window.dispatchEvent(new CustomEvent('show-upgrade-modal', { detail: { reason: 'chats' } }))}
                                    className="mt-1 py-1 rounded-xl bg-amber-500 text-slate-950 font-bold hover:bg-amber-400 transition-colors uppercase tracking-wider text-[10px]"
                                >
                                    Upgrade to Pro
                                </button>
                            </div>
                        )}
                    </CardContent>

                    <CardFooter className="p-4 border-t border-white/5 bg-white/5 relative z-10 mt-auto">
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                  handleSend();
                            }}
                            className="flex w-full gap-2 items-center"
                        >
                            <div className="relative flex-1">
                                <Input
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder={chatLimitReached ? "AI chat limit reached for today." : (isEnterprise ? "Ask about PQC compliance, scan targets, or remediation..." : "Ask anything quantum...")}
                                    className="pr-12 bg-white/5 border-white/10 focus-visible:ring-blue-500/50 h-10 rounded-xl placeholder:text-muted-foreground/50 transition-all focus:bg-white/10"
                                    onKeyDown={handleKeyDown}
                                    disabled={chatLimitReached}
                                />
                                {input.trim() && (
                                    <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                                        <span className="text-[10px] text-muted-foreground/30 font-bold border border-white/5 rounded px-1">ENTER</span>
                                    </div>
                                )}
                            </div>
                            <Button
                                type="submit"
                                size="icon"
                                disabled={isLoading || !input.trim() || chatLimitReached}
                                className={cn("h-10 w-10 shrink-0 rounded-xl text-white shadow-lg disabled:opacity-30 transition-all hover:scale-105 active:scale-95",
                                    isEnterprise ? "bg-emerald-600 hover:bg-emerald-500 shadow-emerald-950/20" : "bg-blue-600 hover:bg-blue-500 shadow-blue-900/20"
                                )}
                            >
                                <Send className="h-4 w-4" />
                            </Button>
                        </form>
                    </CardFooter>
                </Card>
            </div>
        </>
    );
};
