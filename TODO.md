# 📋 TODO List - Voice News Agent

**Last Updated:** 2025-10-09  
**Current Phase:** Backend MVP Testing & Deployment

---

## 🎯 Current Sprint: Backend MVP Deployment

### ⏳ In Progress
- [ ] **Fix Supabase version conflict** - Server won't start due to httpx/supabase version mismatch
  - Try: `uv pip install 'supabase==2.8.1' 'httpx==0.24.1'`
  - Or make DB initialization optional for local testing

- [ ] **Manual streaming test** - Verify WebSocket streaming works
  - Open `test_websocket.html`
  - Test voice commands → TTS streaming
  - Verify `tts_chunk` events arrive
  - Test partial transcriptions
  - Test audio buffering

### ✅ Completed
- [x] **WebSocket streaming implementation** - Real-time voice communication
- [x] **Streaming handler** - Chunked TTS with edge-tts
- [x] **Partial transcription support** - Real-time ASR feedback
- [x] **Audio buffering** - Smart buffering for incoming voice data
- [x] **Test client** - Updated `test_websocket.html` with streaming events
- [x] **Supabase schema** - Tables created on production database
- [x] **Upstash Redis** - Cache connection tested successfully
- [x] **Environment configuration** - Multi-file env setup (env_files/)
- [x] **Documentation** - Testing guides and implementation status
- [x] **README update** - Added v3.0 cloud MVP section

---

## 📦 Next: Render Deployment

### Pending Tasks
- [ ] **Local streaming test** - Verify all events work correctly
- [ ] **Fix server startup issue** - Resolve Supabase dependency conflict
- [ ] **Commit to git** - Push all changes to main branch
- [ ] **Deploy to Render** - Use blueprint (render.yaml)
- [ ] **Set environment variables** - Configure Supabase + Upstash in Render
- [ ] **Production test** - Test WebSocket on deployed URL
- [ ] **iOS integration guide** - Document Swift integration steps

---

## 🚀 Phase 2: iOS App Development

### iOS Client Features
- [ ] **SwiftUI interface** - Voice news app UI
- [ ] **Speech Framework integration** - Client-side ASR
- [ ] **WebSocket client** - Connect to backend API
- [ ] **Audio playback** - Stream and play TTS chunks
- [ ] **Conversation history** - Display chat messages
- [ ] **Settings** - Configure preferences, topics, watchlist

### Backend Enhancements for iOS
- [ ] **Push notifications** - Breaking news alerts
- [ ] **User authentication** - JWT tokens
- [ ] **Preference sync** - Real-time preference updates
- [ ] **Offline mode** - Cache recent news for offline access

---

## 🔧 Technical Debt & Improvements

### High Priority
- [ ] **Error handling** - Better error messages for WebSocket failures
- [ ] **Rate limiting** - Implement per-user rate limits
- [ ] **Logging improvements** - Structured logging with correlation IDs
- [ ] **Metrics & monitoring** - Add performance tracking
- [ ] **Security audit** - Review auth, input validation, SQL injection risks

### Medium Priority
- [ ] **Caching optimization** - Fine-tune TTLs and invalidation strategy
- [ ] **Database indexes** - Optimize query performance
- [ ] **WebSocket connection management** - Heartbeat, reconnection logic
- [ ] **Audio codec optimization** - Test MP3 vs Opus for streaming
- [ ] **Memory optimization** - Profile and reduce backend memory usage

### Low Priority
- [ ] **API versioning** - Prepare for v2 API
- [ ] **GraphQL API** - Consider GraphQL for flexible queries
- [ ] **Admin dashboard** - Monitor users, usage, errors
- [ ] **Analytics integration** - User behavior tracking
- [ ] **A/B testing framework** - Test different news presentation styles

---

## 🧪 Testing & Quality

### Backend Tests
- [ ] **Fix failing tests** - Many tests need mocking for Supabase/Upstash
- [ ] **Integration tests** - End-to-end API testing
- [ ] **WebSocket tests** - Automated streaming tests
- [ ] **Load testing** - Test concurrent WebSocket connections
- [ ] **Security testing** - Penetration testing, vulnerability scan

### Frontend Tests (Future)
- [ ] **Unit tests** - iOS app component testing
- [ ] **UI tests** - XCUITest for iOS app
- [ ] **End-to-end tests** - Full user flow testing

---

## 📱 Platform Expansion

### Mobile
- [x] **iOS preparation** - API ready for iOS integration
- [ ] **iOS MVP** - Build and test iOS app
- [ ] **iOS App Store** - Submit to Apple for review
- [ ] **Android MVP** - Port to Android/Kotlin
- [ ] **Cross-platform** - Consider React Native/Flutter

### Web
- [ ] **Next.js frontend** - Web interface (frontend/ folder exists)
- [ ] **Progressive Web App** - Offline-capable web app
- [ ] **Desktop PWA** - Installable desktop app

### Voice Assistants
- [ ] **Siri Shortcuts** - iOS integration
- [ ] **Google Assistant** - Android integration
- [ ] **Alexa Skill** - Amazon Echo integration
- [ ] **HomePod** - Apple HomePod support

---

## 🎨 Features & Enhancements

### Voice & Audio
- [ ] **Voice profiles** - Multiple voices (male/female, accents)
- [ ] **Speed control** - User-adjustable playback speed
- [ ] **Background playback** - Continue playing while app backgrounded
- [ ] **Offline TTS** - Local TTS for offline mode
- [ ] **Multi-language support** - Spanish, French, Chinese, etc.

### News & Content
- [ ] **More news sources** - BBC, Reuters, NYT, WSJ
- [ ] **Podcast integration** - Stream news podcasts
- [ ] **Video summaries** - YouTube news summaries
- [ ] **Local news** - Location-based local news
- [ ] **Custom RSS feeds** - User-added sources

### Intelligence & Personalization
- [ ] **AI summaries** - Better news summarization
- [ ] **Sentiment analysis** - Detect news tone
- [ ] **Topic clustering** - Group related stories
- [ ] **Recommendation engine** - ML-based news recommendations
- [ ] **Reading level adjustment** - Simplify/complexify explanations

### Social & Sharing
- [ ] **Share news** - Share articles via SMS/email/social
- [ ] **Collaborative watchlists** - Share stock watchlists with friends
- [ ] **Comments & discussions** - User comments on news items
- [ ] **Social login** - Google/Apple/Facebook sign-in

---

## 💰 Monetization (Future)

### Revenue Streams
- [ ] **Freemium model** - Free tier + premium features
- [ ] **Premium subscription** - Ad-free, unlimited news, custom sources
- [ ] **API licensing** - B2B API access
- [ ] **White-label solution** - Branded versions for enterprises
- [ ] **Affiliate marketing** - Broker affiliate links

### Premium Features
- [ ] **Unlimited news sources** - Free tier limited to 3-5 sources
- [ ] **Custom voice** - Premium voice options
- [ ] **Advanced analytics** - Reading patterns, trends
- [ ] **Priority support** - Faster response times
- [ ] **Team accounts** - Multiple users, shared preferences

---

## 📊 Metrics & KPIs

### Track These Metrics
- [ ] **Daily Active Users (DAU)**
- [ ] **Monthly Active Users (MAU)**
- [ ] **Session duration**
- [ ] **News articles consumed per session**
- [ ] **WebSocket connection uptime**
- [ ] **API response times (p50, p95, p99)**
- [ ] **Error rates**
- [ ] **Conversion rate (free → premium)**

---

## 🐛 Known Issues

### Critical
- **Supabase version conflict** - Server won't start, needs version fix

### High
- **Tests failing** - Many tests need proper mocking for DB/cache
- **SenseVoice import** - Local agent can't import SenseVoice in some environments

### Medium
- **Memory usage** - Backend uses more RAM than expected
- **Cold start** - Render free tier has 30-60s cold start

### Low
- **Audio quality** - TTS streaming could use better codec
- **Logs verbose** - Too many debug logs in production

---

## 📝 Documentation Tasks

- [x] **README.md** - Updated with v3.0 cloud MVP
- [x] **MVP.md** - Create comprehensive MVP guide
- [x] **TODO.md** - This file
- [x] **VOICE_INPUT_TESTING.md** - WebSocket testing guide
- [x] **STREAMING_AND_DEPLOYMENT.md** - Streaming implementation
- [x] **STREAMING_IMPLEMENTATION_STATUS.md** - Implementation checklist
- [ ] **DEPLOYMENT_GUIDE.md** - Step-by-step Render deployment
- [ ] **IOS_INTEGRATION.md** - Swift integration guide with examples
- [ ] **API_REFERENCE.md** - Complete API documentation
- [ ] **CONTRIBUTING.md** - Contribution guidelines
- [ ] **CHANGELOG.md** - Version history

---

## 🎓 Learning & Research

### Investigate
- [ ] **Whisper API** - Better ASR for non-iOS clients
- [ ] **ElevenLabs** - Higher quality TTS
- [ ] **WebRTC** - Better than WebSocket for voice?
- [ ] **gRPC** - Faster than REST for real-time?
- [ ] **Redis Streams** - Better event streaming?
- [ ] **Kafka** - For high-volume event processing?

---

**Priority Legend:**
- ⏳ In Progress - Currently being worked on
- ✅ Completed - Done and tested
- 🔥 Critical - Blocking deployment
- 🎯 High Priority - Next sprint
- 📌 Medium Priority - Backlog
- 💡 Nice to Have - Future consideration

