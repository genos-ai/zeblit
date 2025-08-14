# Replit Project Setup Prompt

Please help me set up a React + TypeScript + Tailwind CSS project for enhancing the UI design of my AI Development Platform called "Zeblit".

## Project Requirements

1. **Create a new Node.js Repl**
2. **Upload or paste the provided frontend code**
3. **Install these dependencies**:

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "axios": "^1.7.9",
    "wouter": "^3.5.2",
    "lucide-react": "^0.469.0",
    "framer-motion": "^11.15.0",
    "@tanstack/react-query": "^5.63.0",
    "react-hook-form": "^7.54.2",
    "zod": "^3.24.1",
    "@hookform/resolvers": "^3.9.1",
    "date-fns": "^4.1.0",
    "react-icons": "^5.4.0"
  },
  "devDependencies": {
    "vite": "^7.0.3",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "~5.6.2",
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "tailwindcss": "^3.4.17",
    "postcss": "^8.4.49",
    "autoprefixer": "^10.4.20"
  }
}
```

## Setup Steps

1. **After creating the Repl**, run in Shell:
```bash
npm install
npm run dev
```

2. **Environment Setup**:
Create a `.env` file with:
```
VITE_API_URL=https://jsonplaceholder.typicode.com
VITE_MOCK_MODE=true
VITE_APP_NAME="AI Development Platform"
VITE_APP_VERSION=0.1.0
```

3. **Key Files to Focus On**:
- `src/pages/Dashboard.tsx` - Main dashboard that needs design improvements
- `src/index.css` - Global styles
- `tailwind.config.js` - Tailwind configuration
- `.replit/DESIGN_PROMPT.md` - Detailed design requirements

## Design Task

I need help making this AI Development Platform UI more modern and visually appealing. The current design is functional but bland. I want:

1. **Modern, futuristic design** that reflects the AI-powered nature of the platform
2. **Better visual hierarchy** with improved typography and spacing
3. **Smooth animations** using Framer Motion
4. **Engaging empty states** and loading animations
5. **Polished components** with hover effects and micro-interactions

The platform is where users interact with AI agents to build applications, similar to Replit but with AI doing the coding.

## Mock Data

The app includes mock data in `.replit/mock-data.js` so you can see how it looks with content. The main areas are:
- Project dashboard showing user's projects
- Project creation flow
- Individual project pages (coming soon)

## Important Notes

- The app runs in "mock mode" since the backend isn't available on Replit
- Focus purely on UI/UX improvements
- Keep the existing component structure but enhance the visuals
- Use Tailwind CSS classes and Framer Motion for animations
- Make it feel premium and AI-native

Please review the `.replit/DESIGN_PROMPT.md` file for detailed design requirements and inspiration! 