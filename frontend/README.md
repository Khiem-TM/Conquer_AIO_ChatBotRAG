# RAG Chatbot Frontend - React + Tailwind CSS

A modern, responsive React frontend for the RAG (Retrieval-Augmented Generation) chatbot system built with **React 18**, **TypeScript**, **Vite**, and **Tailwind CSS**.

## 🎨 Features

✨ **Modern UI**

- Dark theme optimized for reading
- Responsive design (mobile, tablet, desktop)
- Smooth animations and transitions
- Clean, intuitive layout

💬 **Chat Interface**

- Real-time message display
- Typing indicators
- Message timestamps
- Conversation history

📎 **Citation Management**

- Expandable source citations
- Citation snippets
- Relevance scores
- Source tracking

📁 **Document Management**

- Ingest status tracking
- Progress indicators
- Error handling
- Real-time feedback

⚙️ **Settings**

- Adjustable Top-K retrieval
- Citation toggle
- Theme preferences
- Auto-save settings

## 🏗️ Project Structure

```
frontend/
├── index.html                 # HTML entry point
├── package.json              # Project dependencies
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript configuration
├── tailwind.config.js        # Tailwind CSS configuration
├── postcss.config.js         # PostCSS configuration
└── src/
    ├── main.tsx              # React entry point
    ├── App.tsx               # Main app component
    ├── index.css             # Global styles
    ├── components/
    │   ├── ChatComponents.tsx # Chat UI components
    │   └── Sidebar.tsx        # Sidebar & settings
    ├── hooks/
    │   └── useApi.ts         # Custom hooks for API
    └── services/
        └── api.ts            # API client
```

## 🚀 Quick Start

### Prerequisites

- Node.js 16+ (for npm)
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env file (optional)
echo "REACT_APP_API_URL=http://localhost:8000" > .env.local
```

### Development

```bash
# Start development server
npm run dev

# Server runs on http://localhost:3000
# Open in browser: http://localhost:3000
```

### Build for Production

```bash
# Build optimized bundle
npm run build

# Preview production build locally
npm run preview
```

## 📦 Dependencies

### Production

- **react** (18.2.0) - UI framework
- **react-dom** (18.2.0) - React DOM rendering
- **axios** (1.6.0) - HTTP client for API calls

### Development

- **vite** (5.0.8) - Build tool and dev server
- **typescript** (5.2.2) - Type safety
- **tailwindcss** (3.4.1) - Utility CSS framework
- **postcss** (8.4.32) - CSS processing
- **autoprefixer** (10.4.16) - CSS vendor prefixes

## 🔌 API Integration

### Environment Variables

Create `.env.local` file:

```env
REACT_APP_API_URL=http://localhost:8000
```

**Default**: `http://localhost:8000`

### Supported Endpoints

The frontend integrates with these backend APIs:

| Method | Endpoint                     | Purpose             |
| ------ | ---------------------------- | ------------------- |
| GET    | `/health`                    | Health check        |
| POST   | `/api/v1/chat`               | Send chat question  |
| GET    | `/api/v1/history`            | Get chat history    |
| DELETE | `/api/v1/history`            | Clear history       |
| POST   | `/api/v1/ingest`             | Start ingestion     |
| GET    | `/api/v1/ingest/status/{id}` | Check ingest status |

## 🧩 Component Structure

### App.tsx

Main application component that orchestrates all features:

- Layout management
- State handling
- Message display
- Settings management

### ChatComponents.tsx

- `ChatMessage` - Individual chat message display
- `CitationCard` - Source citation display
- `ChatContainer` - Chat history container
- `InputArea` - Message input form

### Sidebar.tsx

- `Sidebar` - Navigation and settings
- `DocumentManager` - Document ingestion interface

### Hooks (useApi.ts)

- `useChat()` - Chat functionality hook

  - Load history
  - Send messages
  - Clear history
  - Error handling

- `useIngest()` - Document ingestion hook
  - Start ingest
  - Check status
  - Progress tracking

### Services (api.ts)

- `APIClient` - Centralized API communication
- Type definitions for API responses

## 🎯 Usage Examples

### Basic Chat

```tsx
import { useChat } from "./hooks/useApi";

function ChatApp() {
  const { messages, loading, sendMessage } = useChat();

  return (
    <>
      {messages.map((msg) => (
        <div key={msg.id}>
          <p>Q: {msg.question}</p>
          <p>A: {msg.answer}</p>
        </div>
      ))}
      <button onClick={() => sendMessage("What is AI?")}>Ask Question</button>
    </>
  );
}
```

### Document Ingestion

```tsx
import { useIngest } from "./hooks/useApi";

function IngestApp() {
  const { startIngest, checkStatus, loading } = useIngest();

  const handleIngest = async () => {
    await startIngest();
  };

  return (
    <button onClick={handleIngest} disabled={loading}>
      {loading ? "Ingesting..." : "Ingest Documents"}
    </button>
  );
}
```

## 🎨 Tailwind CSS Customization

### Theme Colors

Edit `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: "#7c3aed", // Purple
        secondary: "#1f2937", // Gray
        // Add more colors
      },
    },
  },
};
```

### Custom Styles

Global styles in `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom animations */
@keyframes slideUp {
  from {
    @apply opacity-0 translate-y-4;
  }
  to {
    @apply opacity-100 translate-y-0;
  }
}
```

## 🔧 Configuration

### Vite (vite.config.ts)

```typescript
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
  },
});
```

### TypeScript (tsconfig.json)

Strict mode enabled for type safety.

## 📱 Responsive Design

The frontend is fully responsive:

- **Mobile** (< 640px) - Single column, optimized touch
- **Tablet** (640px - 1024px) - Two-column layout
- **Desktop** (> 1024px) - Full layout with sidebar

## 🚨 Error Handling

### API Errors

All API errors are caught and displayed to the user:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

### Validation

Input validation happens at multiple levels:

1. Client-side (React state)
2. API request (Axios)
3. Server-side (FastAPI/Pydantic)

## 🔐 Security Considerations

✅ **Implemented**

- HTTPS-ready (configure via environment)
- CORS handled by backend
- Input sanitization
- Error messages don't expose sensitive info

⚠️ **TODO for Production**

- Add authentication token handling
- Implement rate limiting UI
- Add request signing
- Secure environment variables

## 🧪 Testing

Currently no tests included. To add:

```bash
# Install testing library
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest

# Run tests
npm run test
```

## 🐛 Troubleshooting

### Backend Connection Error

**Problem**: "Cannot connect to backend"

**Solution**:

```bash
# Ensure backend is running
cd ../Project
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000

# Verify .env.local has correct URL
cat .env.local
# Should show: REACT_APP_API_URL=http://localhost:8000
```

### CORS Error

**Problem**: "Access to XMLHttpRequest blocked by CORS policy"

**Solution**:

```bash
# Update backend .env to allow frontend origin
CORS_ORIGINS=["http://localhost:3000"]

# Restart backend
```

### Port Already in Use

**Problem**: "Port 3000 is already in use"

**Solution**:

```bash
# Change port in vite.config.ts
server: {
  port: 3001,  // Use different port
}

# Or kill existing process
lsof -ti:3000 | xargs kill -9
```

### TypeScript Errors

**Problem**: "Type 'x' is not assignable to type 'y'"

**Solution**:

```bash
# Check tsconfig.json is correct
# Run type check
npx tsc --noEmit

# Fix type issues or use @ts-ignore as last resort
```

## 📊 Performance

### Bundle Size

Target sizes:

- Main bundle: < 200KB
- CSS: < 50KB
- Total: < 300KB gzipped

### Optimization

- Code splitting for lazy loading
- Tree-shaking unused code
- Image optimization
- CSS purging with Tailwind

## 🚀 Deployment

### Vercel (Recommended)

```bash
# Deploy to Vercel
npm install -g vercel
vercel

# Configure environment variables in Vercel dashboard
# Set REACT_APP_API_URL to backend URL
```

### Docker

```bash
# Create Dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### Traditional Server

```bash
# Build static files
npm run build

# Upload dist/ folder to server
# Serve with nginx or similar

# nginx.conf example
server {
  listen 80;
  root /var/www/rag-chatbot/dist;
  try_files $uri /index.html;
}
```

## 📚 Additional Resources

- [React Documentation](https://react.dev)
- [Vite Documentation](https://vitejs.dev)
- [Tailwind CSS Documentation](https://tailwindcss.com)
- [TypeScript Documentation](https://www.typescriptlang.org)
- [Axios Documentation](https://axios-http.com)

## 🤝 Integration with Backend

Make sure backend is running:

```bash
# Terminal 1: Backend
cd Project
source venv/bin/activate
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Then open: `http://localhost:3000`

## 📝 Environment Setup

### Development

`.env.local`:

```env
REACT_APP_API_URL=http://localhost:8000
```

### Production

Set environment variable at deployment platform:

```env
REACT_APP_API_URL=https://api.yourdomain.com
```

## 🎓 Next Steps

1. ✅ Run frontend: `npm run dev`
2. ✅ Open browser: `http://localhost:3000`
3. ✅ Test chat functionality
4. ✅ Upload documents via Document Manager
5. ✅ Ask questions about documents
6. ✅ Build for production: `npm run build`

## 📞 Support

For issues:

1. Check logs in browser console (F12)
2. Verify backend is running
3. Check network tab for failed requests
4. Review `.env.local` configuration
5. Read error messages carefully

## 📄 License

Part of the Conquer RAG ChatBot initiative.

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2024-01-15  
**Node.js**: 16+ required
