// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the polyagent_sessions database
db = db.getSiblingDB('polyagent_sessions');

// Create collections for session management
db.createCollection('sessions');
db.createCollection('messages');

// Create indexes for better performance
// Index on user_id for sessions
db.sessions.createIndex({ "user_id": 1 });

// Index on session_id and timestamp for messages
db.messages.createIndex({ "session_id": 1, "timestamp": 1 });

// Index on user_id for messages (for cross-session queries)
db.messages.createIndex({ "user_id": 1, "timestamp": 1 });

// Compound index for efficient session + user queries
db.sessions.createIndex({ "user_id": 1, "created_at": -1 });

// TTL index for automatic cleanup of old sessions (optional - 90 days)
// db.sessions.createIndex({ "created_at": 1 }, { expireAfterSeconds: 7776000 });

print("MongoDB initialization completed successfully!");
print("Database: polyagent_sessions");
print("Collections created: sessions, messages");
print("Indexes created for optimal performance");
