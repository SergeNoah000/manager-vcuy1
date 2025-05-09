module.exports = {
  darkMode: 'class',
  content: ['./pages/**/*.{js,ts,jsx,tsx}', './components/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#121212',
          800: '#1E1E1E',
          700: '#2A2A2A',
          600: '#333333',
          500: '#444444',
        },
        primary: {
          DEFAULT: '#4F46E5',
          dark: '#3730A3',
        },
        accent: {
          DEFAULT: '#22D3EE',
          dark: '#0E7490',
        },
      },
    },
  },
  plugins: [],
};