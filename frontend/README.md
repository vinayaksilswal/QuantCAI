# QuantCAI Frontend Development Guide

## Table of Contents
1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Getting Started](#getting-started)
5. [Development Workflow](#development-workflow)
6. [Architecture & Patterns](#architecture--patterns)
7. [Key Features](#key-features)
8. [Authentication & Authorization](#authentication--authorization)
9. [API Integration](#api-integration)
10. [Styling Guidelines](#styling-guidelines)
11. [Component Library](#component-library)
12. [State Management](#state-management)
13. [Routing](#routing)
14. [Environment Variables](#environment-variables)
15. [Building & Deployment](#building--deployment)
16. [Backend Integration Guide](#backend-integration-guide)
17. [Common Tasks](#common-tasks)
18. [Troubleshooting](#troubleshooting)

---

## Project Overview

QuantCAI is a modern web application focused on quantum computing education, simulation, and community engagement. The frontend is built with React 19, TypeScript, and Vite, providing a fast and interactive user experience.

### Key Objectives
- Interactive quantum computing education
- Real-time quantum state visualization
- User authentication and role-based access control
- Community features and content management
- Responsive design with modern UI/UX

---

## Tech Stack

### Core Technologies
- **React 19.2.3** - UI library
- **TypeScript 5.5.3** - Type safety
- **Vite 5.4.1** - Build tool and dev server
- **React Router DOM 7.11.0** - Client-side routing

### UI & Styling
- **Tailwind CSS 3.4.19** - Utility-first CSS framework
- **Radix UI** - Accessible component primitives
- **Lucide React** - Icon library
- **next-themes** - Theme management

### State Management & Data
- **TanStack Query (React Query) 5.90.12** - Server state management
- **React Context API** - Client state management
- **Supabase Client 2.89.0** - Authentication & database (currently used, will be replaced with Python backend)

### Form Handling
- **React Hook Form 7.69.0** - Form state management
- **Zod 4.2.1** - Schema validation
- **@hookform/resolvers** - Form validation integration

### Additional Libraries
- **Recharts 3.6.0** - Charting library
- **Sonner 2.0.7** - Toast notifications
- **Class Variance Authority** - Component variant management

---

## Project Structure

```
frontend/
├── public/                 # Static assets
│   ├── favicon.ico
│   ├── lovable-uploads/    # Image assets
│   └── robots.txt
├── src/
│   ├── components/        # Reusable components
│   │   ├── ui/           # shadcn/ui components
│   │   ├── Footer.tsx
│   │   ├── Navbar.tsx
│   │   ├── NewsletterForm.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── QuantumBackground.tsx
│   │   ├── QuantumGates.tsx
│   │   ├── QuantumStateDisplay.tsx
│   │   ├── QuantumVisualizer.tsx
│   │   ├── LogoProcessor.tsx
│   │   └── VoiceBot.tsx
│   ├── context/          # React Context providers
│   │   └── AuthContext.tsx
│   ├── hooks/            # Custom React hooks
│   │   ├── use-mobile.tsx
│   │   ├── use-toast.ts
│   │   └── usePageTracking.tsx
│   ├── lib/              # Utility libraries
│   │   ├── supabase.ts   # Supabase client (to be replaced)
│   │   └── utils.ts      # Helper functions
│   ├── pages/            # Page components
│   │   ├── Admin.tsx
│   │   ├── Community.tsx
│   │   ├── Developer.tsx
│   │   ├── GetStarted.tsx
│   │   ├── Index.tsx
│   │   ├── Learn.tsx
│   │   ├── Login.tsx
│   │   ├── NotFound.tsx
│   │   ├── Profile.tsx
│   │   ├── QuantumComputing.tsx
│   │   ├── QuantumStates.tsx
│   │   ├── Reddit.tsx
│   │   ├── Soon.tsx
│   │   └── Vision.tsx
│   ├── utils/            # Utility functions
│   │   └── backgroundRemoval.ts
│   ├── App.tsx           # Main app component
│   ├── main.tsx          # Entry point
│   └── index.css         # Global styles
├── index.html
├── package.json
├── package-lock.json
├── postcss.config.js
├── tailwind.config.ts
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts
```

---

## Getting Started

### Prerequisites
- **Node.js** 18+ and npm
- Code editor (VS Code recommended)
- Git

### Installation

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   Create a `.env` file in the `frontend` directory:
   ```env
   VITE_SUPABASE_URL=your_supabase_url
   VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```
   > **Note:** These are currently used for Supabase integration. When migrating to Python backend, these will be replaced with your backend API URL.

4. **Start the development server:**
   ```bash
   npm run dev
   ```

5. **Open your browser:**
   Navigate to `http://localhost:5173`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

---

## Development Workflow

### Code Style Guidelines

1. **TypeScript**: Always use TypeScript. Avoid `any` types when possible.
2. **Component Structure**: Use functional components with hooks.
3. **File Naming**: Use PascalCase for components, camelCase for utilities.
4. **Imports**: Group imports: external libraries → internal components → types → utilities.

### Example Component Structure

```typescript
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/context/AuthContext';

interface MyComponentProps {
  title: string;
  onAction?: () => void;
}

export const MyComponent = ({ title, onAction }: MyComponentProps) => {
  const { user } = useAuth();
  const [state, setState] = useState<string>('');

  useEffect(() => {
    // Side effects
  }, []);

  return (
    <div>
      <h1>{title}</h1>
      <Button onClick={onAction}>Action</Button>
    </div>
  );
};
```

---

## Architecture & Patterns

### Component Architecture
- **Pages**: Top-level route components in `src/pages/`
- **Components**: Reusable UI components in `src/components/`
- **UI Components**: shadcn/ui components in `src/components/ui/`

### State Management Pattern
- **Server State**: TanStack Query for API data
- **Client State**: React Context API for auth and global state
- **Local State**: React hooks (`useState`, `useReducer`) for component state

### Data Fetching Pattern
```typescript
import { useQuery } from '@tanstack/react-query';

const { data, isLoading, error } = useQuery({
  queryKey: ['resource', id],
  queryFn: () => fetchResource(id),
});
```

---

## Key Features

### 1. Authentication System
- Email/password authentication
- Google OAuth integration
- Role-based access control (root, developer, user)
- Protected routes

### 2. Quantum Computing Features
- Interactive quantum state visualizer
- Quantum gates simulator
- Educational content with MathJax support
- Real-time quantum state calculations

### 3. User Management
- User profiles and progress tracking
- Admin dashboard for user management
- Developer content creation tools
- Page visit tracking

### 4. UI/UX Features
- Responsive design (mobile-first)
- Dark theme by default
- Voice bot integration
- Newsletter subscription
- Logo processing with background removal

---

## Authentication & Authorization

### AuthContext
The `AuthContext` provides authentication state throughout the app:

```typescript
import { useAuth } from '@/context/AuthContext';

const { user, session, role, loading, signOut } = useAuth();
```

### Roles
- **root**: Full admin access
- **developer**: Content creation access
- **user**: Standard user access

### Protected Routes
Use the `ProtectedRoute` component to protect routes:

```typescript
<Route 
  path="/admin" 
  element={
    <ProtectedRoute roles={["root"]}>
      <Admin />
    </ProtectedRoute>
  } 
/>
```

---

## API Integration

### Current Implementation (Supabase)
The app currently uses Supabase for authentication and data. Key files:
- `src/lib/supabase.ts` - Supabase client configuration
- `src/context/AuthContext.tsx` - Auth state management

### Migration to Python Backend

When integrating with your Python backend, you'll need to:

1. **Replace Supabase Client** (`src/lib/supabase.ts`):
   ```typescript
   // Replace with your API client
   const API_BASE_URL = import.meta.env.VITE_API_URL;
   
   export const apiClient = {
     get: (endpoint: string) => fetch(`${API_BASE_URL}${endpoint}`),
     post: (endpoint: string, data: any) => 
       fetch(`${API_BASE_URL}${endpoint}`, {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(data),
       }),
   };
   ```

2. **Update AuthContext** to use your backend:
   ```typescript
   // Replace Supabase calls with your API endpoints
   const login = async (email: string, password: string) => {
     const response = await fetch(`${API_BASE_URL}/auth/login`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ email, password }),
     });
     return response.json();
   };
   ```

3. **Update Environment Variables**:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```

### API Endpoints Needed

Your Python backend should provide:

**Authentication:**
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/oauth/google` - Google OAuth

**User Management:**
- `GET /api/users` - List users (admin only)
- `PUT /api/users/{id}/role` - Update user role (admin only)
- `POST /api/users/{id}/block` - Block user (admin only)

**Content:**
- `GET /api/learn-blocks` - Get learning content
- `POST /api/learn-blocks` - Create content (developer/admin)
- `GET /api/page-progress` - Get user progress
- `POST /api/usage-events` - Track page visits

**Newsletter:**
- `POST /api/newsletter/subscribe` - Subscribe to newsletter

---

## Styling Guidelines

### Tailwind CSS
The project uses Tailwind CSS for styling. Key patterns:

```typescript
// Utility classes
<div className="bg-slate-800/50 border-slate-700/50 backdrop-blur-sm">

// Responsive design
<div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">

// Dark theme colors
className="text-white bg-slate-900"
```

### Color Scheme
- **Primary**: Blue (`blue-400`, `blue-500`, `blue-600`)
- **Secondary**: Purple (`purple-400`, `purple-500`, `purple-600`)
- **Background**: Dark slate (`slate-900`, `slate-800`)
- **Text**: White/gray (`white`, `gray-300`, `blue-100`)

### Component Styling
- Use `cn()` utility for conditional classes:
  ```typescript
  import { cn } from '@/lib/utils';
  className={cn("base-class", condition && "conditional-class")}
  ```

---

## Component Library

### shadcn/ui Components
The project uses shadcn/ui components located in `src/components/ui/`. These are customizable and accessible.

**Commonly Used Components:**
- `Button` - Various button styles
- `Card` - Container component
- `Input` - Form input
- `Dialog` - Modal dialogs
- `Toast` - Notifications
- `Select` - Dropdown select

### Custom Components

**Navbar** (`src/components/Navbar.tsx`)
- Responsive navigation bar
- User authentication state
- Mobile menu

**Footer** (`src/components/Footer.tsx`)
- Site footer with links
- Newsletter subscription
- Social media links

**ProtectedRoute** (`src/components/ProtectedRoute.tsx`)
- Route protection based on roles
- Redirects unauthenticated users

**QuantumVisualizer** (`src/components/QuantumVisualizer.tsx`)
- Interactive quantum state visualization

---

## State Management

### React Context
- **AuthContext**: Authentication state, user info, roles

### TanStack Query
Used for server state management:

```typescript
import { useQuery, useMutation } from '@tanstack/react-query';

// Query
const { data, isLoading } = useQuery({
  queryKey: ['users'],
  queryFn: fetchUsers,
});

// Mutation
const mutation = useMutation({
  mutationFn: createUser,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['users'] });
  },
});
```

---

## Routing

Routes are defined in `src/App.tsx`:

```typescript
<Routes>
  <Route path="/" element={<Index />} />
  <Route path="/learn" element={<Learn />} />
  <Route path="/quantum-computing" element={<QuantumComputing />} />
  <Route path="/login" element={<Login />} />
  <Route path="/admin" element={
    <ProtectedRoute roles={["root"]}>
      <Admin />
    </ProtectedRoute>
  } />
</Routes>
```

### Page Tracking
Pages use the `usePageTracking` hook to track visits:

```typescript
import { usePageTracking } from '@/hooks/usePageTracking';

const MyPage = () => {
  usePageTracking('page-key');
  // ...
};
```

---

## Environment Variables

Create a `.env` file in the `frontend` directory:

```env
# Current (Supabase - to be replaced)
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key

# Future (Python Backend)
VITE_API_URL=http://localhost:8000/api
```

> **Note:** Vite requires the `VITE_` prefix for environment variables to be exposed to the client.

---

## Building & Deployment

### Production Build
```bash
npm run build
```

This creates an optimized build in the `dist` directory (configured in `vite.config.ts`).

### Preview Production Build
```bash
npm run preview
```

### Deployment Considerations
1. Set environment variables in your hosting platform
2. Configure your backend CORS to allow your frontend domain
3. Update API URLs for production
4. Ensure static assets are served correctly

---

## Backend Integration Guide

### Step 1: Update API Client
Replace `src/lib/supabase.ts` with your API client:

```typescript
// src/lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const api = {
  async request(endpoint: string, options: RequestInit = {}) {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }
    
    return response.json();
  },
  
  get: (endpoint: string) => api.request(endpoint),
  post: (endpoint: string, data: any) => 
    api.request(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: (endpoint: string, data: any) => 
    api.request(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  delete: (endpoint: string) => 
    api.request(endpoint, { method: 'DELETE' }),
};
```

### Step 2: Update AuthContext
Modify `src/context/AuthContext.tsx` to use your backend:

```typescript
const login = async (email: string, password: string) => {
  const data = await api.post('/auth/login', { email, password });
  localStorage.setItem('auth_token', data.token);
  // Update state
};
```

### Step 3: Update All Supabase Calls
Search for `supabase.` in the codebase and replace with your API calls.

### Step 4: Update Environment Variables
```env
VITE_API_URL=http://localhost:8000/api
```

### Step 5: CORS Configuration
Ensure your Python backend allows CORS from your frontend domain:

```python
# Example with FastAPI
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Common Tasks

### Adding a New Page
1. Create component in `src/pages/NewPage.tsx`
2. Add route in `src/App.tsx`
3. Add navigation link in `src/components/Navbar.tsx`

### Adding a New Component
1. Create component in `src/components/NewComponent.tsx`
2. Export from component file
3. Import where needed

### Adding Authentication
1. Use `useAuth()` hook from `AuthContext`
2. Check `user` and `role` for authorization
3. Use `ProtectedRoute` for route protection

### Styling a Component
1. Use Tailwind utility classes
2. Use `cn()` for conditional classes
3. Follow existing color scheme

---

## Troubleshooting

### Common Issues

**1. Module not found errors**
- Check path aliases in `tsconfig.json`
- Ensure `@/` alias points to `src/`
- Restart TypeScript server in your IDE

**2. Environment variables not working**
- Ensure variables start with `VITE_`
- Restart dev server after adding variables
- Check `.env` file is in `frontend/` directory

**3. Build errors**
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check TypeScript errors: `npm run build`
- Ensure all imports are correct

**4. CORS errors**
- Configure backend CORS properly
- Check API URL in environment variables
- Verify backend is running

**5. Authentication not working**
- Check backend API endpoints
- Verify token storage/retrieval
- Check network tab for API errors

---

## Additional Resources

- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [React Router Documentation](https://reactrouter.com/)

---

## Support

For questions or issues:
- Check existing documentation
- Review code comments
- Contact the development team

---

**Last Updated:** 2024
**Version:** 0.1.0

