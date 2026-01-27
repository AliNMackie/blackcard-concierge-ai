import { NextResponse } from 'next/server';

export async function POST(request: Request) {
    const body = await request.json();
    const { clientId, action } = body;

    console.log(`[MOCK BFF] Override for ${clientId}: ${action}`);

    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 800));

    return NextResponse.json({
        success: true,
        message: `Override '${action}' applied for client ${clientId}`
    });
}
