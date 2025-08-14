# Zeblit Frontend - Replit Setup

This is the frontend for the Zeblit AI Development Platform.

## Setup on Replit

1. **Create a new Repl**
   - Choose "Import from GitHub" or upload the files
   - Select "Node.js" as the template

2. **Setup Instructions**
   ```bash
   # If using the provided package.json.replit, rename it first:
   mv package.json.replit package.json
   
   # Install dependencies
   npm install
   
   # Start the development server
   npm run dev
   ```

3. **Environment Variables**
   Create a `.env` file with:
   ```
   VITE_API_URL=http://localhost:8000/api/v1
   VITE_WS_URL=ws://localhost:8000/api/v1/ws/connect
   VITE_APP_NAME="AI Development Platform"
   VITE_APP_VERSION=0.1.0
   ```

   For testing without backend, you can use mock mode:
   ```
   VITE_API_URL=https://jsonplaceholder.typicode.com
   VITE_MOCK_MODE=true
   ```

4. **Important Files to Check**
   - `src/pages/Dashboard.tsx` - Main dashboard component
   - `src/lib/api-client.ts` - API configuration
   - `tailwind.config.js` - Tailwind CSS configuration
   - `src/index.css` - Global styles

## Design Focus Areas

1. **Dashboard (`src/pages/Dashboard.tsx`)**
   - Project cards layout
   - Color scheme improvements
   - Better visual hierarchy
   - Responsive design

2. **Project Detail Page (`src/pages/ProjectDetail.tsx`)**
   - Code editor layout
   - Agent chat interface
   - File explorer design

3. **New Project Page (`src/pages/NewProject.tsx`)**
   - Template selection UI
   - Form design
   - Better user flow

## Current Design
- Dark theme (gray-900 background)
- Blue accent color (blue-600)
- Card-based layout
- Tailwind CSS utility classes

## Suggested Improvements
- Add more visual interest with gradients
- Improve typography hierarchy
- Add subtle animations
- Better empty states
- More polished form inputs
- Enhanced loading states

## Running Locally
The app will be available at the Replit preview URL. Use the Webview panel to see your changes in real-time. 