"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Send, Activity, Users, Trophy, MessageSquare, Loader2 } from "lucide-react";
import Link from 'next/link';
import { fetchEvents, EventLog, sendChatMessage } from '@/lib/api';
import { formatDistanceToNow } from 'date-fns';

export default function MessagesPage() {
    const router = useRouter();
    const [messages, setMessages] = useState<EventLog[]>([]);
    const [loading, setLoading] = useState(true);
    const [inputMessage, setInputMessage] = useState("");
    const [sending, setSending] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Load messages on mount
    useEffect(() => {
        loadMessages();
        // Poll for new messages every 10 seconds
        const interval = setInterval(loadMessages, 10000);
        return () => clearInterval(interval);
    }, []);

    // Scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    async function loadMessages() {
        try {
            const events = await fetchEvents(50);
            // Filter to chat and trainer_message events only
            const chatEvents = events.filter(e =>
                e.event_type === 'chat' || e.event_type === 'trainer_message'
            );
            // Reverse to show oldest first (chronological order)
            setMessages(chatEvents.reverse());
        } catch (err) {
            console.error("Failed to load messages:", err);
        }
        setLoading(false);
    }

    async function handleSend() {
        if (!inputMessage.trim() || sending) return;

        const text = inputMessage.trim();
        setInputMessage("");
        setSending(true);

        // Optimistic: Immediately show the user's message
        const optimisticId = -Date.now();
        const optimisticMsg: EventLog = {
            id: optimisticId,
            user_id: "1",
            event_type: "chat",
            payload: { message: text, role: "user" },
            agent_decision: "",
            agent_message: "",
            created_at: new Date().toISOString(),
        };
        setMessages(prev => [...prev, optimisticMsg]);

        try {
            await sendChatMessage("1", text);
            // Refresh to get server-confirmed message + AI response
            await loadMessages();
        } catch (err) {
            console.error("Failed to send:", err);
            // Rollback the optimistic message
            setMessages(prev => prev.filter(m => m.id !== optimisticId));
            setInputMessage(text); // Restore the input
            alert("Failed to send message. Please try again.");
        }
        setSending(false);
    }

    function handleKeyPress(e: React.KeyboardEvent) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    }

    // Determine if a message is from the user or from trainer/AI
    function isFromUser(event: EventLog): boolean {
        if (event.event_type === 'trainer_message') return false;
        // For chat events, check the payload
        return event.payload?.role !== 'assistant';
    }

    function getMessageText(event: EventLog): string {
        if (event.event_type === 'trainer_message') {
            return event.agent_message || event.payload?.message || "";
        }
        // For chat, show user message or AI response
        return event.payload?.message || event.agent_message || "";
    }

    function getSenderLabel(event: EventLog): string {
        if (event.event_type === 'trainer_message') return "Trainer";
        if (event.payload?.role === 'assistant') return "AI Concierge";
        return "You";
    }

    return (
        <div className="min-h-screen bg-black text-white font-sans flex flex-col max-w-md mx-auto border-x border-gray-900">
            {/* Header */}
            <header className="p-6 border-b border-gray-900 flex items-center gap-4">
                <button onClick={() => router.back()} className="text-gray-500 hover:text-white">
                    <ArrowLeft size={24} />
                </button>
                <div>
                    <h1 className="text-xl font-bold tracking-tight">Coach Connection</h1>
                    <p className="text-[10px] text-green-500 uppercase tracking-widest font-bold">
                        {loading ? "Loading..." : `${messages.length} Messages`}
                    </p>
                </div>
            </header>

            {/* Chat Body */}
            <main className="flex-grow p-6 space-y-4 overflow-y-auto pb-40">
                {loading ? (
                    <div className="flex items-center justify-center py-12">
                        <Loader2 className="animate-spin text-gray-500" size={32} />
                    </div>
                ) : messages.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                        <MessageSquare size={48} className="mx-auto mb-4 opacity-50" />
                        <p>No messages yet.</p>
                        <p className="text-sm">Say hi to your AI concierge!</p>
                    </div>
                ) : (
                    messages.map((msg) => {
                        const fromUser = isFromUser(msg);
                        const isTrainer = msg.event_type === 'trainer_message';

                        return (
                            <div
                                key={msg.id}
                                className={`flex flex-col ${fromUser ? "items-end" : "items-start"}`}
                            >
                                <div className={`max-w-[85%] p-4 rounded-2xl text-sm ${fromUser
                                    ? "bg-zinc-800 text-white rounded-tr-none"
                                    : isTrainer
                                        ? "bg-green-900/30 border border-green-800 text-green-100 rounded-tl-none"
                                        : "bg-zinc-100 text-black rounded-tl-none font-medium"
                                    }`}>
                                    {isTrainer && (
                                        <p className="text-[10px] text-green-400 uppercase font-bold mb-1 tracking-widest">
                                            💪 From Your Trainer
                                        </p>
                                    )}
                                    {getMessageText(msg)}
                                </div>
                                <span className="text-[10px] text-gray-600 mt-1 uppercase tracking-tighter">
                                    {getSenderLabel(msg)} • {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })}
                                </span>
                            </div>
                        );
                    })
                )}
                <div ref={messagesEndRef} />
            </main>

            {/* Input */}
            <div className="fixed bottom-16 left-0 right-0 p-4 border-t border-gray-900 bg-black max-w-md mx-auto">
                <div className="relative">
                    <input
                        type="text"
                        value={inputMessage}
                        onChange={(e) => setInputMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Message your coach..."
                        disabled={sending}
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-xl py-4 px-6 text-sm text-white pr-14 focus:border-white transition-all outline-none disabled:opacity-50"
                    />
                    <button
                        onClick={handleSend}
                        disabled={sending || !inputMessage.trim()}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white disabled:opacity-30 transition"
                    >
                        {sending ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
                    </button>
                </div>
            </div>

            {/* Navigation */}
            <div className="fixed bottom-0 left-0 right-0 border-t border-gray-900 bg-black/90 backdrop-blur pb-6 pt-4 flex justify-around text-gray-500 max-w-md mx-auto z-50">
                <Link href="/dashboard"><Activity size={24} className="hover:text-white transition" /></Link>
                <Link href="/personas"><Users size={24} className="hover:text-white transition" /></Link>
                <Link href="/performance"><Trophy size={24} className="hover:text-white transition" /></Link>
                <Link href="/messages"><div className="text-white relative"><MessageSquare size={24} /><div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 bg-white rounded-full"></div></div></Link>
            </div>
        </div>
    );
}
