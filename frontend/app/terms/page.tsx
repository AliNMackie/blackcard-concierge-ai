import Link from 'next/link';

export const metadata = {
    title: 'Terms of Service | Elite Concierge AI',
    description: 'Terms and conditions for using Elite Concierge AI.',
};

export default function TermsPage() {
    return (
        <main className="min-h-screen bg-black text-white px-6 py-16 max-w-3xl mx-auto">
            <Link href="/" className="text-zinc-500 hover:text-white text-sm mb-8 inline-block">&larr; Back</Link>

            <h1 className="text-3xl font-bold mb-2">Terms of Service</h1>
            <p className="text-zinc-500 text-sm mb-10">Last updated: 14 February 2026</p>

            <section className="space-y-8 text-zinc-300 leading-relaxed">

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">1. Acceptance</h2>
                    <p>
                        By accessing or using Elite Concierge AI (&quot;the Service&quot;), you agree to be bound by these Terms.
                        If you do not agree, you must not use the Service.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">2. The Service</h2>
                    <p>
                        Elite Concierge AI is an AI-powered fitness intelligence platform that provides:
                    </p>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                        <li>Biometric monitoring and readiness scoring.</li>
                        <li>AI-generated coaching recommendations.</li>
                        <li>Vision-based movement analysis.</li>
                        <li>Secure messaging between clients and trainers.</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">3. Not Medical Advice</h2>
                    <div className="bg-amber-950/30 border border-amber-800/50 rounded-lg p-4">
                        <p className="text-amber-200 font-medium">⚠️ Important Disclaimer</p>
                        <p className="mt-2">
                            The Service is a <strong>fitness and performance tool</strong>, not a medical device.
                            AI-generated recommendations are for informational purposes only and do not constitute medical advice,
                            diagnosis, or treatment. Always consult a qualified healthcare professional before making decisions
                            based on biometric data or AI recommendations.
                        </p>
                        <p className="mt-2">
                            If you experience chest pain, dizziness, or any medical emergency, contact emergency services immediately.
                            Do not rely on this Service for medical decisions.
                        </p>
                    </div>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">4. Accounts & Access</h2>
                    <ul className="list-disc list-inside space-y-1">
                        <li>You must provide accurate information when creating an account.</li>
                        <li>You are responsible for maintaining the security of your login credentials.</li>
                        <li><strong>Client accounts</strong> are assigned to a trainer. Your trainer can view your data.</li>
                        <li><strong>Trainer accounts</strong> have elevated access to manage client dashboards and alerts.</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">5. Acceptable Use</h2>
                    <p>You agree not to:</p>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                        <li>Use the Service for any unlawful purpose.</li>
                        <li>Upload content that is offensive, harmful, or violates third-party rights.</li>
                        <li>Attempt to reverse-engineer, scrape, or exploit the AI models or API.</li>
                        <li>Share your account credentials with others.</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">6. Intellectual Property</h2>
                    <p>
                        All content, design, and AI models within the Service are owned by [Your Company Name].
                        You retain ownership of data you upload (photos, videos, messages), but grant us a limited licence
                        to process it for Service delivery.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">7. Limitation of Liability</h2>
                    <p>
                        To the maximum extent permitted by law, [Your Company Name] shall not be liable for any indirect,
                        incidental, or consequential damages arising from your use of the Service, including but not limited to:
                    </p>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                        <li>Injuries resulting from following AI-generated fitness recommendations.</li>
                        <li>Data loss due to service outages or technical failures.</li>
                        <li>Inaccurate biometric readings from third-party wearable devices.</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">8. Termination</h2>
                    <p>
                        You may delete your account at any time via Settings &rarr; Delete Account.
                        We may suspend or terminate your access if you violate these Terms.
                        Upon termination, your data will be handled in accordance with our{' '}
                        <Link href="/privacy" className="text-blue-400 hover:text-blue-300 underline">Privacy Policy</Link>.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">9. Changes to Terms</h2>
                    <p>
                        We may update these Terms from time to time. Material changes will be communicated via the Service
                        or email. Continued use after changes constitutes acceptance.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">10. Governing Law</h2>
                    <p>
                        These Terms are governed by the laws of England and Wales.
                        Any disputes shall be subject to the exclusive jurisdiction of the courts of England and Wales.
                    </p>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-white mb-2">11. Contact</h2>
                    <p>
                        For questions about these Terms, contact:<br />
                        <strong>legal@eliteconcierge.ai</strong>
                    </p>
                </div>

            </section>

            <div className="mt-12 pt-8 border-t border-zinc-800 text-zinc-600 text-sm">
                <Link href="/privacy" className="hover:text-white">Privacy Policy</Link>
            </div>
        </main>
    );
}
