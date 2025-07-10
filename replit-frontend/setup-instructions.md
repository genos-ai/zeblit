# Zeblit Frontend - Replit Setup Instructions

## Quick Start

1. **After importing to Replit**, run these commands in the Shell:

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

2. The app will start on port 5173 and Replit will automatically map it to port 80.

## File Structure

```
frontend/
├── .replit/              # Replit configuration files
├── src/
│   ├── components/       # Reusable UI components
│   ├── contexts/        # React contexts (Auth, etc.)
│   ├── hooks/           # Custom React hooks
│   ├── lib/             # Utilities and helpers
│   ├── pages/           # Page components
│   └── types/           # TypeScript type definitions
├── public/              # Static assets
└── package.json         # Dependencies and scripts
```

## Mock Mode

Since the backend isn't available on Replit, the app runs in "mock mode":
- Mock data is provided for projects, users, and templates
- API calls return static data
- Perfect for UI/UX design work

## Key Files to Edit

### 1. Dashboard Design
- `src/pages/Dashboard.tsx` - Main dashboard layout
- Current: Dark theme with project cards
- Improve: Add gradients, animations, better spacing

### 2. Color Scheme
- `tailwind.config.js` - Tailwind configuration
- `src/index.css` - Global styles
- Current: Gray + Blue theme
- Try: Purple gradients, glassmorphism effects

### 3. Components
- `src/components/ui/` - Create reusable UI components
- Add: Loading skeletons, animated cards, better buttons

### 4. New Project Flow
- `src/pages/NewProject.tsx` - Project creation form
- Improve: Template selection UI, form validation feedback

## Design Ideas

### Modern UI Trends to Try:
1. **Glassmorphism**
   ```css
   backdrop-filter: blur(10px);
   background: rgba(255, 255, 255, 0.1);
   ```

2. **Gradient Borders**
   ```css
   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
   ```

3. **Smooth Animations**
   - Use Framer Motion (already installed)
   - Add hover effects to cards
   - Smooth page transitions

4. **Better Empty States**
   - Create illustrated empty states
   - Add helpful CTAs

## Testing Your Changes

1. The preview will auto-reload when you save files
2. Test responsive design by resizing the preview
3. Check dark/light mode if implemented
4. Test all interactive elements

## Exporting Your Work

When done with design improvements:
1. Download the entire project as ZIP
2. Extract and copy changed files back to local project
3. Test with real backend API

## Common Issues

- **Styles not updating?** Hard refresh the preview
- **Build errors?** Check the console in Replit
- **Missing dependencies?** Run `npm install` again

## Resources

- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Framer Motion](https://www.framer.com/motion/)
- [React Icons](https://react-icons.github.io/react-icons/)
- [UI Inspiration](https://dribbble.com/search/dashboard) 