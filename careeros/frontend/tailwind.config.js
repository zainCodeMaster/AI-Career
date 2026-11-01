/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Brand colors - blue/indigo/violet palette
        brand: {
          50: '#f0f4ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#6366f1',  // Primary indigo
          600: '#4f46e5',  // Primary indigo dark
          700: '#4338ca',  // Primary indigo darker
          800: '#3730a3',
          900: '#312e81',
          950: '#1e1b4b',
        },
        brandViolet: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
          950: '#2e1065',
        },
        brandBlue: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#172554',
        },
        // Dark surfaces - deep navy/charcoal
        surface: {
          DEFAULT: '#0f172a',      // slate-950
          elevated: '#1e293b',     // slate-900
          muted: '#0f172a',        // slate-950
          overlay: 'rgba(0, 0, 0, 0.7)',
          card: '#1e293b',         // slate-900
          cardHover: '#334155',    // slate-700
          border: '#334155',       // slate-700
          borderMuted: '#1e293b',  // slate-900
          input: '#0f172a',        // slate-950
          inputBorder: '#334155',  // slate-700
        },
        // Text colors for dark mode
        text: {
          primary: '#f1f5f9',      // slate-100
          secondary: '#cbd5e1',    // slate-300
          muted: '#94a3b8',        // slate-400
          inverse: '#0f172a',      // slate-950
        },
        // Status colors (preserved from original)
        status: {
          saved: '#94a3b8',        // slate-400
          ready_to_apply: '#60a5fa',    // blue-400
          applied: '#a78bfa',           // violet-400
          application_viewed: '#818cf8', // indigo-400
          screening: '#fbbf24',         // amber-400
          interview: '#fb923c',         // orange-400
          technical_interview: '#f87171', // red-400
          final_interview: '#ef4444',   // red-500
          offer: '#34d399',             // emerald-400
          accepted: '#10b981',          // emerald-500
          rejected: '#f87171',          // red-400
          withdrawn: '#94a3b8',         // slate-400
          expired: '#94a3b8',           // slate-400
          on_hold: '#fbbf24',           // amber-400
        },
        // Semantic colors
        success: {
          DEFAULT: '#22c55e',
          light: '#052e16',
          dark: '#16a34a',
        },
        warning: {
          DEFAULT: '#f59e0b',
          light: '#422006',
          dark: '#d97706',
        },
        error: {
          DEFAULT: '#ef4444',
          light: '#450a0a',
          dark: '#dc2626',
        },
        info: {
          DEFAULT: '#3b82f6',
          light: '#1e3a8a',
          dark: '#2563eb',
        },
      },
      spacing: {
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      borderRadius: {
        'sm': '6px',
        'DEFAULT': '8px',
        'md': '10px',
        'lg': '12px',
        'xl': '16px',
        '2xl': '20px',
        'full': '9999px',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
        'DEFAULT': '0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px -1px rgba(0, 0, 0, 0.3)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.3)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -4px rgba(0, 0, 0, 0.3)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.3)',
        'glow': '0 0 20px rgba(99, 102, 241, 0.3)',
        'glow-violet': '0 0 20px rgba(139, 92, 246, 0.3)',
        'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.2)',
      },
      fontSize: {
        'display': ['2.5rem', { lineHeight: '1.1', fontWeight: '700', letterSpacing: '-0.02em' }],
        'h1': ['1.75rem', { lineHeight: '1.2', fontWeight: '600', letterSpacing: '-0.01em' }],
        'h2': ['1.375rem', { lineHeight: '1.3', fontWeight: '600', letterSpacing: '-0.01em' }],
        'h3': ['1.125rem', { lineHeight: '1.4', fontWeight: '600' }],
        'h4': ['1rem', { lineHeight: '1.5', fontWeight: '600' }],
        'body': ['0.9375rem', { lineHeight: '1.6' }],
        'body-sm': ['0.875rem', { lineHeight: '1.5' }],
        'label': ['0.75rem', { lineHeight: '1', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.05em' }],
        'caption': ['0.75rem', { lineHeight: '1.4', color: '#94a3b8' }],
        'metadata': ['0.8125rem', { lineHeight: '1.4', color: '#94a3b8' }],
        'numeric': ['0.9375rem', { lineHeight: '1.4', fontWeight: '600', fontVariantNumeric: 'tabular-nums' }],
      },
      maxWidth: {
        'content': '72rem',
        'narrow': '54rem',
        'wide': '88rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-soft': 'pulseSoft 2s infinite',
        'shimmer': 'shimmer 1.5s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'mesh-gradient': 'radial-gradient(ellipse at 0% 0%, rgba(99, 102, 241, 0.15) 0%, transparent 50%), radial-gradient(ellipse at 100% 100%, rgba(139, 92, 246, 0.15) 0%, transparent 50%)',
      },
    },
  },
  plugins: [],
}