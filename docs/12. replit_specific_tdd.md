# Technical Design Document (TDD)
## CyberScale AI Hackathon Platform

### Document Information
- **Document Version:** 1.0
- **Last Updated:** July 3, 2025
- **Author:** CyberScale AI Team
- **Review Cycle:** Quarterly

---

## Table of Contents
1. [System Architecture Overview](#system-architecture-overview)
2. [Frontend Architecture](#frontend-architecture)
3. [Backend Architecture](#backend-architecture)
4. [Database Design](#database-design)
5. [External Integrations](#external-integrations)
6. [Development Tools & Build System](#development-tools--build-system)
7. [Security Implementation](#security-implementation)
8. [Performance Optimization](#performance-optimization)
9. [Deployment Architecture](#deployment-architecture)
10. [Monitoring & Logging](#monitoring--logging)

---

## System Architecture Overview

### High-Level Architecture
The CyberScale AI Hackathon Platform follows a modern **three-tier architecture** pattern:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Presentation  │    │   Application   │    │      Data       │
│     Layer       │◄──►│     Layer       │◄──►│     Layer       │
│                 │    │                 │    │                 │
│ React 18 + Vite │    │ Express.js +    │    │ PostgreSQL +    │
│ TypeScript      │    │ Node.js         │    │ Drizzle ORM     │
│ Tailwind CSS    │    │ TypeScript      │    │ Neon Database   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Technology Stack Summary
- **Frontend Runtime:** React 18.3.1 with TypeScript 5.6.3
- **Backend Runtime:** Node.js 20.18.1 with Express.js 4.21.1
- **Database:** PostgreSQL 16 via Neon Database (serverless)
- **Build System:** Vite 6.0.5 with esbuild bundling
- **Package Manager:** npm 10.8.2
- **Deployment Platform:** Replit Autoscale with persistent storage

---

## Frontend Architecture

### Core Framework Stack

#### React 18.3.1
- **Concurrent Features:** Utilized for better UX with Suspense boundaries
- **Strict Mode:** Enabled for development-time error detection
- **JSX Transform:** Automatic JSX runtime (no explicit React imports needed)
- **Component Architecture:** Functional components with hooks exclusively

#### TypeScript 5.6.3
- **Configuration:** Strict mode enabled with all type checking flags
- **Module Resolution:** Node16 resolution for modern ES modules
- **Target:** ES2022 for modern browser features
- **Path Mapping:** Absolute imports using `@/` prefix for cleaner imports

#### Routing - Wouter 3.3.5
```typescript
// Route structure implementation
<Switch>
  <Route path="/" component={DashboardPage} />
  <Route path="/dashboard" component={DashboardPage} />
  <Route path="/teams" component={TeamsPage} />
  <Route path="/team/:id">
    {(params) => <TeamDetailPage id={parseInt(params.id)} />}
  </Route>
  <Route path="/teams/:id">
    {(params) => <Redirect to={`/team/${params.id}`} />}
  </Route>
  // Additional routes...
</Switch>
```
- **Size:** 2.7KB minified + gzipped (compared to React Router's 13KB)
- **Features:** Hook-based navigation, pattern matching, nested routing
- **Performance:** Zero dependencies, tree-shakeable

### State Management

#### TanStack Query (React Query) 5.62.7
```typescript
// Query configuration example
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount, error) => {
        if (error?.status === 401) return false;
        return failureCount < 3;
      },
    },
  },
});
```
- **Cache Management:** Intelligent background refetching and stale-while-revalidate
- **Optimistic Updates:** Immediate UI updates for better UX
- **Error Boundaries:** Automatic error handling with retry logic
- **DevTools:** Integrated React Query DevTools for debugging

### UI Component System

#### Radix UI Primitives
Complete headless component library with accessibility built-in:

```typescript
// Component library breakdown
"@radix-ui/react-accordion": "^1.2.1",
"@radix-ui/react-alert-dialog": "^1.1.2",
"@radix-ui/react-aspect-ratio": "^1.1.0",
"@radix-ui/react-avatar": "^1.1.1",
"@radix-ui/react-checkbox": "^1.1.2",
"@radix-ui/react-collapsible": "^1.1.1",
"@radix-ui/react-context-menu": "^2.2.2",
"@radix-ui/react-dialog": "^1.1.2",
"@radix-ui/react-dropdown-menu": "^2.1.2",
"@radix-ui/react-hover-card": "^1.1.2",
"@radix-ui/react-label": "^2.1.0",
"@radix-ui/react-menubar": "^1.1.2",
"@radix-ui/react-navigation-menu": "^1.2.1",
"@radix-ui/react-popover": "^1.1.2",
"@radix-ui/react-progress": "^1.1.0",
"@radix-ui/react-radio-group": "^1.2.1",
"@radix-ui/react-scroll-area": "^1.2.0",
"@radix-ui/react-select": "^2.1.2",
"@radix-ui/react-separator": "^1.1.0",
"@radix-ui/react-slider": "^1.2.1",
"@radix-ui/react-slot": "^1.1.0",
"@radix-ui/react-switch": "^1.1.1",
"@radix-ui/react-tabs": "^1.1.1",
"@radix-ui/react-toast": "^1.2.2",
"@radix-ui/react-toggle": "^1.1.0",
"@radix-ui/react-toggle-group": "^1.1.0",
"@radix-ui/react-tooltip": "^1.1.3"
```

#### shadcn/ui Components
Custom component system built on Radix UI with Tailwind styling:
- **Copy-paste Architecture:** Components copied into project for full customization
- **Consistent API:** Standardized props and styling patterns
- **Accessibility:** WCAG 2.1 AA compliance out of the box
- **Theming:** CSS custom properties for dynamic theming

### Styling System

#### Tailwind CSS 3.4.17
```typescript
// Configuration excerpt
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Cyberpunk theme colors
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: "hsl(var(--primary))",
        secondary: "hsl(var(--secondary))",
        accent: "hsl(var(--accent))",
        // ... additional custom colors
      },
    },
  },
}
```

#### Additional Styling Dependencies
- **@tailwindcss/typography:** Rich text styling for markdown content
- **@tailwindcss/vite:** Vite plugin for optimal Tailwind integration
- **tailwindcss-animate:** CSS animations and transitions
- **class-variance-authority:** Type-safe component variant system
- **clsx:** Conditional className utility
- **tailwind-merge:** Intelligent Tailwind class merging

### Form Management

#### React Hook Form 7.54.2
```typescript
// Form implementation pattern
const form = useForm<FormData>({
  resolver: zodResolver(schema),
  defaultValues: {
    email: "",
    password: "",
  },
});
```
- **Validation:** Zod schema validation via @hookform/resolvers/zod
- **Performance:** Uncontrolled components for minimal re-renders
- **TypeScript:** Full type safety with form data types

#### Zod Validation 3.24.1
```typescript
// Schema definition example
const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
});
```

### Icon Systems
- **Lucide React 0.468.0:** 1000+ consistent SVG icons
- **React Icons 5.4.0:** Popular icon libraries (specifically `react-icons/si` for company logos)

### Additional Frontend Libraries
- **Framer Motion 11.15.0:** Production-ready motion library for animations
- **date-fns 4.1.0:** Lightweight date utility library
- **next-themes 0.4.4:** Theme management for dark/light mode
- **cmdk 1.0.4:** Command palette component
- **input-otp 1.4.1:** OTP input component
- **react-day-picker 9.4.4:** Date picker component
- **react-resizable-panels 2.1.7:** Resizable panel layouts
- **recharts 2.13.3:** Chart components for data visualization
- **vaul 1.1.2:** Drawer component for mobile interfaces
- **embla-carousel-react 8.5.2:** Carousel/slider component

---

## Backend Architecture

### Core Runtime Environment

#### Node.js 20.18.1
- **ES Modules:** Full ESM support with `.js` extension imports
- **V8 Engine:** Latest JavaScript engine features
- **Memory Management:** Optimized for server-side applications
- **Security:** Latest security patches and updates

#### Express.js 4.21.1
```typescript
// Server configuration
const app = express();

// Middleware stack
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? ['https://aihackathon.app'] 
    : ['http://localhost:5000'],
  credentials: true
}));

// Session configuration
app.use(session({
  secret: process.env.JWT_SECRET!,
  resave: false,
  saveUninitialized: false,
  store: new (require('connect-pg-simple')(session))({
    pool: pool,
    tableName: 'session'
  }),
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));
```

#### TypeScript 5.6.3 (Backend)
- **tsx 4.19.2:** TypeScript execution for development and production
- **Build Target:** ES2022 with Node.js compatibility
- **Module System:** ESM with proper import/export syntax
- **Type Definitions:** Comprehensive type coverage for all dependencies

### Authentication & Security

#### JSON Web Tokens
- **jsonwebtoken 9.0.2:** JWT creation and verification
- **bcryptjs 2.4.3:** Password hashing with salt rounds of 12
- **passport 0.7.0:** Authentication middleware
- **passport-local 1.0.0:** Local strategy for email/password auth

#### Session Management
- **express-session 1.18.1:** Server-side session handling
- **connect-pg-simple 10.0.0:** PostgreSQL session store
- **cookie-parser 1.4.7:** Cookie parsing middleware
- **memorystore 1.6.7:** Fallback memory session store

### File Upload System

#### Multer 1.4.5-lts.1
```typescript
// File upload configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const sanitizedName = file.originalname.replace(/[^a-zA-Z0-9.-]/g, '_');
    cb(null, `${Date.now()}-${sanitizedName}`);
  }
});

const upload = multer({
  storage: storage,
  fileFilter: (req, file, cb) => {
    const allowedTypes = ['application/pdf', 'text/markdown'];
    cb(null, allowedTypes.includes(file.mimetype));
  },
  limits: {
    fileSize: 50 * 1024 * 1024 // 50MB
  }
});
```

### Real-time Communication

#### WebSocket Implementation
- **ws 8.18.0:** WebSocket server for real-time updates
- **Connection Management:** Automatic client tracking and cleanup
- **Message Broadcasting:** Real-time notifications for voting, team updates

```typescript
// WebSocket server setup
const wss = new WebSocketServer({ server });
let clients: Set<WebSocket> = new Set();

wss.on('connection', (ws) => {
  clients.add(ws);
  ws.on('close', () => clients.delete(ws));
});

function broadcastToClients(data: any) {
  const message = JSON.stringify(data);
  clients.forEach(client => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  });
}
```

---

## Database Design

### PostgreSQL 16
- **Version:** PostgreSQL 16.x via Neon Database
- **Connection:** Serverless connection pooling
- **SSL:** Required for all connections
- **Backup:** Automated point-in-time recovery

### Neon Database Configuration
```typescript
// Database connection
import { Pool } from '@neondatabase/serverless';

export const pool = new Pool({ 
  connectionString: process.env.DATABASE_URL,
  ssl: {
    rejectUnauthorized: false
  }
});
```

### ORM - Drizzle ORM 0.37.0
```typescript
// Schema definition example
export const users = pgTable('users', {
  id: serial('id').primaryKey(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  name: varchar('name', { length: 255 }).notNull(),
  password: varchar('password', { length: 255 }).notNull(),
  role: varchar('role', { length: 50 }).notNull().default('participant'),
  avatarUrl: varchar('avatar_url', { length: 500 }),
  teamId: integer('team_id').references(() => teams.id),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});
```

#### Drizzle Kit 0.30.1
- **Migrations:** Schema version control and migration management
- **Type Generation:** Automatic TypeScript type generation
- **Push/Pull:** Schema synchronization with database
- **Introspection:** Database schema analysis

### Database Schema Design

#### Core Tables
1. **users** - User authentication and profile information
2. **teams** - Team information and metadata
3. **ideas** - Problem/solution documentation
4. **demos** - Demo submission details
5. **files** - File upload metadata and references
6. **votes** - Individual vote records
7. **voting_criteria** - Configurable voting criteria
8. **voting_settings** - Global voting configuration
9. **agenda** - Event schedule management
10. **winners** - Final competition results

#### Relationships
```sql
-- Foreign key relationships
users.teamId → teams.id
ideas.teamId → teams.id
demos.teamId → teams.id
files.teamId → teams.id
votes.voterId → users.id
votes.teamId → teams.id
winners.teamId → teams.id
```

---

## External Integrations

### OpenAI API Integration

#### OpenAI 4.75.1
```typescript
// OpenAI client configuration
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

// GPT-4 for idea feedback
const completion = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [
    {
      role: "system",
      content: "You are a cybersecurity expert providing feedback on hackathon ideas..."
    },
    {
      role: "user", 
      content: `Problem: ${problem}\nSolution: ${solution}`
    }
  ],
  max_tokens: 500,
  temperature: 0.7,
});

// DALL-E 3 for avatar generation
const response = await openai.images.generate({
  model: "dall-e-3",
  prompt: "A circular cybersecurity team avatar...",
  size: "1024x1024",
  quality: "standard",
  n: 1,
});
```

#### Rate Limiting & Error Handling
```typescript
// Rate limit handling with exponential backoff
async function handleRateLimit(apiCall: () => Promise<any>, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error: any) {
      if (error.status === 429) {
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }
      throw error;
    }
  }
}
```

### Email Service Integration

#### Resend 4.0.1
```typescript
// Email service configuration
import { Resend } from 'resend';

const resend = new Resend(process.env.RESEND_API_KEY);

// Email template system
const sendWelcomeEmail = async (userData: any) => {
  const emailData = {
    from: 'CyberScale Hackathon <noreply@aihackathon.app>',
    to: [userData.email],
    subject: 'Welcome to CyberScale AI Hackathon!',
    html: generateWelcomeTemplate(userData),
  };
  
  return await resend.emails.send(emailData);
};
```

#### Email Templates
- **Welcome Email:** User onboarding with credentials
- **Password Reset:** Secure password reset functionality
- **Event Notifications:** Agenda updates and announcements

---

## Development Tools & Build System

### Vite 6.0.5 Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [
    react(),
    cartographer(),
    runtimeErrorModal()
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./client/src"),
      "@shared": path.resolve(__dirname, "./shared"),
      "@assets": path.resolve(__dirname, "./assets"),
    },
  },
  server: {
    port: 5000,
    proxy: {
      '/api': 'http://localhost:5000',
      '/uploads': 'http://localhost:5000',
    }
  },
  build: {
    outDir: './dist/public',
    sourcemap: true,
    rollupOptions: {
      external: ['fs', 'path']
    }
  }
});
```

### Replit-Specific Plugins
- **@replit/vite-plugin-cartographer:** Code navigation and project mapping
- **@replit/vite-plugin-runtime-error-modal:** Enhanced error reporting

### Build Tools
- **esbuild 0.24.2:** Fast JavaScript/TypeScript bundler
- **postcss 8.5.1:** CSS processing pipeline
- **autoprefixer 10.4.20:** Automatic vendor prefixing

### TypeScript Configuration
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./client/src/*"],
      "@shared/*": ["./shared/*"]
    }
  }
}
```

---

## Security Implementation

### Password Security
```typescript
// Password hashing with bcrypt
import bcrypt from 'bcryptjs';

const hashPassword = async (password: string): Promise<string> => {
  return await bcrypt.hash(password, 12); // 12 salt rounds
};

const verifyPassword = async (password: string, hash: string): Promise<boolean> => {
  return await bcrypt.compare(password, hash);
};
```

### JWT Security
```typescript
// JWT token management
import jwt from 'jsonwebtoken';

const generateToken = (userId: number): string => {
  return jwt.sign(
    { userId },
    process.env.JWT_SECRET!,
    { 
      expiresIn: '24h',
      algorithm: 'HS256'
    }
  );
};

const verifyToken = (token: string): any => {
  return jwt.verify(token, process.env.JWT_SECRET!);
};
```

### Input Validation
- **Zod 3.24.1:** Runtime type validation for all API endpoints
- **drizzle-zod 0.5.1:** Database schema validation
- **File Upload Validation:** MIME type and size restrictions

### CORS Configuration
```typescript
// CORS security settings
app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? ['https://aihackathon.app'] 
    : ['http://localhost:5000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));
```

---

## Performance Optimization

### Frontend Optimization
- **Code Splitting:** Automatic route-based code splitting via Vite
- **Tree Shaking:** Dead code elimination for smaller bundles
- **Asset Optimization:** Image and static asset compression
- **Browser Caching:** Optimized cache headers for static assets

### Backend Optimization
- **Connection Pooling:** Database connection pooling via Neon
- **Query Optimization:** Efficient database queries with proper indexing
- **Response Compression:** Gzip compression for API responses
- **Static File Serving:** Efficient static file delivery

### Database Optimization
```sql
-- Key indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_teams_id ON teams(id);
CREATE INDEX idx_votes_team_id ON votes(team_id);
CREATE INDEX idx_votes_voter_id ON votes(voter_id);
CREATE INDEX idx_files_team_id ON files(team_id);
```

### Caching Strategy
- **Client-side:** TanStack Query caching with stale-while-revalidate
- **Server-side:** Session storage with PostgreSQL backing
- **Static Assets:** CDN-style caching for uploaded files

---

## Deployment Architecture

### Replit Autoscale Platform
- **Runtime:** Node.js 20.18.1 with automatic scaling
- **Process Management:** PM2-style process management
- **Health Checks:** Automatic health monitoring and restart
- **SSL/TLS:** Automatic HTTPS certificate management

### Environment Configuration
```bash
# Required environment variables
DATABASE_URL=postgresql://...
JWT_SECRET=your-secret-key
OPENAI_API_KEY=sk-...
RESEND_API_KEY=re_...
NODE_ENV=production
```

### Build Process
```json
// package.json scripts
{
  "scripts": {
    "dev": "NODE_ENV=development tsx server/index.ts",
    "build": "vite build && tsc server/index.ts --outDir dist --target ES2022",
    "start": "NODE_ENV=production node dist/index.js",
    "db:push": "drizzle-kit push",
    "db:generate": "drizzle-kit generate"
  }
}
```

### Static File Serving
```typescript
// Static file configuration
app.use('/uploads', express.static('uploads', {
  maxAge: '1d',
  etag: true,
  lastModified: true
}));

app.use(express.static('dist/public', {
  maxAge: '1y',
  etag: true,
  immutable: true
}));
```

---

## Monitoring & Logging

### Application Logging
```typescript
// Custom logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    const log = `${new Date().toISOString()} [express] ${req.method} ${req.path} ${res.statusCode} in ${duration}ms`;
    
    if (req.body && Object.keys(req.body).length > 0) {
      const sanitizedBody = { ...req.body };
      if (sanitizedBody.password) sanitizedBody.password = '[REDACTED]';
      log += ` :: ${JSON.stringify(sanitizedBody).substring(0, 100)}...`;
    }
    
    console.log(log);
  });
  
  next();
});
```

### Error Handling
```typescript
// Global error handler
app.use((err: any, req: Request, res: Response, next: NextFunction) => {
  console.error(`${new Date().toISOString()} [ERROR] ${err.stack}`);
  
  if (process.env.NODE_ENV === 'production') {
    res.status(500).json({ error: 'Internal server error' });
  } else {
    res.status(500).json({ 
      error: err.message,
      stack: err.stack 
    });
  }
});
```

### Health Monitoring
- **Uptime Monitoring:** Application availability tracking
- **Performance Metrics:** Response time and throughput monitoring
- **Error Tracking:** Real-time error detection and alerting
- **Database Health:** Connection and query performance monitoring

---

## Development Workflow

### Local Development Setup
```bash
# Installation
npm install

# Database setup
npm run db:push

# Development server
npm run dev
```

### Code Quality Tools
- **ESLint:** JavaScript/TypeScript linting
- **Prettier:** Code formatting (configured via Vite)
- **TypeScript:** Static type checking
- **Husky:** Git hooks for pre-commit validation

### Testing Strategy
- **Manual Testing:** Comprehensive feature testing via UI
- **API Testing:** Postman/cURL testing for all endpoints
- **Database Testing:** Reset scripts for clean testing environments
- **Load Testing:** Performance testing with realistic user loads

### Version Control
- **Git:** Source code management
- **Branching Strategy:** Feature branches with main deployment
- **Commit Conventions:** Conventional commits for automated changelog
- **Release Process:** Tagged releases with semantic versioning

---

## Future Technical Considerations

### Scalability Improvements
- **Microservices:** Potential service decomposition for larger scale
- **Caching Layer:** Redis implementation for session and query caching
- **CDN Integration:** Global content delivery for static assets
- **Database Sharding:** Horizontal scaling for large datasets

### Technology Upgrades
- **React 19:** Concurrent features and server components
- **Node.js 22:** Latest LTS features and performance improvements
- **PostgreSQL 17:** Enhanced JSON and performance features
- **Drizzle 1.0:** Stable API and enhanced features

### Monitoring Enhancements
- **APM Integration:** Application Performance Monitoring
- **Distributed Tracing:** Request tracing across services
- **Custom Metrics:** Business-specific KPI tracking
- **Alerting System:** Proactive issue detection and notification

---

## Appendix

### Package Versions (Complete List)
```json
{
  "dependencies": {
    "@hookform/resolvers": "^3.10.0",
    "@neondatabase/serverless": "^0.10.3",
    "@radix-ui/react-accordion": "^1.2.1",
    "@radix-ui/react-alert-dialog": "^1.1.2",
    "@radix-ui/react-aspect-ratio": "^1.1.0",
    "@radix-ui/react-avatar": "^1.1.1",
    "@radix-ui/react-checkbox": "^1.1.2",
    "@radix-ui/react-collapsible": "^1.1.1",
    "@radix-ui/react-context-menu": "^2.2.2",
    "@radix-ui/react-dialog": "^1.1.2",
    "@radix-ui/react-dropdown-menu": "^2.1.2",
    "@radix-ui/react-hover-card": "^1.1.2",
    "@radix-ui/react-label": "^2.1.0",
    "@radix-ui/react-menubar": "^1.1.2",
    "@radix-ui/react-navigation-menu": "^1.2.1",
    "@radix-ui/react-popover": "^1.1.2",
    "@radix-ui/react-progress": "^1.1.0",
    "@radix-ui/react-radio-group": "^1.2.1",
    "@radix-ui/react-scroll-area": "^1.2.0",
    "@radix-ui/react-select": "^2.1.2",
    "@radix-ui/react-separator": "^1.1.0",
    "@radix-ui/react-slider": "^1.2.1",
    "@radix-ui/react-slot": "^1.1.0",
    "@radix-ui/react-switch": "^1.1.1",
    "@radix-ui/react-tabs": "^1.1.1",
    "@radix-ui/react-toast": "^1.2.2",
    "@radix-ui/react-toggle": "^1.1.0",
    "@radix-ui/react-toggle-group": "^1.1.0",
    "@radix-ui/react-tooltip": "^1.1.3",
    "@replit/vite-plugin-cartographer": "^1.0.3",
    "@replit/vite-plugin-runtime-error-modal": "^1.0.0",
    "@sendgrid/mail": "^8.1.4",
    "@tailwindcss/typography": "^0.5.15",
    "@tailwindcss/vite": "^4.0.0-alpha.31",
    "@tanstack/react-query": "^5.62.7",
    "bcryptjs": "^2.4.3",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "cmdk": "^1.0.4",
    "connect-pg-simple": "^10.0.0",
    "cookie-parser": "^1.4.7",
    "date-fns": "^4.1.0",
    "drizzle-kit": "^0.30.1",
    "drizzle-orm": "^0.37.0",
    "drizzle-zod": "^0.5.1",
    "embla-carousel-react": "^8.5.2",
    "esbuild": "^0.24.2",
    "express": "^4.21.1",
    "express-session": "^1.18.1",
    "framer-motion": "^11.15.0",
    "input-otp": "^1.4.1",
    "jsonwebtoken": "^9.0.2",
    "lucide-react": "^0.468.0",
    "memorystore": "^1.6.7",
    "multer": "^1.4.5-lts.1",
    "next-themes": "^0.4.4",
    "openai": "^4.75.1",
    "passport": "^0.7.0",
    "passport-local": "^1.0.0",
    "postcss": "^8.5.1",
    "react": "^18.3.1",
    "react-day-picker": "^9.4.4",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.54.2",
    "react-icons": "^5.4.0",
    "react-resizable-panels": "^2.1.7",
    "recharts": "^2.13.3",
    "resend": "^4.0.1",
    "tailwind-merge": "^2.6.0",
    "tailwindcss": "^3.4.17",
    "tailwindcss-animate": "^1.0.7",
    "tsx": "^4.19.2",
    "tw-animate-css": "^0.1.0",
    "typescript": "^5.6.3",
    "vaul": "^1.1.2",
    "vite": "^6.0.5",
    "wouter": "^3.3.5",
    "ws": "^8.18.0",
    "zod": "^3.24.1",
    "zod-validation-error": "^3.4.0"
  },
  "devDependencies": {
    "@jridgewell/trace-mapping": "^0.3.25",
    "@types/bcryptjs": "^2.4.6",
    "@types/connect-pg-simple": "^7.0.3",
    "@types/cookie-parser": "^1.4.7",
    "@types/express": "^5.0.0",
    "@types/express-session": "^1.18.0",
    "@types/jsonwebtoken": "^9.0.7",
    "@types/multer": "^1.4.12",
    "@types/node": "^22.10.1",
    "@types/passport": "^1.0.16",
    "@types/passport-local": "^1.0.38",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@types/ws": "^8.5.13",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20"
  }
}
```

### File Structure
```
├── client/                     # Frontend React application
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── lib/              # Utility libraries
│   │   ├── hooks/            # Custom React hooks
│   │   └── App.tsx           # Main application component
├── server/                    # Backend Express application
│   ├── db.ts                 # Database connection
│   ├── index.ts              # Main server file
│   ├── routes.ts             # API route definitions
│   └── services/             # Business logic services
├── shared/                    # Shared types and schemas
│   └── schema.ts             # Database schema definitions
├── docs/                     # Documentation
├── scripts/                  # Database management scripts
├── uploads/                  # File storage directory
└── dist/                     # Build output directory
```

---

**Document Maintenance:**
This technical design document should be updated whenever:
- New dependencies are added or updated
- Architecture patterns change
- Security implementations are modified
- Performance optimizations are implemented
- Deployment configurations change

**Review Schedule:** Quarterly technical review with architecture updates as needed.