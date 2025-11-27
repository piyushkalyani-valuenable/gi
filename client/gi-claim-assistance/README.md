# GI Claim Assistance - Client

React + TypeScript frontend for health insurance claim assessment.

## 🚀 Setup

### 1. Install Dependencies

```bash
cd client/gi-claim-assistance
npm install
```

### 2. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## 📦 Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## 🏗️ Project Structure

```
src/
├── components/          # React components
│   ├── ChatInput.tsx    # Message input component
│   ├── ChatMessage.tsx  # Message display component
│   └── *.css            # Component styles
├── services/            # API services
│   └── api.ts           # Backend API calls
├── types/               # TypeScript type definitions
│   └── index.ts         # Shared types
├── utils/               # Utility functions
│   └── sessionId.ts     # Session management
├── config/              # Configuration
│   └── api.ts           # API endpoints
├── App.tsx              # Main app component
├── App.css              # App styles
├── main.tsx             # Entry point
└── index.css            # Global styles
```

## 🎨 Features

- ✅ **Session-based** - Each user gets a unique session
- ✅ **File upload** - Support for PDF and images
- ✅ **Real-time updates** - Loading indicators and auto-scroll
- ✅ **Type-safe** - Full TypeScript support
- ✅ **Responsive** - Works on desktop and mobile
- ✅ **Clean UI** - Modern, intuitive interface

## 🔧 Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## 🌐 API Integration

The frontend communicates with the FastAPI backend through:

- **POST /api/chat** - Send messages and upload files
- **GET /api/health** - Check backend health

Session management is handled automatically using `sessionStorage`.

## 📝 Usage

1. Open the app in your browser
2. Upload documents in sequence:
   - **Turn 1**: Prescription (price check)
   - **Turn 2**: Discharge Summary (hospital bill)
   - **Turn 3**: Policy Bond (insurance policy)
3. View the calculated claim assessment

## 🔐 Security Notes

- Session IDs are stored in `sessionStorage` (cleared on tab close)
- No sensitive data is stored in localStorage
- All API calls go through the configured backend URL
