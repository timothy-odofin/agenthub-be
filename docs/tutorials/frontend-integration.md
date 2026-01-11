# Frontend Integration Guide - AgentHub Conversational Signup

This guide provides comprehensive information for building the landing page and integrating the conversational signup API.

---

## 📋 Table of Contents
1. [Landing Page Content](#landing-page-content)
2. [Demo Flow & User Experience](#demo-flow--user-experience)
3. [API Integration](#api-integration)
4. [React Component Examples](#react-component-examples)
5. [Error Handling](#error-handling)
6. [Testing the Demo](#testing-the-demo)

---

## 🎨 Landing Page Content

### Hero Section

**Headline:**
```
Build Intelligent AI Agents in Minutes, Not Months
```

**Subheadline:**
```
Open-source platform for creating production-ready AI agents with built-in LLM integration, 
conversation management, and enterprise features. No complex setup required.
```

**CTA Buttons:**
- Primary: **"Try Live Demo"** (Triggers conversational signup)
- Secondary: **"View on GitHub"** (Links to repo)

---

### Key Features Section

**Section Title:** "Everything You Need for AI Agent Development"

**Feature 1: Conversational Interfaces**
- **Icon:** 💬
- **Title:** "Natural Language Signup"
- **Description:** "Experience our intelligent conversational signup. No forms - just chat naturally. Our AI understands your intent and guides you through account creation."

**Feature 2: LLM Integration**
- **Icon:** 🤖
- **Title:** "Multi-Provider LLM Support"
- **Description:** "Built-in support for OpenAI, Anthropic, and more. Switch providers seamlessly with factory pattern design. Context-aware conversation management included."

**Feature 3: Enterprise Ready**
- **Icon:** 🔒
- **Title:** "Production-Grade Security"
- **Description:** "Redis session management, password hashing, JWT authentication, and MongoDB integration. Built for scale from day one."

**Feature 4: Vector Search**
- **Icon:** 🔍
- **Title:** "RAG & Knowledge Bases"
- **Description:** "Integrated vector databases (Qdrant, ChromaDB, PgVector) for retrieval-augmented generation. Build agents with long-term memory."

**Feature 5: Workflow Orchestration**
- **Icon:** ⚙️
- **Title:** "YAML-Based Workflows"
- **Description:** "Define complex workflows in simple YAML files. Built-in approval flows, signup workflows, and custom workflow support."

**Feature 6: External Integrations**
- **Icon:** 🔌
- **Title:** "Connect Everything"
- **Description:** "Pre-built integrations with GitHub, Jira, Datadog, and more. RESTful API design makes adding new integrations simple."

---

### Tech Stack Section

**Section Title:** "Built with Modern Technologies"

**Backend:**
- Python 3.12+ with FastAPI
- MongoDB for data persistence
- Redis for session management
- PostgreSQL for structured data
- OpenAI/Anthropic for LLM

**Frontend (Your Implementation):**
- React 18+ with TypeScript
- TailwindCSS for styling
- Axios for API calls
- React Query for state management

---

### Demo Section (Interactive)

**Section Title:** "Try the Live Demo"

**Intro Text:**
```
Experience our intelligent conversational signup - no traditional forms, 
just natural conversation. Click "Get Started" below to see how AI can 
make user onboarding effortless.
```

**Demo Box:**
```
┌─────────────────────────────────────────────────┐
│  💬 Conversational Signup Demo                  │
│                                                  │
│  [Chat Interface Placeholder]                   │
│                                                  │
│  Bot: 👋 Ready to create your account?          │
│       I just need a few quick details.          │
│                                                  │
│  [Get Started Button]                           │
└─────────────────────────────────────────────────┘
```

**Initial Prompt for User:**
When user clicks "Get Started", the chat interface opens with:

```
Bot: 👋 Welcome! Let's create your account. 

To get started, you can:
• Type "yes" or "let's go" to begin
• Ask me "What do I need?" to learn about requirements
• Ask me any questions about the signup process

What would you like to do?
```

**Alternative Opening (More Direct):**
```
Bot: 👋 Hi there! Ready to create your account?

I'll need 5 quick pieces of information:
📧 Email address
👤 Username  
🔐 Password
👋 First name
📝 Last name

The whole process takes less than a minute! 

Would you like to get started? (Just say "yes" or ask me anything)
```

---

### Use Cases Section

**Section Title:** "What Can You Build?"

**Use Case 1: Customer Support Agent**
```
Build intelligent support bots that understand context, search knowledge 
bases, and escalate to humans when needed. Reduce support tickets by 70%.
```

**Use Case 2: Data Analysis Agent**
```
Create agents that query databases, generate reports, and visualize data 
based on natural language requests. No SQL required for end users.
```

**Use Case 3: Workflow Automation**
```
Orchestrate complex business workflows with AI decision-making. Approval 
routing, document processing, and task assignment - all conversational.
```

**Use Case 4: Integration Hub**
```
Connect Jira, GitHub, Slack, and internal tools through a single 
conversational interface. "Create a ticket" works across all platforms.
```

---

### Getting Started Section

**Section Title:** "Get Started in 3 Steps"

**Step 1: Clone & Install**
```bash
git clone https://github.com/timothy-odofin/agenthub-be.git
cd agenthub-be
pip install -r requirements.txt
```

**Step 2: Configure**
```bash
cp .env.example .env
# Add your OpenAI API key, MongoDB URI, and Redis connection
```

**Step 3: Run**
```bash
python -m uvicorn src.app.main:app --reload
# API runs on http://localhost:8000
# Docs available at http://localhost:8000/docs
```

---

### Call to Action (Footer)

**Primary CTA:**
```
Ready to Build Your AI Agent?

[Try Live Demo]  [View Documentation]  [Star on GitHub]
```

**Secondary Links:**
- API Documentation
- GitHub Repository
- Contributing Guide
- Community Discord/Slack

---

## 🚀 Demo Flow & User Experience

### Complete Conversation Example

Here's what users will experience in the demo:

**Scenario 1: Direct User (Knows What They Want)**

```
Bot: 👋 Welcome! Let's create your account. What's your email address?
User: john@example.com

Bot: Great! Now choose a username (3-30 characters, letters, numbers, _ or -).
User: johndoe

Bot: Perfect! Create a password (min 8 characters, at least one uppercase, one lowercase, and one number).
User: MyPass123

Bot: Excellent! What's your first name?
User: John

Bot: Almost there! What's your last name?
User: Doe

Bot: 🎉 Welcome aboard, John! Your account has been created successfully!
     You can now access the full platform.
     
     [Continue to Dashboard]
```

**Scenario 2: Curious User (Asks Questions)**

```
Bot: 👋 Welcome! Let's create your account. What's your email address?
User: What do you need my email for?

Bot: Great question! Your email serves as your unique login identifier. 
     We'll also use it to send important account notifications and 
     password reset links if you ever need them. Your email is kept 
     secure and never shared with third parties.
     
     What's your email address?
User: john@example.com

Bot: Great! Now choose a username (3-30 characters, letters, numbers, _ or -).
User: What's the difference between email and username?

Bot: Good question! Your email is for logging in and communication, 
     while your username is how you'll appear to other users on the 
     platform - think of it as your public identity. For example, 
     you could use "john_dev" or "johndoe123".
     
     What username would you like?
User: john_dev

[Continues...]
```

**Scenario 3: Confused User (Needs Guidance)**

```
Bot: 👋 Welcome! Let's create your account. What's your email address?
User: What do I need in order to create an account?

Bot: To create an account, you'll need 5 things:

     📧 Email address - Your login and contact method
     👤 Username - Your public identity (3-30 characters)  
     🔐 Password - A secure password (min 8 chars, mixed case, numbers)
     👋 First name - How we'll greet you
     📝 Last name - Completes your profile
     
     The whole process takes less than a minute! Ready to get started?
User: yes

Bot: Awesome! Let's begin. What's your email address?
[Continues...]
```

---

## 🔌 API Integration

### Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.yourdomain.com/api/v1
```

### Authentication
The signup flow doesn't require authentication until completion. Once signup is complete, you'll receive JWT tokens.

### Endpoint: Start Conversation

**GET** `/auth/signup/conversation/start`

**Response:**
```json
{
  "success": true,
  "message": "👋 Welcome! Let's create your account. What's your email address?",
  "next_step": "email",
  "session_id": "abc-123-uuid",
  "is_valid": true,
  "progress_percentage": 0,
  "fields_remaining": 5,
  "user_id": null,
  "access_token": null,
  "refresh_token": null,
  "token_type": "bearer"
}
```

### Endpoint: Send Message

**POST** `/auth/signup/conversation`

**Request Body:**
```json
{
  "message": "john@example.com",
  "session_id": "abc-123-uuid",
  "current_step": "email"
}
```

**Response (Success - Valid Email):**
```json
{
  "success": true,
  "message": "Great! Now choose a username (3-30 characters, letters, numbers, _ or -).",
  "next_step": "username",
  "session_id": "abc-123-uuid",
  "is_valid": true,
  "validation_error": null,
  "progress_percentage": 20,
  "fields_remaining": 4,
  "user_id": null,
  "access_token": null,
  "refresh_token": null,
  "token_type": "bearer"
}
```

**Response (Error - Invalid Email):**
```json
{
  "success": false,
  "message": "❌ That doesn't look like a valid email. Please try again with a valid email address (e.g., john@example.com).",
  "next_step": "email",
  "session_id": "abc-123-uuid",
  "is_valid": false,
  "validation_error": "Invalid email format",
  "progress_percentage": 0,
  "fields_remaining": 5,
  "user_id": null,
  "access_token": null,
  "refresh_token": null,
  "token_type": "bearer"
}
```

**Response (Complete - Final Step):**
```json
{
  "success": true,
  "message": "🎉 Welcome aboard, John! Your account has been created successfully!",
  "next_step": "complete",
  "session_id": "abc-123-uuid",
  "is_valid": true,
  "validation_error": null,
  "progress_percentage": 100,
  "fields_remaining": 0,
  "user_id": "user-uuid-123",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Complete Flow State Diagram

```
START (current_step: null)
  ↓
EMAIL (current_step: "email")
  ↓
USERNAME (current_step: "username")
  ↓
PASSWORD (current_step: "password")
  ↓
FIRSTNAME (current_step: "firstname")
  ↓
LASTNAME (current_step: "lastname")
  ↓
COMPLETE (current_step: "complete")
```

**Important Rules:**
1. Always send `current_step` matching the `next_step` from previous response
2. Always send the same `session_id` received from the first response
3. The backend stores all validated data in Redis - don't send previous fields
4. Session expires after 5 minutes of inactivity

---

## ⚛️ React Component Examples

### 1. Chat Message Component

```typescript
// components/ChatMessage.tsx
interface ChatMessageProps {
  message: string;
  isBot: boolean;
  timestamp: Date;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  message, 
  isBot, 
  timestamp 
}) => {
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} mb-4`}>
      <div className={`max-w-[70%] ${
        isBot 
          ? 'bg-gray-100 text-gray-900' 
          : 'bg-blue-600 text-white'
      } rounded-lg px-4 py-2 shadow-sm`}>
        {isBot && <div className="text-xs text-gray-500 mb-1">🤖 AgentHub</div>}
        <div className="whitespace-pre-wrap">{message}</div>
        <div className={`text-xs mt-1 ${
          isBot ? 'text-gray-400' : 'text-blue-200'
        }`}>
          {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
    </div>
  );
};
```

### 2. Chat Input Component

```typescript
// components/ChatInput.tsx
import { useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({ 
  onSend, 
  disabled = false,
  placeholder = "Type your message..."
}) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
      />
      <button
        type="submit"
        disabled={disabled || !message.trim()}
        className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
      >
        Send
      </button>
    </form>
  );
};
```

### 3. Progress Indicator Component

```typescript
// components/SignupProgress.tsx
interface SignupProgressProps {
  progress: number;
  fieldsRemaining: number;
}

export const SignupProgress: React.FC<SignupProgressProps> = ({ 
  progress, 
  fieldsRemaining 
}) => {
  return (
    <div className="mb-4">
      <div className="flex justify-between text-sm text-gray-600 mb-2">
        <span>Signup Progress</span>
        <span>{fieldsRemaining} fields remaining</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};
```

### 4. Main Conversational Signup Component

```typescript
// components/ConversationalSignup.tsx
import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { SignupProgress } from './SignupProgress';

interface Message {
  text: string;
  isBot: boolean;
  timestamp: Date;
}

interface SignupState {
  sessionId: string | null;
  currentStep: string | null;
  progress: number;
  fieldsRemaining: number;
  isComplete: boolean;
  accessToken: string | null;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const ConversationalSignup: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [state, setState] = useState<SignupState>({
    sessionId: null,
    currentStep: null,
    progress: 0,
    fieldsRemaining: 5,
    isComplete: false,
    accessToken: null,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Start conversation on mount
  useEffect(() => {
    startConversation();
  }, []);

  const startConversation = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_BASE_URL}/auth/signup/conversation/start`);
      const data = response.data;

      // Add bot's initial message
      addBotMessage(data.message);

      // Update state
      setState({
        sessionId: data.session_id,
        currentStep: data.next_step,
        progress: data.progress_percentage,
        fieldsRemaining: data.fields_remaining,
        isComplete: false,
        accessToken: null,
      });
    } catch (err) {
      setError('Failed to start conversation. Please refresh the page.');
      console.error('Start conversation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (message: string) => {
    if (!state.sessionId || state.isComplete) return;

    // Add user message to chat
    addUserMessage(message);

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.post(`${API_BASE_URL}/auth/signup/conversation`, {
        message,
        session_id: state.sessionId,
        current_step: state.currentStep,
      });

      const data = response.data;

      // Add bot response
      addBotMessage(data.message);

      // Update state
      setState({
        sessionId: data.session_id,
        currentStep: data.next_step,
        progress: data.progress_percentage,
        fieldsRemaining: data.fields_remaining,
        isComplete: data.next_step === 'complete',
        accessToken: data.access_token,
      });

      // If signup is complete, handle success
      if (data.next_step === 'complete' && data.access_token) {
        handleSignupComplete(data.access_token, data.refresh_token);
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Something went wrong. Please try again.';
      setError(errorMessage);
      addBotMessage(`❌ ${errorMessage}`);
      console.error('Send message error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const addBotMessage = (text: string) => {
    setMessages(prev => [...prev, {
      text,
      isBot: true,
      timestamp: new Date(),
    }]);
  };

  const addUserMessage = (text: string) => {
    setMessages(prev => [...prev, {
      text,
      isBot: false,
      timestamp: new Date(),
    }]);
  };

  const handleSignupComplete = (accessToken: string, refreshToken: string) => {
    // Store tokens
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);

    // Redirect to dashboard or show success
    setTimeout(() => {
      window.location.href = '/dashboard';
    }, 2000);
  };

  return (
    <div className="max-w-2xl mx-auto p-4">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Create Your Account
        </h2>
        <p className="text-gray-600">
          Chat with our AI assistant to complete your signup - no forms required!
        </p>
      </div>

      {/* Progress */}
      {!state.isComplete && (
        <div className="bg-white rounded-lg shadow-lg p-4 mb-4">
          <SignupProgress 
            progress={state.progress} 
            fieldsRemaining={state.fieldsRemaining} 
          />
        </div>
      )}

      {/* Chat Container */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Messages */}
        <div className="h-[500px] overflow-y-auto mb-4 pr-2">
          {messages.map((msg, index) => (
            <ChatMessage
              key={index}
              message={msg.text}
              isBot={msg.isBot}
              timestamp={msg.timestamp}
            />
          ))}
          {isLoading && (
            <div className="flex justify-start mb-4">
              <div className="bg-gray-100 rounded-lg px-4 py-2">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Input */}
        {!state.isComplete ? (
          <ChatInput
            onSend={sendMessage}
            disabled={isLoading}
            placeholder="Type your response..."
          />
        ) : (
          <div className="text-center py-4">
            <div className="text-green-600 font-semibold mb-2">
              ✅ Signup Complete!
            </div>
            <div className="text-gray-600">
              Redirecting to dashboard...
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
```

### 5. Landing Page Integration

```typescript
// pages/Landing.tsx
import { useState } from 'react';
import { ConversationalSignup } from '../components/ConversationalSignup';

export const Landing: React.FC = () => {
  const [showDemo, setShowDemo] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">
          Build Intelligent AI Agents in Minutes, Not Months
        </h1>
        <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
          Open-source platform for creating production-ready AI agents with built-in 
          LLM integration, conversation management, and enterprise features.
        </p>
        <div className="flex gap-4 justify-center">
          <button
            onClick={() => setShowDemo(true)}
            className="px-8 py-4 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-lg"
          >
            Try Live Demo
          </button>
          <a
            href="https://github.com/timothy-odofin/agenthub-be"
            target="_blank"
            rel="noopener noreferrer"
            className="px-8 py-4 bg-gray-800 text-white text-lg font-semibold rounded-lg hover:bg-gray-900 transition-colors shadow-lg"
          >
            View on GitHub
          </a>
        </div>
      </section>

      {/* Demo Modal */}
      {showDemo && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b p-4 flex justify-between items-center">
              <h3 className="text-xl font-bold">Live Demo - Conversational Signup</h3>
              <button
                onClick={() => setShowDemo(false)}
                className="text-gray-500 hover:text-gray-700 text-2xl"
              >
                ×
              </button>
            </div>
            <div className="p-6">
              <ConversationalSignup />
            </div>
          </div>
        </div>
      )}

      {/* Features, use cases, etc. */}
      {/* ... rest of your landing page ... */}
    </div>
  );
};
```

---

## 🚨 Error Handling

### Common Errors and Solutions

**1. Session Expired**
```json
{
  "success": false,
  "message": "❌ Your session has expired. Please start again.",
  "next_step": "start"
}
```
**Solution:** Call GET `/auth/signup/conversation/start` again to restart

**2. Invalid Email Format**
```json
{
  "is_valid": false,
  "validation_error": "Invalid email format",
  "message": "❌ That doesn't look like a valid email..."
}
```
**Solution:** Stay on same step, prompt user to re-enter

**3. Email Already Exists**
```json
{
  "is_valid": false,
  "validation_error": "Email already registered",
  "message": "❌ This email is already registered. Please use a different email or try logging in."
}
```
**Solution:** Offer login option or prompt for different email

**4. Network Errors**
```javascript
try {
  await sendMessage(message);
} catch (error) {
  if (error.response) {
    // Server responded with error
    showError(error.response.data.detail);
  } else if (error.request) {
    // Request made but no response
    showError('Network error. Please check your connection.');
  } else {
    // Something else happened
    showError('An unexpected error occurred.');
  }
}
```

---

## 🧪 Testing the Demo

### Manual Testing Checklist

**Happy Path:**
- [ ] Click "Get Started" starts conversation
- [ ] Enter valid email → proceeds to username
- [ ] Enter unique username → proceeds to password
- [ ] Enter strong password → proceeds to firstname
- [ ] Enter firstname → proceeds to lastname
- [ ] Enter lastname → signup completes
- [ ] Tokens are received and stored
- [ ] User redirected to dashboard

**Question Handling:**
- [ ] Ask "What do I need?" at START → receives requirements list
- [ ] Ask "Why do you need my email?" at EMAIL step → receives explanation
- [ ] Ask about password requirements → receives detailed guidance
- [ ] Questions don't lose session or progress

**Validation:**
- [ ] Invalid email format → error message, stays on email step
- [ ] Email already exists → helpful error, suggests login
- [ ] Username too short → error with requirements
- [ ] Weak password → specific feedback on what's missing
- [ ] Empty name → validation error

**Edge Cases:**
- [ ] Session expires after 5 minutes → prompts restart
- [ ] Network error → retry option
- [ ] Quick successive messages → handled gracefully
- [ ] Special characters in input → properly escaped

### API Testing with cURL

```bash
# Start conversation
curl -X GET "http://localhost:8000/api/v1/auth/signup/conversation/start"

# Send email
curl -X POST "http://localhost:8000/api/v1/auth/signup/conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "john@example.com",
    "session_id": "YOUR_SESSION_ID",
    "current_step": "email"
  }'

# Send username
curl -X POST "http://localhost:8000/api/v1/auth/signup/conversation" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "johndoe",
    "session_id": "YOUR_SESSION_ID",
    "current_step": "username"
  }'

# Continue for password, firstname, lastname...
```

---

## 📝 Additional Resources

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Environment Variables Needed

```env
# Backend (Already configured)
OPENAI_API_KEY=your_openai_api_key
MONGODB_URI=mongodb://localhost:27017
REDIS_HOST=localhost
REDIS_PORT=6379

# Frontend (.env.local)
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_ENV=development
```

### TypeScript Types

```typescript
// types/signup.ts
export interface SignupResponse {
  success: boolean;
  message: string;
  next_step: 'start' | 'email' | 'username' | 'password' | 'firstname' | 'lastname' | 'complete';
  session_id: string;
  is_valid: boolean;
  validation_error: string | null;
  progress_percentage: number;
  fields_remaining: number;
  user_id: string | null;
  access_token: string | null;
  refresh_token: string | null;
  token_type: string;
}

export interface SignupRequest {
  message: string;
  session_id: string | null;
  current_step: string | null;
}
```

---

## 🎯 Key Takeaways for Frontend Engineer

1. **No Forms Required:** This is a conversational interface - think chat app, not traditional form
2. **State Management:** Track `session_id`, `current_step`, and progress throughout conversation
3. **Intelligent Responses:** Backend uses LLM to understand user intent - questions are handled naturally
4. **Error Recovery:** Validation errors keep user on same step, session expiry restarts flow
5. **Security:** All validated data stored server-side in Redis - frontend only sends current message
6. **Token Storage:** Upon completion, store `access_token` and `refresh_token` for authenticated API calls

---

## 📞 Support

Questions? Issues?
- GitHub Issues: [Create an issue](https://github.com/timothy-odofin/agenthub-be/issues)
- Email: timothy.odofin@example.com
- Documentation: [Full API Docs](http://localhost:8000/docs)

---

**Happy Building! 🚀**
