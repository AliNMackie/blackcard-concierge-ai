import { NextResponse } from 'next/server';

export async function GET() {
    const mockEvents = [
        {
            id: 101,
            user_id: "client-1",
            event_type: "wearable",
            payload: { score: 42 },
            agent_decision: "RED",
            agent_message: "Your recovery is critically low (42). Intervention: Day off.",
            created_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        },
        {
            id: 102,
            user_id: "client-1",
            event_type: "vision",
            payload: { detected: ["Kettlebells"] },
            agent_decision: "WORKOUT_GENERATED",
            agent_message: "Detected Kettlebells. Generating HIIT flows.",
            created_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
        },
        {
            id: 103,
            user_id: "client-1",
            event_type: "chat",
            payload: { message: "Reschedule to 6pm" },
            agent_decision: "ACK",
            agent_message: "Understood. Notifying your Personal Trainer.",
            created_at: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
        },
        {
            id: 104,
            user_id: "client-2",
            event_type: "wearable",
            payload: { score: 95 },
            agent_decision: "GREEN",
            agent_message: "Excellent recovery. Go heavy today.",
            created_at: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
        }
    ];

    return NextResponse.json(mockEvents);
}
