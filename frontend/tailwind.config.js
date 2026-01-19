/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                xierra: {
                    bg: '#050505',      // Deep void black
                    card: '#0a0a0a',    // Very dark card background
                    border: '#333333',  // Subtle border
                    text: '#e5e5e5',    // Primary text (off-white)
                    muted: '#737373',   // Secondary text
                    accent: '#ffffff',  // High contrast accent
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            animation: {
                'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }
        },
    },
    plugins: [],
}
