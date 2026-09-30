/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'aged-paper': '#faf8f5',
        'ink-black': '#000000',
        'charcoal': '#27251e',
        'ash-gray': '#72706b',
        'stone': '#92918b',
        'pebble': '#d1d1cd',
        'deep-teal': '#016a71',
        'subtle-fill': '#e8e6e1',
        'skeleton-bar': '#f0eeea',
      },
      fontFamily: {
        pplxSans: ['pplxSans', 'Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'subtle': 'rgba(0, 0, 0, 0.08) 0px 1px 2px 0px',
      },
      maxWidth: {
        'content': '640px',
      },
      borderRadius: {
        'pill': '9999px',
        'input': '12px',
        'card': '16px',
        'chip': '6px',
      }
    },
  },
  plugins: [],
}
