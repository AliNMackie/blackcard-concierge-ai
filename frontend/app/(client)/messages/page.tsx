"use client";

import { useRouter } from "next/navigation";
import { ArrowLeft, Send } from "lucide-react";

export default function MessagesPage() {
    const router = useRouter();

    const messages = [
        {
            id: 1,
            sender: "User",
            text: "My knee is feeling tight on lunges.",
            time: "Yesterday, 4:12 PM"
        },
        {
            id: 2,
            sender: "Coach",
            text: "Understood. I've switched your lower body volume to Sled Pushes to reduce eccentric load. Check your new plan.",
            time: "Yesterday, 4:15 PM"
        }
    ];

    return (
        <div className="min-h-screen bg-black text-white font-sans flex flex-col max-w-md mx-auto border-x border-gray-900">
            {/* Header */}
            <header className="p-6 border-b border-gray-900 flex items-center gap-4">
                <button onClick={() => router.back()} className="text-gray-500 hover:text-white">
                    <ArrowLeft size={24} />
                </button>
                <div>
                    <h1 className="text-xl font-bold tracking-tight">Coach Connection</h1>
                    <p className="text-[10px] text-green-500 uppercase tracking-widest font-bold">Active Protocol</p>
                </div>
            </header>

            {/* Chat Body */}
            <main className="flex-grow p-6 space-y-6 overflow-y-auto">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`flex flex-col ${msg.sender === "User" ? "items-end" : "items-start"}`}
                    >
                        <div className={`max-w-[80%] p-4 rounded-2xl text-sm ${msg.sender === "User"
                                ? "bg-zinc-800 text-white rounded-tr-none"
                                : "bg-zinc-100 text-black rounded-tl-none font-medium"
                            }`}>
                            {msg.text}
                        </div>
                        <span className="text-[10px] text-gray-600 mt-1 uppercase tracking-tighter">
                            {msg.time}
                        </span>
                    </div>
                ))}
            </main>

            {/* Input Placeholder */}
            <footer className="p-6 border-t border-gray-900 bg-black/50 backdrop-blur pb-10">
                <div className="relative">
                    <input
                        type="text"
                        placeholder="Message your coach..."
                        className="w-full bg-zinc-900 border border-zinc-800 rounded-xl py-4 px-6 text-sm text-white pr-14 focus:border-white transition-all outline-none"
                    />
                    <button className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                        <Send size={20} />
                    </button>
                </div>
            </footer>
        </div>
    );
}
