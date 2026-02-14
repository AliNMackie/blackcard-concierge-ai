import Link from 'next/link';

export const metadata = {
    title: 'Privacy Policy | Elite Concierge AI',
    description: 'How we handle your personal and biometric data.',
};

export default function PrivacyPage() {
    return (
        <main className="min-h-screen bg-black text-white px-6 py-16 max-w-3xl mx-auto">
            <Link href="/" className="text-zinc-500 hover:text-white text-sm mb-8 inline-block">&larr; Back</Link>

            <h1 className="text-3xl font-bold mb-2">Privacy Policy</h1>
            <p className="text-zinc-500 text-sm mb-10">Last updated: 14 February 2026</p>

            <section className="space-y-8 text-zinc-300 leading-relaxed">

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">1. Who We Are</h2>
                    <p>
                        Elite Concierge AI (&quot;we&quot;, &quot;us&quot;) is operated by [Your Company Name], registered in England and Wales.
                        We provide an AI-powered fitness concierge platform for high-performance athletes and their coaching teams.
                    </p>
                    <p className="mt-2">
                        <strong>Data Controller:</strong> [Your Company Name]<br />
                        <strong>Contact:</strong> privacy@eliteconcierge.ai
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">2. What Data We Collect</h2>
                    <ul className="list-disc list-inside space-y-1">
                        <li><strong>Account Data:</strong> Name, email address, role (Client / Trainer).</li>
                        <li><strong>Biometric Data:</strong> Heart rate, sleep scores, recovery metrics (via wearable integrations such as WHOOP, Oura).</li>
                        <li><strong>Media:</strong> Photos and videos uploaded for AI-powered form analysis (Vision Coach).</li>
                        <li><strong>Chat Messages:</strong> Conversations with the AI concierge.</li>
                        <li><strong>Usage Data:</strong> Timestamps, device info, and interaction logs for service improvement.</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">3. How We Use Your Data</h2>
                    <ul className="list-disc list-inside space-y-1">
                        <li>To deliver personalised coaching recommendations via our AI engine (Google Vertex AI / Gemini).</li>
                        <li>To display your readiness and performance data on your dashboard.</li>
                        <li>To enable your trainer to monitor your progress and intervene when needed.</li>
                        <li>To send push notifications for critical health alerts (e.g., RED biometric status).</li>
                    </ul>
                    <p className="mt-2 text-zinc-400 text-sm">
                        We do <strong>not</strong> sell your data. We do <strong>not</strong> use your data for advertising.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">4. Where Your Data is Stored</h2>
                    <p>
                        All data is stored on Google Cloud Platform infrastructure in the <strong>europe-west2 (London)</strong> region.
                        This includes Cloud SQL (PostgreSQL) for structured data and Cloud Run for application processing.
                        Media uploaded to Vision Coach is processed in-memory and <strong>not permanently stored</strong> &mdash; only the AI analysis is retained.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">5. Data Sharing</h2>
                    <ul className="list-disc list-inside space-y-1">
                        <li><strong>Your Trainer:</strong> If you are assigned to a trainer, they can view your dashboard data, chat history, and alerts.</li>
                        <li><strong>Google Cloud / Vertex AI:</strong> Your queries are processed by Google&apos;s Gemini model. Google&apos;s data processing terms apply.</li>
                        <li><strong>No other third parties</strong> receive your personal data.</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">6. Your Rights (UK GDPR)</h2>
                    <p>You have the right to:</p>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                        <li><strong>Access</strong> your data (Settings &rarr; Export Data).</li>
                        <li><strong>Rectify</strong> inaccurate data by contacting us.</li>
                        <li><strong>Erase</strong> all your data (Settings &rarr; Delete Account). This triggers a permanent, irreversible wipe of all your records.</li>
                        <li><strong>Object</strong> to processing by contacting privacy@eliteconcierge.ai.</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">7. Data Retention</h2>
                    <p>
                        We retain your data for as long as your account is active.
                        If you request deletion, all personal data is permanently removed within 30 days.
                        Anonymised, aggregated analytics data may be retained indefinitely.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">8. Security</h2>
                    <p>
                        All data is encrypted in transit (TLS 1.3) and at rest (AES-256 via Google Cloud).
                        Access to production systems is restricted via IAM roles and Workload Identity Federation.
                        API authentication uses Firebase ID Tokens and server-side API keys.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">9. Contact</h2>
                    <p>
                        For any privacy-related queries, contact:<br />
                        <strong>privacy@eliteconcierge.ai</strong>
                    </p>
                </div>

            </section>

            <div className="mt-12 pt-8 border-t border-zinc-800 text-zinc-600 text-sm">
                <Link href="/terms" className="hover:text-white">Terms of Service</Link>
            </div>
        </main>
    );
}
