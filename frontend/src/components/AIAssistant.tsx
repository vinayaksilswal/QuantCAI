import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAI } from "../hooks/useAI";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { MessageCircle, X, Send, Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "./ui/card";
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';

export const AIAssistant = () => {
    const { isOpen, toggleChat, messages, sendMessage, isLoading, activeTool, closeTool } = useAI();
    const [input, setInput] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();

    // Tool Navigation Handler
    useEffect(() => {
        if (!activeTool) return;

        if (activeTool === "quantum-states") {
            navigate("/quantum-states");
            closeTool();
        } else if (activeTool === "circuit-builder") {
            navigate("/circuit-builder");
            closeTool();
        }
    }, [activeTool, navigate, closeTool]);

    // Handle external custom events from AI context
    useEffect(() => {
        const handleNavigate = (e: any) => {
            const { path, section } = e.detail;
            navigate(path + (section ? `#${section}` : ""));
            // Maybe close chat or show a message
        };

        const handleStartTutorial = (e: any) => {
            const { tutorialId } = e.detail;
            // This event should be picked up by TutorialOverlay if it's listening,
            // or we can handle it by navigating to circuit builder first.
            navigate("/circuit-builder");
            // We need a way to tell TutorialOverlay to start.
            // Let's use localStorage or a shared state if needed, 
            // but for now, the user's request "integrate it with the tutorial" 
            // suggests the AI should be able to trigger it.
            localStorage.setItem("pending_tutorial", tutorialId);
        };

        window.addEventListener("ai-navigate", handleNavigate);
        window.addEventListener("ai-start-tutorial", handleStartTutorial);

        return () => {
            window.removeEventListener("ai-navigate", handleNavigate);
            window.removeEventListener("ai-start-tutorial", handleStartTutorial);
        };
    }, [navigate]);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, isOpen]);


    const handleSend = async () => {
        if (!input.trim()) return;
        const msg = input;
        setInput("");
        await sendMessage(msg);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <>
            {/* Floating Button */}
            <div className="fixed bottom-6 right-6 z-50">
                <Button
                    onClick={toggleChat}
                    size="lg"
                    className={cn(
                        "rounded-full h-14 w-14 shadow-lg transition-transform duration-300",
                        isOpen ? "scale-0 opacity-0" : "scale-100 opacity-100",
                        "bg-primary hover:bg-primary/90 text-primary-foreground"
                    )}
                >
                    <MessageCircle className="h-6 w-6" />
                    <span className="sr-only">Talk to AI</span>
                </Button>
            </div>

            {/* Chat Interface */}
            <div
                className={cn(
                    "fixed bottom-6 right-6 z-50 transition-all duration-300 origin-bottom-right",
                    isOpen
                        ? "scale-100 opacity-100 translate-y-0"
                        : "scale-90 opacity-0 translate-y-8 pointer-events-none"
                )}
            >
                <Card className="w-[380px] h-[600px] shadow-2xl border-primary/20 flex flex-col backdrop-blur-md bg-background/95">
                    <CardHeader className="flex flex-row items-center justify-between pb-3 border-b">
                        <div className="flex items-center gap-2">
                            <Bot className="h-5 w-5 text-primary" />
                            <CardTitle className="text-lg">QuantAI Assistant</CardTitle>
                        </div>
                        <Button
                            variant="ghost"
                            size="icon"
                            onClick={toggleChat}
                            className="h-8 w-8 -mr-2"
                        >
                            <X className="h-4 w-4" />
                        </Button>
                    </CardHeader>

                    <CardContent className="flex-1 p-0 overflow-hidden relative">
                        <ScrollArea className="h-full p-4">
                            <div className="flex flex-col gap-4 pb-4">
                                {messages.length === 0 && (
                                    <div className="text-center text-muted-foreground my-8">
                                        <Bot className="h-12 w-12 mx-auto mb-3 opacity-50" />
                                        <p>Hi! I'm QuantAI.</p>
                                        <p className="text-sm">Ask me about quantum concepts or tell me to open a tool!</p>
                                    </div>
                                )}

                                {messages.map((msg, i) => (
                                    <div
                                        key={i}
                                        className={cn(
                                            "flex flex-col gap-1",
                                            msg.role === "user" ? "items-end" : "items-start"
                                        )}
                                    >
                                        <div
                                            className={cn(
                                                "flex gap-3 max-w-[85%]",
                                                msg.role === "user" ? "flex-row-reverse" : "flex-row"
                                            )}
                                        >
                                            <div
                                                className={cn(
                                                    "h-8 w-8 rounded-full flex items-center justify-center shrink-0",
                                                    msg.role === "user"
                                                        ? "bg-primary text-primary-foreground"
                                                        : "bg-secondary text-secondary-foreground"
                                                )}
                                            >
                                                {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                            </div>
                                            <div
                                                className={cn(
                                                    "p-3 rounded-2xl text-sm prose prose-invert max-w-none",
                                                    msg.role === "user"
                                                        ? "bg-primary text-primary-foreground rounded-tr-sm"
                                                        : "bg-secondary text-secondary-foreground rounded-tl-sm shadow-sm border border-white/5"
                                                )}
                                            >
                                                {msg.content ? (
                                                    <ReactMarkdown
                                                        remarkPlugins={[remarkMath]}
                                                        rehypePlugins={[rehypeKatex]}
                                                        components={{
                                                            p: ({ children }) => <p className="m-0">{children}</p>,
                                                            code: ({ children }) => <code className="bg-black/20 rounded px-1">{children}</code>
                                                        }}
                                                    >
                                                        {msg.content}
                                                    </ReactMarkdown>
                                                ) : (
                                                    isLoading && i === messages.length - 1 ? (
                                                        <div className="flex gap-1 h-5 items-center">
                                                            <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                                                            <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                                                            <span className="w-1.5 h-1.5 bg-foreground/50 rounded-full animate-bounce"></span>
                                                        </div>
                                                    ) : null
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                ))}

                                <div ref={scrollRef} />
                            </div>
                        </ScrollArea>
                    </CardContent>

                    <CardFooter className="p-3 pt-3 border-t bg-muted/20">
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                handleSend();
                            }}
                            className="flex w-full gap-2"
                        >
                            <Input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Type a message..."
                                className="flex-1 bg-background/50"
                                onKeyDown={handleKeyDown}
                            />
                            <Button type="submit" size="icon" disabled={isLoading || !input.trim()}>
                                <Send className="h-4 w-4" />
                            </Button>
                        </form>
                    </CardFooter>
                </Card>
            </div>
        </>
    );
};
