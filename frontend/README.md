# Voice News Agent Frontend

A Next.js frontend for the Voice News Agent with real-time voice interaction capabilities.

## Features

- 🎙️ **Real-time Voice Interaction** - WebSocket-based voice communication
- 📱 **Responsive Design** - Works on desktop and mobile
- 🎨 **Modern UI** - Built with Tailwind CSS and Framer Motion
- 🔊 **Voice Commands** - Quick command buttons and voice recognition
- 📰 **News Display** - Real-time news updates with topic categorization
- 💬 **Conversation History** - Track all interactions with the agent
- 🌙 **Dark Mode** - Automatic dark/light theme switching

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Socket.io** - Real-time WebSocket communication
- **React Speech Recognition** - Browser-based voice input
- **Framer Motion** - Smooth animations
- **Lucide React** - Beautiful icons

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running (see main project)

### Installation

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Set environment variables:**
   Create `.env.local` file:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── globals.css         # Global styles
│   ├── layout.tsx          # Root layout
│   └── page.tsx           # Home page
├── components/            # React components
│   ├── VoiceInterface.tsx # Main voice control
│   ├── NewsDisplay.tsx    # News presentation
│   └── ConversationHistory.tsx # Chat history
├── contexts/              # React contexts
│   ├── VoiceContext.tsx   # Voice state management
│   └── NewsContext.tsx    # News state management
├── package.json           # Dependencies
├── tailwind.config.js     # Tailwind configuration
└── next.config.js         # Next.js configuration
```

## Voice Commands

### Basic Commands
- **"Tell me the news"** - Get latest headlines
- **"Stock prices"** - Get market data
- **"Tell me more"** - Deep dive into current news
- **"Skip"** - Move to next news item
- **"Stop"** - Interrupt current speech
- **"Help"** - Show available commands

### Advanced Commands
- **"Add [topic] to my preferred topics"** - Manage preferences
- **"Add [ticker] to my watchlist"** - Track stocks
- **"What are my preferred topics?"** - List preferences
- **"Volume up/down"** - Control audio level
- **"Speak faster/slower"** - Adjust speech speed

## Deployment

### Vercel (Recommended)
1. Connect GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push

### Netlify
1. Connect repository to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `.next`

### Manual Deployment
```bash
npm run build
npm start
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |

## Browser Compatibility

- **Chrome/Edge** - Full support
- **Firefox** - Full support
- **Safari** - Full support (iOS 14.5+)
- **Mobile** - Responsive design

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Adding New Features

1. **Voice Commands**: Add to `VoiceInterface.tsx`
2. **News Types**: Extend `NewsContext.tsx`
3. **UI Components**: Create in `components/`
4. **Styling**: Use Tailwind classes

## Troubleshooting

### Common Issues

1. **Microphone Access Denied**
   - Ensure HTTPS in production
   - Check browser permissions
   - Use Chrome/Edge for best compatibility

2. **WebSocket Connection Failed**
   - Verify backend is running
   - Check CORS settings
   - Ensure correct WS URL

3. **Voice Recognition Not Working**
   - Check microphone permissions
   - Use supported browser
   - Ensure stable internet connection

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

MIT License - see main project for details.
