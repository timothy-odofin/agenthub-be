# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-13

### Added
- Initial release of AgentHub Frontend
- Modern authentication system with conversational signup
- Real-time chat interface with AI assistant
- Session management (create, rename, share, delete)
- Markdown rendering with syntax highlighting
- Dark mode support for markdown content
- Model capabilities display with category filtering
- Session loading states and animations
- Custom confirmation modal for destructive actions
- Responsive design for mobile and desktop
- JWT token authentication with automatic refresh
- Protected routes with authentication middleware

### Features
- **Authentication**
  - Login with email/username and password
  - Conversational signup flow with progress tracking
  - Automatic token refresh on expiration
  
- **Chat Interface**
  - Multiple chat sessions support
  - Real-time message streaming
  - Message history with timestamps
  - Session rename functionality
  - Session sharing capabilities
  - Session deletion with confirmation
  - Loading states for all async operations
  
- **UI/UX**
  - Clean, modern ChatGPT-inspired design
  - Smooth animations and transitions
  - Markdown rendering with code syntax highlighting
  - Copy-to-clipboard for code blocks
  - Responsive layout for all screen sizes
  - Dark mode text rendering
  - Empty state handling
  
- **Developer Experience**
  - TypeScript for type safety
  - ESLint for code quality
  - Vite for fast development
  - Modular component architecture
  - Centralized API configuration
  - Reusable custom hooks

### Technical Stack
- React 19.2.0
- TypeScript 5.9.3
- Vite 7.2.4
- React Router 7.12.0
- Tailwind CSS 4.1.18
- Axios for HTTP requests
- React Markdown for rich text
- Lucide React for icons

### Documentation
- Comprehensive README with setup instructions
- Contributing guidelines
- Security policy
- MIT License
- Code of conduct

## [Unreleased]

### Planned
- User profile management
- Theme customization
- Message search functionality
- Export chat history
- File upload support
- Voice input capability
- Multi-language support

---

## Version History

For older versions, see [releases](https://github.com/timothy-odofin/agenthub-fe/releases).
