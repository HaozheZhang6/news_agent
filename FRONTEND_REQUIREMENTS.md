# Frontend Website Requirements for Voice News Agent

## Overview
A modern, responsive web application built with Next.js 14+ that provides a comprehensive interface for users to interact with the Voice News Agent. The application includes authentication, profile management, voice interaction, and conversation history.

## Technology Stack
- **Framework**: Next.js 14+ with App Router
- **Styling**: Tailwind CSS with shadcn/ui components
- **Authentication**: NextAuth.js or Supabase Auth
- **State Management**: React Context + Zustand
- **Real-time Communication**: WebSocket for voice streaming
- **Icons**: Lucide React
- **Notifications**: React Hot Toast
- **Forms**: React Hook Form + Zod validation

## Core Features

### 1. Authentication System

#### Login Page (`/login`)
- **Layout**: Centered card design with gradient background
- **Fields**:
  - Email input with validation
  - Password input with show/hide toggle
  - "Remember me" checkbox
  - "Forgot password?" link
- **Actions**:
  - Login button (primary)
  - "Sign up" link
  - Social login options (Google, GitHub)
- **States**: Loading, error, success
- **Validation**: Real-time email format validation

#### Registration Page (`/register`)
- **Layout**: Similar to login with additional fields
- **Fields**:
  - Full name
  - Email with confirmation
  - Password with strength indicator
  - Confirm password
  - Terms & conditions checkbox
- **Actions**:
  - Register button
  - "Already have account?" link
- **Validation**: Password strength, email confirmation match

#### Password Reset (`/forgot-password`)
- **Layout**: Simple form with email input
- **Fields**: Email address
- **Actions**: Send reset email button
- **Feedback**: Success message with instructions

### 2. Profile Management (`/profile`)

#### Profile Overview Section
- **User Avatar**: Upload/change profile picture
- **Basic Info**: Name, email, subscription tier
- **Quick Stats**: Total conversations, favorite topics, watchlist count
- **Last Active**: Timestamp of last interaction

#### Interests Management
- **Layout**: Grid of topic cards with toggle functionality
- **Available Topics**:
  - Technology
  - Finance
  - Politics
  - Crypto
  - Energy
  - Healthcare
  - Automotive
  - Real Estate
  - Retail
  - General
- **Features**:
  - Visual toggle switches
  - Search/filter topics
  - "Select All" / "Clear All" buttons
  - Save changes button

#### Stock Watchlist
- **Layout**: List view with add/remove functionality
- **Features**:
  - Add stock symbol input with autocomplete
  - Remove stocks with confirmation
  - Stock price display (if available)
  - Sort by symbol or date added
- **Validation**: Valid stock symbol format

#### Voice Settings
- **Speech Rate**: Slider (0.5x - 2.0x)
- **Voice Type**: Dropdown (Default, Male, Female, Custom)
- **Interruption Sensitivity**: Slider (Low, Medium, High)
- **Auto Play**: Toggle switch
- **Test Voice**: Button to preview settings

#### Notification Preferences
- **Breaking News**: Toggle switch
- **Stock Alerts**: Toggle switch
- **Daily Briefing**: Toggle switch
- **Email Notifications**: Toggle switch
- **Push Notifications**: Toggle switch (if supported)

### 3. Voice Agent Interface (`/`)

#### Main Dashboard Layout
- **Header**: Logo, user avatar, connection status, logout
- **Grid Layout**: 3-column responsive design
  - Left: Voice controls
  - Center: News display
  - Right: Quick actions

#### Voice Control Panel
- **Main Voice Button**: 
  - Large circular button (80px)
  - Start: Blue with microphone icon
  - Listening: Red with pulsing animation
  - Speaking: Green with speaker icon
  - Disabled: Gray when disconnected
- **Status Indicators**:
  - Connection status (green/red dot)
  - Listening status
  - Speaking status
- **Quick Commands**: Grid of preset buttons
  - "Tell me the news"
  - "Stock prices"
  - "Tell me more"
  - "Stop"
  - "Skip"
  - "Help"
- **Interrupt Button**: Appears only when agent is speaking

#### News Display Area
- **Current News**: Card-based layout
- **Loading States**: Skeleton loaders
- **Error States**: User-friendly error messages
- **Empty States**: Encouraging messages to start conversation

#### Connection Status
- **Visual Indicator**: Colored dot with status text
- **Auto-reconnect**: Automatic reconnection attempts
- **Error Messages**: Clear error descriptions

### 4. Conversation History (`/history`)

#### History List View
- **Layout**: Timeline-style vertical list
- **Each Entry Contains**:
  - Timestamp (date and time)
  - User input (speech-to-text result)
  - Agent response
  - Associated news items (if any)
  - Duration of conversation
- **Visual Design**:
  - User messages: Blue bubble on right
  - Agent messages: Green bubble on left
  - News items: Gray cards with title and summary

#### Filtering and Search
- **Date Range**: Calendar picker for date range
- **Topic Filter**: Dropdown with user's topics
- **Search**: Text search across conversations
- **Sort Options**: Date, duration, topic

#### Conversation Details
- **Expandable Cards**: Click to see full conversation
- **News Items**: Expandable news cards with full content
- **Export Options**: Download conversation as PDF/text
- **Share**: Share specific conversations (if enabled)

#### Statistics Dashboard
- **Summary Cards**:
  - Total conversations
  - Total news items discussed
  - Most active day/time
  - Average conversation duration
- **Charts**: 
  - Conversation frequency over time
  - Topic distribution pie chart
  - Response time trends

### 5. Responsive Design

#### Mobile-First Approach
- **Breakpoints**:
  - Mobile: 320px - 768px
  - Tablet: 768px - 1024px
  - Desktop: 1024px+
- **Mobile Optimizations**:
  - Touch-friendly buttons (44px minimum)
  - Swipe gestures for navigation
  - Optimized voice button size
  - Collapsible sidebar navigation

#### Desktop Enhancements
- **Keyboard Shortcuts**: Space bar for voice toggle
- **Hover States**: Enhanced interactions
- **Multi-column Layouts**: Better space utilization
- **Drag & Drop**: For profile picture upload

### 6. User Experience Features

#### Loading States
- **Skeleton Loaders**: For content areas
- **Progress Indicators**: For long operations
- **Optimistic Updates**: Immediate UI feedback

#### Error Handling
- **User-Friendly Messages**: Clear, actionable error text
- **Retry Mechanisms**: Automatic retry for network errors
- **Fallback Content**: Graceful degradation

#### Accessibility
- **ARIA Labels**: Screen reader support
- **Keyboard Navigation**: Full keyboard accessibility
- **Color Contrast**: WCAG AA compliance
- **Focus Management**: Clear focus indicators

#### Performance
- **Code Splitting**: Route-based splitting
- **Image Optimization**: Next.js Image component
- **Caching**: Aggressive caching for static content
- **Bundle Optimization**: Tree shaking and minification

## Page Structure

```
/ (Home/Dashboard)
├── /login
├── /register
├── /forgot-password
├── /profile
│   ├── /profile/interests
│   ├── /profile/watchlist
│   └── /profile/settings
├── /history
└── /settings
```

## Component Architecture

### Core Components
- `AuthProvider`: Authentication context
- `VoiceProvider`: Voice interaction context
- `NewsProvider`: News data context
- `Layout`: Main app layout with navigation
- `Header`: Top navigation bar
- `Sidebar`: Collapsible navigation (mobile)
- `VoiceButton`: Main voice interaction button
- `NewsCard`: News item display component
- `ConversationCard`: History item component
- `ProfileForm`: User profile editing form
- `TopicSelector`: Interest management component
- `WatchlistManager`: Stock watchlist component

### UI Components (shadcn/ui)
- Button, Input, Card, Dialog
- Select, Checkbox, Switch, Slider
- Toast, Alert, Badge, Avatar
- Table, Pagination, Tabs
- Form, Label, Textarea

## State Management

### Global State (Zustand)
- User authentication state
- Voice connection status
- Current conversation state
- User preferences cache

### Local State (React)
- Form inputs and validation
- UI component states
- Loading and error states
- Modal and dialog states

## API Integration

### Authentication Endpoints
- `POST /api/auth/login`
- `POST /api/auth/register`
- `POST /api/auth/logout`
- `POST /api/auth/forgot-password`

### User Management
- `GET /api/user/preferences`
- `PUT /api/user/preferences`
- `GET /api/user/topics`
- `POST /api/user/topics/add`
- `DELETE /api/user/topics/{topic}`
- `GET /api/user/watchlist`
- `POST /api/user/watchlist/add`
- `DELETE /api/user/watchlist/{symbol}`

### Voice & News
- WebSocket connection for real-time voice
- `GET /api/news/latest`
- `GET /api/conversation/history`

## Security Considerations

- **Authentication**: Secure JWT tokens
- **Input Validation**: Client and server-side validation
- **XSS Protection**: Sanitized content rendering
- **CSRF Protection**: Token-based protection
- **Rate Limiting**: API request limits
- **Secure Headers**: Security headers configuration

## Deployment Considerations

- **Environment Variables**: Secure configuration
- **Build Optimization**: Production-ready builds
- **CDN Integration**: Static asset delivery
- **Monitoring**: Error tracking and analytics
- **SEO**: Meta tags and structured data

## Design System

### Color Palette
- **Primary**: Blue (#3B82F6)
- **Secondary**: Green (#10B981)
- **Accent**: Purple (#8B5CF6)
- **Neutral**: Gray scale
- **Success**: Green (#059669)
- **Warning**: Yellow (#F59E0B)
- **Error**: Red (#DC2626)

### Typography
- **Font Family**: Inter (Google Fonts)
- **Headings**: Font weights 600-700
- **Body**: Font weight 400
- **Captions**: Font weight 300

### Spacing
- **Base Unit**: 4px
- **Common Spacing**: 4, 8, 12, 16, 24, 32, 48, 64px

### Border Radius
- **Small**: 4px
- **Medium**: 8px
- **Large**: 12px
- **Full**: 9999px (for buttons)

This comprehensive requirements document provides a complete blueprint for building a modern, user-friendly frontend for the Voice News Agent application.
