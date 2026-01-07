# Conversational Authentication API Guide

## Overview

The AgentHub API now supports **conversational (chatbot-style) authentication** alongside traditional REST endpoints. This allows your frontend to provide a natural, step-by-step signup experience.

---

## 🎯 Why Conversational Signup?

✅ **Better UX**: Users interact naturally, one field at a time  
✅ **Real-time Validation**: Immediate feedback on each input  
✅ **Progress Tracking**: Users see how far along they are  
✅ **Error Recovery**: Clear, friendly error messages  
✅ **Mobile-Friendly**: Works great in chat interfaces  

---

## 📍 Endpoints

### **Traditional Endpoints** (Still Available)
- `POST /api/v1/auth/signup` - Traditional all-at-once signup
- `POST /api/v1/auth/login` - Traditional login
- `POST /api/v1/auth/refresh` - Refresh access token

### **New Conversational Endpoints**
- `GET /api/v1/auth/signup/conversation/start` - Start conversational signup
- `POST /api/v1/auth/signup/conversation` - Continue conversational signup

---

## 🚀 Conversational Signup Flow

### **Step-by-Step Process**

```
START → EMAIL → USERNAME → PASSWORD → FIRSTNAME → LASTNAME → COMPLETE
```

### **Frontend Implementation Example**

```javascript
// 1. START: Initialize conversation
const startSignup = async () => {
  const response = await fetch('/api/v1/auth/signup/conversation/start');
  const data = await response.json();
  
  // Response:
  // {
  //   "success": true,
  //   "message": "👋 Welcome! Let's create your account. What's your email address?",
  //   "next_step": "email",
  //   "session_id": "uuid-here",
  //   "progress_percentage": 0,
  //   "fields_remaining": 5
  // }
  
  return data;
};

// 2. User provides email
const submitEmail = async (sessionId, email) => {
  const response = await fetch('/api/v1/auth/signup/conversation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: email,
      session_id: sessionId,
      current_step: 'email'
    })
  });
  
  const data = await response.json();
  
  // If valid:
  // {
  //   "success": true,
  //   "message": "Great! Now choose a username...",
  //   "next_step": "username",
  //   "is_valid": true,
  //   "progress_percentage": 20,
  //   "fields_remaining": 4
  // }
  
  // If invalid:
  // {
  //   "success": false,
  //   "message": "❌ That doesn't look like a valid email...",
  //   "next_step": "email",  // Stay on same step
  //   "is_valid": false,
  //   "validation_error": "Invalid email format"
  // }
  
  return data;
};

// 3. User provides username
const submitUsername = async (sessionId, email, username) => {
  const response = await fetch('/api/v1/auth/signup/conversation', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: username,
      session_id: sessionId,
      current_step: 'username',
      email: email  // Pass along previously collected data
    })
  });
  
  return await response.json();
};

// 4. Continue for password, firstname, lastname...

// 5. COMPLETE: When all fields collected
// {
//   "success": true,
//   "message": "🎉 Welcome aboard, John! Your account has been created...",
//   "next_step": "complete",
//   "user_id": "user-id-here",
//   "access_token": "jwt-token-here",
//   "refresh_token": "refresh-token-here",
//   "token_type": "bearer",
//   "progress_percentage": 100,
//   "fields_remaining": 0
// }
```

---

## 📋 Complete React Example

```tsx
import { useState } from 'react';

interface SignupState {
  sessionId: string;
  currentStep: string;
  email?: string;
  username?: string;
  password?: string;
  firstname?: string;
  lastname?: string;
}

export default function ConversationalSignup() {
  const [messages, setMessages] = useState<Array<{role: 'bot' | 'user', text: string}>>([]);
  const [state, setState] = useState<SignupState | null>(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [tokens, setTokens] = useState<{access: string, refresh: string} | null>(null);

  // Start conversation
  const startConversation = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/auth/signup/conversation/start');
      const data = await response.json();
      
      setMessages([{ role: 'bot', text: data.message }]);
      setState({
        sessionId: data.session_id,
        currentStep: data.next_step
      });
    } catch (error) {
      console.error('Error starting signup:', error);
    }
    setLoading(false);
  };

  // Handle user input
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !state) return;

    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', text: input }]);
    setLoading(true);

    try {
      const response = await fetch('/api/v1/auth/signup/conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          session_id: state.sessionId,
          current_step: state.currentStep,
          email: state.email,
          username: state.username,
          password: state.password,
          firstname: state.firstname,
          lastname: state.lastname
        })
      });

      const data = await response.json();

      // Add bot response
      setMessages(prev => [...prev, { role: 'bot', text: data.message }]);

      // Update state based on current step
      const newState = { ...state };
      if (data.is_valid) {
        // Move to next step, save current input
        switch (state.currentStep) {
          case 'email':
            newState.email = input;
            break;
          case 'username':
            newState.username = input;
            break;
          case 'password':
            newState.password = input;
            break;
          case 'firstname':
            newState.firstname = input;
            break;
          case 'lastname':
            newState.lastname = input;
            break;
        }
      }
      newState.currentStep = data.next_step;
      setState(newState);

      // Check if signup complete
      if (data.next_step === 'complete' && data.access_token) {
        setTokens({
          access: data.access_token,
          refresh: data.refresh_token
        });
        // Store tokens and redirect
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        // Redirect to dashboard or show success
      }

      setInput('');
    } catch (error) {
      console.error('Error submitting:', error);
      setMessages(prev => [...prev, { 
        role: 'bot', 
        text: '❌ Something went wrong. Please try again.' 
      }]);
    }
    setLoading(false);
  };

  return (
    <div className="chatbot-signup">
      {!state ? (
        <button onClick={startConversation}>Start Signup</button>
      ) : (
        <>
          <div className="messages">
            {messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                {msg.text}
              </div>
            ))}
            {loading && <div className="typing-indicator">Bot is typing...</div>}
          </div>
          
          <form onSubmit={handleSubmit}>
            <input
              type={state.currentStep === 'password' ? 'password' : 'text'}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your answer..."
              disabled={loading || state.currentStep === 'complete'}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
          
          {state.currentStep !== 'complete' && (
            <div className="progress">
              Progress: {messages.length} / 5 fields
            </div>
          )}
        </>
      )}
    </div>
  );
}
```

---

## 🎨 UI/UX Recommendations

### **Chat Interface Design**
```
┌─────────────────────────────────────┐
│  AgentHub Sign Up                   │
├─────────────────────────────────────┤
│                                     │
│  🤖 Bot: Welcome! Let's create...   │
│                                     │
│     👤 You: john@example.com        │
│                                     │
│  🤖 Bot: Great! Now choose a...     │
│                                     │
│     👤 You: johndoe                 │
│                                     │
│  [Progress: ████░░░░░ 40%]          │
│                                     │
│  ┌──────────────────────────────┐  │
│  │ Type your answer...          │  │
│  └──────────────────────────────┘  │
│               [Send]                │
└─────────────────────────────────────┘
```

### **State Management Tips**

1. **Preserve scroll position** - Auto-scroll to latest message
2. **Show typing indicators** - When waiting for bot response
3. **Password masking** - Use `type="password"` for password step
4. **Validation feedback** - Show inline errors with ❌ emoji
5. **Progress bar** - Use `progress_percentage` from response
6. **Session persistence** - Store `session_id` in state/context

---

## 🔒 Security Considerations

1. **Never log passwords** - Don't console.log the password step
2. **HTTPS only** - Always use HTTPS in production
3. **Token storage** - Store tokens in httpOnly cookies or secure storage
4. **CORS configuration** - Already configured in backend
5. **Rate limiting** - Consider adding on frontend to prevent spam

---

## 🧪 Testing the API

### **Using cURL**

```bash
# 1. Start conversation
curl -X GET https://your-api.onrender.com/api/v1/auth/signup/conversation/start

# 2. Submit email
curl -X POST https://your-api.onrender.com/api/v1/auth/signup/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "message": "john@example.com",
    "session_id": "your-session-id",
    "current_step": "email"
  }'

# 3. Submit username
curl -X POST https://your-api.onrender.com/api/v1/auth/signup/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "message": "johndoe",
    "session_id": "your-session-id",
    "current_step": "username",
    "email": "john@example.com"
  }'

# Continue for password, firstname, lastname...
```

---

## 📊 Response Schema

### **ConversationalSignupResponse**

```typescript
interface ConversationalSignupResponse {
  success: boolean;              // Whether current step succeeded
  message: string;               // Bot's response message
  next_step: SignupStep;         // Next step in flow
  session_id: string;            // Session ID for tracking
  is_valid: boolean;             // Whether input was valid
  validation_error?: string;     // Error message if invalid
  progress_percentage: number;   // 0-100%
  fields_remaining: number;      // How many fields left
  
  // Only populated when signup complete
  user_id?: string;
  access_token?: string;
  refresh_token?: string;
  token_type: string;            // "bearer"
}
```

### **SignupStep Enum**

```typescript
type SignupStep = 
  | "start"      // Initial greeting
  | "email"      // Collecting email
  | "username"   // Collecting username
  | "password"   // Collecting password
  | "firstname"  // Collecting first name
  | "lastname"   // Collecting last name
  | "complete";  // Signup finished
```

---

## ❓ FAQs

**Q: Can I still use the traditional signup endpoint?**  
A: Yes! `POST /api/v1/auth/signup` still works for traditional forms.

**Q: What if user refreshes the page mid-signup?**  
A: Session data is not persisted server-side. You'll need to handle state persistence on frontend (e.g., sessionStorage).

**Q: Can I skip steps or go backwards?**  
A: Not currently supported. Design enforces linear flow for simplicity.

**Q: How do I handle "user already exists" errors?**  
A: Check the `validation_error` field in the response when `is_valid` is false.

**Q: Can I customize the bot messages?**  
A: Backend messages are predefined. You can modify them in `conversational_auth_service.py`.

---

## 🎉 Next Steps

1. ✅ Backend is ready - endpoints deployed on Render
2. 📱 Build your chat UI using the React example above
3. 🎨 Customize styling to match your design system
4. 🧪 Test with real users
5. 📊 Add analytics to track signup completion rates

**Happy building! 🚀**
