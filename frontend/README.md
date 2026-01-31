---
title: AgentHub Frontend
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AgentHub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/timothy-odofin/agenthub-fe)
[![React](https://img.shields.io/badge/React-19.2.0-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9.3-blue.svg)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-7.2.4-646CFF.svg)](https://vitejs.dev/)

AgentHub is an AI-powered chat application that provides intelligent conversational experiences. Built with modern web technologies, it offers a clean and intuitive interface for interacting with AI assistants.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
  - [Building for Production](#building-for-production)
- [Project Architecture](#project-architecture)
- [Tech Stack](#tech-stack)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Overview

This application provides two main experiences: a conversational signup process and a full-featured chat interface. The signup guides users through account creation in a natural, conversation-style flow, while the main chat interface supports multiple sessions, real-time messaging, and session management.

## Features

- 🤖 **AI-Powered Chat**: Real-time conversations with intelligent AI assistants
- 🎨 **Dark Mode Support**: Seamless theme switching for comfortable viewing
- 💬 **Session Management**: Create, rename, share, and delete chat sessions
- 📝 **Rich Markdown**: Full support for formatted text, code blocks, tables, and more
- 🔐 **Secure Authentication**: JWT-based auth with automatic token refresh
- 📱 **Responsive Design**: Works beautifully on desktop, tablet, and mobile
- ⚡ **Fast Performance**: Built with Vite for lightning-fast development and production builds
- 🎯 **Conversational Signup**: Natural, guided account creation process

## Getting Started

### Prerequisites

- Node.js 20.19+ or 22.12+
- npm or yarn package manager

### Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/timothy-odofin/agenthub-fe.git
cd agenthub-fe
npm install
```

### Configuration

Create a `.env` file in the root directory (use `.env.example` as template):

```bash
# Development server port
PORT=3000

# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# For production:
# VITE_API_BASE_URL=https://api.yourdomain.com
```

### Running the Application

Start the development server:

```bash
npm run dev
```

The application will be available at http://localhost:3000

### Building for Production

Create a production build:

```bash
npm run build
```

The built files will be in the `dist` directory.

## Features

### Authentication

**Login Page**
The login page provides a modern, clean interface for user authentication. Users can sign in with their email or username and password. The page displays clear error messages from the backend when credentials are invalid.

**Conversational Signup**
New users experience a unique chat-based registration flow. Instead of filling out a traditional form, users interact with a bot that guides them through each step:

1. Email address
2. Username
3. Password
4. First name
5. Last name

The interface shows progress through visual indicators and displays validation errors in real-time. Once complete, users are automatically logged in and redirected to the main dashboard.

### Chat Interface

**Session Management**
Users can create and manage multiple chat sessions. Each session maintains its own conversation history. Sessions are listed in a sidebar with titles and timestamps. You can rename sessions by clicking the edit icon, and the title updates immediately.

**Real-time Messaging**
Messages appear in a clean, modern layout with distinct styling for user and assistant messages. The interface automatically scrolls to show the latest message. When the AI is processing a response, animated indicators show the current status.

**Session Actions**
Each session supports several actions accessible through a dropdown menu:
- Rename the session title
- Share the session with others
- Additional options through the more menu

**Logout**
A logout button is available at the bottom of the sidebar. Clicking it clears all authentication tokens and returns you to the login page.

## Technical Architecture

### Frontend Stack

- React 18 with TypeScript for type-safe component development
- React Router v6 for client-side routing
- Axios for HTTP requests with automatic token refresh
- Tailwind CSS for styling
- Lucide React for icons
- Vite as the build tool

### Project Structure

```
src/
├── api/              # API client configuration and endpoints
├── components/       # Reusable UI components
│   ├── chat/        # Chat-specific components
│   ├── common/      # Shared components
│   └── modals/      # Modal dialogs
├── hooks/           # Custom React hooks
├── middleware/      # Route protection and guards
├── pages/           # Top-level page components
├── routes/          # Application routing configuration
├── types/           # TypeScript type definitions
└── utils/           # Helper functions and utilities
```

### Authentication Flow

The application uses JWT tokens for authentication. When a user logs in, the backend returns an access token and refresh token. These tokens are stored in localStorage and automatically attached to API requests.

If an access token expires, the application automatically attempts to refresh it using the refresh token. If the refresh fails, the user is logged out and redirected to the login page.

### API Integration

All API calls go through an Axios instance configured with interceptors for:
- Automatic token attachment to requests
- Token refresh on 401 responses
- Automatic logout on authentication failures

## Development

### Code Style

The project uses ESLint and TypeScript for code quality. Run the linter:

```bash
npm run lint
```

### Type Safety

All components use TypeScript with strict type checking enabled. Interface definitions are located in `src/types/`.

### Component Development

Components follow React best practices:
- Functional components with hooks
- Props validation through TypeScript interfaces
- Proper cleanup in useEffect hooks
- Separation of concerns between UI and logic

## Tech Stack

### Frontend
- **React 19.2.0** - Modern UI library with hooks
- **TypeScript 5.9.3** - Type-safe JavaScript
- **Vite 7.2.4** - Lightning-fast build tool
- **React Router 7.12.0** - Client-side routing
- **Tailwind CSS 4.1.18** - Utility-first styling
- **Axios 1.13.2** - HTTP client with interceptors

### UI Components
- **Lucide React 0.562.0** - Beautiful icon set
- **react-markdown 10.1.0** - Markdown rendering
- **remark-gfm 4.0.1** - GitHub Flavored Markdown
- **rehype-highlight 7.0.2** - Syntax highlighting
- **highlight.js** - Code block styling

## Environment Variables

Configure the application using a `.env` file (see `.env.example`):

```
PORT=3000
VITE_API_BASE_URL=http://localhost:8000
```

Access them in code using `import.meta.env.VITE_API_BASE_URL`.

## Deployment

The application can be deployed to any static hosting service:

1. Build the production bundle: `npm run build`
2. Upload the `dist` directory to your hosting service
3. Configure your server to serve `index.html` for all routes

Popular hosting options include Vercel, Netlify, AWS S3, or any CDN service.

## Browser Support

The application supports modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- How to report bugs
- How to suggest features
- Development setup
- Code style guidelines
- Pull request process
- Code of Conduct

## Security

For security concerns or vulnerability reports, please see [SECURITY.md](SECURITY.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 Timothy Odofin

## Support

- **Issues**: [GitHub Issues](https://github.com/timothy-odofin/agenthub-fe/issues)
- **Documentation**: See the [docs](https://github.com/timothy-odofin/agenthub-fe#readme)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

Made with ❤️ by [Timothy Odofin](https://github.com/timothy-odofin)
