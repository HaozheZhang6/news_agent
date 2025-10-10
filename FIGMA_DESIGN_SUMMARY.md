# Figma Design Summary for Voice News Agent Frontend

## Project Overview
Design a modern, responsive web application for an AI-powered voice news assistant using Next.js. The app should have a clean, professional interface with excellent UX for voice interactions.

## Key Pages to Design

### 1. Login/Registration Pages
- **Login Page**: Centered card with email/password fields, social login options
- **Registration Page**: Similar layout with additional name field and password confirmation
- **Password Reset**: Simple email input form

### 2. Main Dashboard (`/`)
- **Layout**: 3-column grid (voice controls | news display | quick actions)
- **Header**: Logo, user avatar, connection status indicator
- **Voice Button**: Large circular button (80px) with microphone icon
- **News Cards**: Clean card layout for news items
- **Status Indicators**: Small colored dots for connection/listening/speaking states

### 3. Profile Management (`/profile`)
- **Profile Overview**: Avatar, name, email, subscription tier
- **Interests Section**: Grid of topic cards with toggle switches
- **Stock Watchlist**: List with add/remove functionality
- **Voice Settings**: Sliders and dropdowns for voice preferences
- **Notification Settings**: Toggle switches for different notification types

### 4. Conversation History (`/history`)
- **Timeline View**: Vertical list of conversation entries
- **Message Bubbles**: User (blue, right) and Agent (green, left)
- **News Cards**: Gray cards showing associated news items
- **Filter Bar**: Date range, topic filter, search input
- **Statistics Cards**: Summary metrics at the top

## Design System

### Colors
- **Primary Blue**: #3B82F6
- **Success Green**: #10B981
- **Error Red**: #DC2626
- **Warning Yellow**: #F59E0B
- **Neutral Grays**: #F9FAFB to #111827

### Typography
- **Font**: Inter (Google Fonts)
- **Headings**: 600-700 weight
- **Body**: 400 weight
- **Captions**: 300 weight

### Components to Include
- **Buttons**: Primary (blue), Secondary (gray), Danger (red)
- **Input Fields**: Text, email, password with validation states
- **Cards**: News cards, conversation cards, profile cards
- **Status Indicators**: Connection dots, loading states
- **Voice Button**: Large circular button with icon states
- **Toggle Switches**: For settings and preferences
- **Sliders**: For voice settings (speech rate, sensitivity)

### Layout Principles
- **Mobile-First**: Design for 320px width first
- **Responsive**: Breakpoints at 768px, 1024px
- **Grid System**: 12-column grid with proper gutters
- **Spacing**: 4px base unit (4, 8, 12, 16, 24, 32, 48, 64px)

### Interactive States
- **Hover**: Subtle color changes and shadows
- **Active**: Pressed state for buttons
- **Focus**: Clear outline for accessibility
- **Loading**: Skeleton loaders and spinners
- **Error**: Red borders and error messages
- **Success**: Green confirmation states

### Voice-Specific Design Elements
- **Voice Button States**:
  - Idle: Blue with microphone icon
  - Listening: Red with pulsing animation
  - Speaking: Green with speaker icon
  - Disabled: Gray with no interaction
- **Connection Status**: Small colored dots (green=connected, red=disconnected)
- **Audio Visualizations**: Optional waveform or sound bars during voice interaction

### Accessibility Requirements
- **Color Contrast**: WCAG AA compliance (4.5:1 ratio)
- **Touch Targets**: Minimum 44px for mobile
- **Focus Indicators**: Clear visual focus states
- **Screen Reader**: Proper ARIA labels and semantic HTML

### Key User Flows to Design
1. **Onboarding**: Login → Dashboard → First voice interaction
2. **Profile Setup**: Profile → Interests → Watchlist → Voice Settings
3. **Daily Usage**: Dashboard → Voice interaction → View news → Check history
4. **Settings Management**: Profile → Edit preferences → Save changes

### Mobile Considerations
- **Touch-Friendly**: Large buttons and touch targets
- **Thumb Navigation**: Important actions within thumb reach
- **Swipe Gestures**: Optional swipe for navigation
- **Voice Button**: Prominent placement for easy access
- **Collapsible Sections**: Space-efficient information display

### Desktop Enhancements
- **Keyboard Shortcuts**: Visual indicators for shortcuts
- **Hover States**: Rich hover interactions
- **Multi-Column Layouts**: Better space utilization
- **Drag & Drop**: For file uploads and reordering

## Design Deliverables Needed
1. **Wireframes**: Low-fidelity layouts for all pages
2. **High-Fidelity Mockups**: Detailed designs with colors, typography, spacing
3. **Component Library**: Reusable UI components
4. **Responsive Designs**: Mobile, tablet, desktop versions
5. **Interactive Prototypes**: Clickable prototypes for key user flows
6. **Design Specifications**: Detailed specs for developers

## Success Metrics
- **Usability**: Easy voice interaction initiation
- **Accessibility**: WCAG AA compliance
- **Performance**: Fast loading and smooth interactions
- **Mobile Experience**: Excellent touch interface
- **Visual Hierarchy**: Clear information architecture

This design should prioritize the voice interaction experience while maintaining a clean, professional appearance that builds trust with users.
