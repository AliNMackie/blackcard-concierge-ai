/** @type {import('next').NextConfig} */
const withPWA = require('next-pwa')({
    dest: 'public',
    register: true,
    skipWaiting: true,
    disable: process.env.NODE_ENV === 'development',
    runtimeCaching: [
        {
            // Cache API calls (stale-while-revalidate for offline support)
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
                cacheName: 'api-cache',
                networkTimeoutSeconds: 10,
                expiration: { maxEntries: 50, maxAgeSeconds: 300 },
            },
        },
        {
            // Cache health/events endpoints
            urlPattern: /^https?:\/\/.*\/(health|events).*/i,
            handler: 'NetworkFirst',
            options: {
                cacheName: 'backend-cache',
                networkTimeoutSeconds: 10,
                expiration: { maxEntries: 30, maxAgeSeconds: 60 },
            },
        },
        {
            // Cache static assets aggressively
            urlPattern: /\.(?:js|css|woff2?|png|jpg|jpeg|gif|svg|ico)$/i,
            handler: 'CacheFirst',
            options: {
                cacheName: 'static-assets',
                expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 * 30 }, // 30 days
            },
        },
        {
            // Cache Next.js pages (navigation works offline)
            urlPattern: /^https?:\/\/.*\/(?:dashboard|messages|performance|login|privacy|terms).*$/i,
            handler: 'StaleWhileRevalidate',
            options: {
                cacheName: 'pages-cache',
                expiration: { maxEntries: 20, maxAgeSeconds: 60 * 60 * 24 },
            },
        },
    ],
});

const nextConfig = {
    // Add other Next.js config here if needed
};

module.exports = withPWA(nextConfig);
