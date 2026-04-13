package com.agentdesk.service;

import com.agentdesk.model.Artifact;
import com.agentdesk.model.McpServer;
import javafx.application.Platform;
import javafx.concurrent.Task;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.function.Consumer;
import java.util.stream.Collectors;

@Service
public class ChatService {

    private static final List<String> GENERAL_RESPONSES = List.of(
        "I'd be happy to help you with that! Let me break this down step by step.\n\n## Key Considerations\n\nFirst, it's important to understand the core concept. The approach you're considering has several **trade-offs** worth examining:\n\n- **Performance** — this is often the primary concern, especially at scale\n- **Maintainability** — how easy will it be to modify later?\n- **Complexity** — simpler solutions tend to be more robust\n\nBased on these considerations, I'd recommend starting with the simplest approach that meets your requirements.\n\n> The best code is the code you don't have to write. Start simple, iterate fast.\n\nWould you like me to walk through a specific implementation?",

        "That's a great question! There are a few different angles to consider.\n\n## Architecture Options\n\nThe short answer is that it depends on your specific use case. Here's how I'd think about it:\n\n1. **WebSocket / SSE** — If you need real-time updates\n2. **Queue-based architecture** — For batch processing workloads\n3. **Simple polling** — If latency isn't critical\n\nEach approach has distinct advantages. The real-time option gives the best user experience but adds operational complexity.\n\n### Quick Comparison\n\n| Approach | Latency | Complexity |\n|----------|---------|------------|\n| WebSocket | Low | High |\n| Polling | Medium | Low |\n\nFor more details, check the official docs at https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API\n\nWhat's your primary constraint — latency, complexity, or infrastructure cost?",

        "Absolutely, I can help with that. This is a common pattern with well-established solutions.\n\nHere's what I'd suggest:\n\n```typescript\n// Define your data model\ninterface Config {\n  theme: 'light' | 'dark';\n  language: string;\n  notifications: boolean;\n}\n\n// Create a reactive store\nconst store = createStore<Config>(defaultConfig);\n\n// Subscribe to changes\nstore.subscribe((state) => {\n  console.log('Config updated:', state);\n});\n```\n\nThe key insight here is to **separate your state management from your UI layer**. This makes testing significantly easier and allows you to swap out the rendering framework without touching your business logic.\n\nShall I elaborate on any part of this, or would you like to see the full implementation?",

        "I've looked into this and here's what I found.\n\n## Root Cause Analysis\n\nThe issue you're describing is typically caused by one of three things:\n\n1. **Race condition** in the initialization sequence — the most common culprit\n2. **Incorrect DI ordering** — check your module configuration\n3. **Stale cache** serving outdated data — try clearing build artifacts\n\nTo diagnose, add logging at these key points:\n\n```java\nlogger.info(\"Service initializing...\");\nlogger.info(\"First request received at: {}\", Instant.now());\nlogger.error(\"Error at checkpoint: {}\", errorDetails);\n```\n\nThis will help narrow down the timing. If it's the race condition, wrapping the initialization in a proper `async` guard should resolve it.\n\n---\n\n*Pro tip:* Always use structured logging with context fields rather than string concatenation.",

        "Good thinking! Let me add some context that might help.\n\nThe pattern you're describing is essentially the **Strategy Pattern**, which is a solid choice here. It lets you define a family of algorithms, encapsulate each one, and make them interchangeable.\n\n## Benefits\n\n- Swap implementations at runtime without changing client code\n- Test each strategy independently with simple unit tests\n- Add new strategies without modifying existing ones (*Open/Closed Principle*)\n\nHere's a minimal example:\n\n```python\nfrom abc import ABC, abstractmethod\n\nclass PaymentStrategy(ABC):\n    @abstractmethod\n    def process(self, amount: float) -> bool:\n        pass\n\nclass CreditCardPayment(PaymentStrategy):\n    def process(self, amount: float) -> bool:\n        # Process credit card payment\n        return True\n\nclass PayPalPayment(PaymentStrategy):\n    def process(self, amount: float) -> bool:\n        # Process PayPal payment\n        return True\n```\n\n> **Watch out:** if the strategies share a lot of state, consider using a Context object that encapsulates the shared state.\n\nWant me to sketch out the class diagram for your specific scenario?",

        "Here's a comprehensive overview of how this works.\n\n## Processing Pipeline\n\nAt a high level, the system processes requests through three main stages:\n\n### Stage 1: Validation\n\nIncoming data is validated against the schema before any processing begins. This catches malformed requests early and provides clear error messages.\n\n### Stage 2: Transformation\n\nValid data is transformed into the internal representation. This is where **business rules** are applied — normalization, enrichment, and any computed fields.\n\n### Stage 3: Persistence\n\nThe transformed data is written to the database in a single transaction. If anything fails, the entire operation rolls back cleanly.\n\n```sql\nBEGIN TRANSACTION;\nINSERT INTO events (type, payload, created_at)\nVALUES ('user_action', '{\"action\": \"login\"}', NOW());\nCOMMIT;\n```\n\nThis pipeline approach makes it easy to add new processing steps and maintain a clear audit trail. For more info see https://martinfowler.com/articles/data-monolith-to-mesh.html",

        "I understand what you're trying to accomplish. Let me offer a slightly different perspective.\n\n## Library Recommendations\n\nRather than building from scratch, leverage an existing library:\n\n1. **Option A** — Lightweight, minimal dependencies, great for small projects\n2. **Option B** — Full-featured, excellent documentation, active community\n3. **Option C** — Enterprise-grade, built-in monitoring, steeper learning curve\n\nFor your use case, I'd lean toward **Option B**. It strikes a good balance between features and simplicity.\n\n### Getting Started\n\n```bash\nnpm install option-b@latest\nnpx option-b init --template=starter\nnpm run dev\n```\n\nThe community is very active, which means good Stack Overflow coverage and regular security updates.\n\n> *\"Good artists copy; great artists ship.\"* — don't reinvent the wheel when a battle-tested solution exists.\n\nI can help you set up any of these — which direction appeals to you most?"
    );

    private static final Map<String, List<String>> TOPIC_RESPONSES = Map.of(
        "pricing", List.of(
            "Here's an overview of the typical pricing models you'll encounter:\n\n**Free Tier**\nMost platforms offer a generous free tier that includes basic features, limited API calls, and community support. This is great for prototyping and personal projects.\n\n**Pro Plan ($20-50/month)**\nUnlocks higher rate limits, priority support, and advanced features like team collaboration, custom integrations, and analytics dashboards.\n\n**Enterprise (Custom pricing)**\nFor organizations needing SLAs, dedicated infrastructure, SSO/SAML, audit logs, and custom data retention policies.\n\nThe key is to start with the free tier and upgrade when you hit a genuine limitation, not before. Many teams over-provision early and end up paying for capacity they don't use."
        ),
        "support", List.of(
            "I can help you with support-related questions. Here are the most common channels:\n\n**Documentation**\nAlways the best first stop. The docs cover installation, configuration, API reference, and common troubleshooting steps. Most issues have a documented solution.\n\n**Community Forum**\nGreat for questions that aren't covered in the docs. The community is active and responses usually come within a few hours.\n\n**Direct Support**\nFor urgent issues or account-specific problems, you can reach the support team through the dashboard. Response times depend on your plan:\n- Free: 48 hours\n- Pro: 12 hours\n- Enterprise: 1 hour SLA\n\nIs there a specific issue I can help you troubleshoot right now?"
        ),
        "knowledge", List.of(
            "A knowledge base is a powerful tool for organizing and retrieving information efficiently. Here's how to build one that actually gets used:\n\n**Structure**\nOrganize content into clear categories with consistent naming. Use a flat hierarchy where possible — deep nesting makes content hard to find.\n\n**Content Guidelines**\n• Keep articles focused on a single topic\n• Use clear, scannable headings\n• Include code examples where relevant\n• Add a \"Quick Answer\" summary at the top\n• Link related articles to create a web of knowledge\n\n**Maintenance**\nSchedule quarterly reviews to archive outdated content and update frequently accessed articles. Track search queries that return no results — these highlight gaps in your coverage.\n\nWant me to help you set up a specific knowledge base structure?"
        )
    );

    private static final String CODE_RESPONSE = "Sure! Here's a complete implementation of a REST API endpoint with proper error handling and validation.\n\nI've created the code artifact in the panel on the right — you can copy or download it from there.\n\nThe key features of this implementation:\n\n• Input validation with clear error messages\n• Proper HTTP status codes for different scenarios\n• Async/await pattern for database operations\n• Structured logging for debugging\n\nLet me know if you'd like me to modify anything or add additional endpoints.";

    private static final Artifact CODE_ARTIFACT = Artifact.code(
        "REST API Controller",
        """
        import express from 'express';
        import { z } from 'zod';
        import { db } from './database';
        import { logger } from './logger';

        const router = express.Router();

        const CreateUserSchema = z.object({
          name: z.string().min(1).max(100),
          email: z.string().email(),
          role: z.enum(['admin', 'user', 'viewer']),
        });

        router.post('/api/users', async (req, res) => {
          try {
            const validated = CreateUserSchema.parse(req.body);

            const existing = await db.users.findByEmail(validated.email);
            if (existing) {
              return res.status(409).json({
                error: 'User already exists',
                field: 'email',
              });
            }

            const user = await db.users.create({
              ...validated,
              createdAt: new Date(),
              updatedAt: new Date(),
            });

            logger.info('User created', { userId: user.id });

            return res.status(201).json({
              id: user.id,
              name: user.name,
              email: user.email,
              role: user.role,
            });
          } catch (err) {
            if (err instanceof z.ZodError) {
              return res.status(400).json({
                error: 'Validation failed',
                details: err.errors,
              });
            }

            logger.error('Failed to create user', { error: err });
            return res.status(500).json({
              error: 'Internal server error',
            });
          }
        });

        router.get('/api/users/:id', async (req, res) => {
          const user = await db.users.findById(req.params.id);
          if (!user) {
            return res.status(404).json({ error: 'User not found' });
          }
          return res.json(user);
        });

        export default router;
        """,
        "typescript"
    );

    private static final String HTML_RESPONSE = "I've created an interactive dashboard preview for you. You can see it rendered in the artifact panel on the right.\n\nThe dashboard includes:\n\n• A responsive header with navigation\n• Key metrics displayed in card components\n• A clean, modern design using CSS Grid\n• Hover effects and smooth transitions\n\nThis is a static preview — you can download the HTML and customize it further with your own data and branding.";

    private static final Artifact HTML_ARTIFACT = Artifact.html(
        "Dashboard Preview",
        """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; color: #1a1a2e; }
            .header { background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 24px 32px; }
            .header h1 { font-size: 22px; font-weight: 600; }
            .header p { opacity: 0.85; margin-top: 4px; font-size: 14px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; padding: 24px 32px; }
            .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                     transition: transform 0.2s, box-shadow 0.2s; }
            .card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
            .card .label { font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px; }
            .card .value { font-size: 28px; font-weight: 700; margin-top: 8px; color: #6c5ce7; }
            .card .change { font-size: 12px; margin-top: 4px; color: #22c55e; }
          </style>
        </head>
        <body>
          <div class="header">
            <h1>Analytics Dashboard</h1>
            <p>Real-time metrics overview</p>
          </div>
          <div class="grid">
            <div class="card"><div class="label">Total Users</div><div class="value">12,847</div><div class="change">↑ 12.5% this month</div></div>
            <div class="card"><div class="label">Revenue</div><div class="value">$48.2K</div><div class="change">↑ 8.3% this month</div></div>
            <div class="card"><div class="label">Active Sessions</div><div class="value">1,429</div><div class="change">↑ 23.1% today</div></div>
            <div class="card"><div class="label">Uptime</div><div class="value">99.97%</div><div class="change">Last 30 days</div></div>
          </div>
        </body>
        </html>
        """
    );

    private static final String DOCUMENT_RESPONSE = "I've drafted the project specification document for you. You can view the full document in the artifact panel on the right.\n\nThe document covers:\n\n• Project objectives and scope\n• Technical architecture overview\n• Key milestones and timeline\n• Risk assessment and mitigation strategies\n\nFeel free to copy or download it, and let me know if you'd like me to expand on any section.";

    private static final Artifact DOCUMENT_ARTIFACT = Artifact.document(
        "Project Specification",
        """
        PROJECT SPECIFICATION: Cloud Migration Platform
        ================================================

        1. EXECUTIVE SUMMARY

        This document outlines the technical specification for the Cloud Migration Platform,
        a tool designed to automate and streamline the migration of on-premise applications
        to cloud infrastructure.

        2. OBJECTIVES

        - Reduce migration time by 60% compared to manual processes
        - Provide automated dependency analysis and compatibility checking
        - Support AWS, Azure, and GCP as target platforms
        - Deliver a self-service portal for development teams

        3. TECHNICAL ARCHITECTURE

        The platform consists of three core components:

        a) Discovery Engine
           - Scans source infrastructure to inventory applications and dependencies
           - Generates a dependency graph for migration planning
           - Identifies potential compatibility issues

        b) Migration Orchestrator
           - Manages the end-to-end migration workflow
           - Supports rolling, blue-green, and canary deployment strategies
           - Provides rollback capabilities at each stage

        c) Validation Suite
           - Automated smoke tests post-migration
           - Performance benchmarking against baseline metrics
           - Data integrity verification

        4. MILESTONES

        Phase 1 (Q1): Discovery Engine + basic orchestration
        Phase 2 (Q2): Full orchestration + validation suite
        Phase 3 (Q3): Self-service portal + reporting dashboard
        Phase 4 (Q4): Multi-cloud support + enterprise features

        5. RISK ASSESSMENT

        - Data loss during migration: Mitigated by incremental sync + verification
        - Downtime exceeding SLA: Mitigated by blue-green deployment support
        - Vendor lock-in: Mitigated by cloud-agnostic abstraction layer
        """
    );

    private static final Map<String, ArtifactResponse> ARTIFACT_TRIGGERS = Map.of(
        "code", new ArtifactResponse(CODE_RESPONSE, CODE_ARTIFACT),
        "api", new ArtifactResponse(CODE_RESPONSE, CODE_ARTIFACT),
        "function", new ArtifactResponse(CODE_RESPONSE, CODE_ARTIFACT),
        "implement", new ArtifactResponse(CODE_RESPONSE, CODE_ARTIFACT),
        "dashboard", new ArtifactResponse(HTML_RESPONSE, HTML_ARTIFACT),
        "html", new ArtifactResponse(HTML_RESPONSE, HTML_ARTIFACT),
        "preview", new ArtifactResponse(HTML_RESPONSE, HTML_ARTIFACT),
        "website", new ArtifactResponse(HTML_RESPONSE, HTML_ARTIFACT),
        "document", new ArtifactResponse(DOCUMENT_RESPONSE, DOCUMENT_ARTIFACT),
        "specification", new ArtifactResponse(DOCUMENT_RESPONSE, DOCUMENT_ARTIFACT)
    );

    private final Random random = new Random();
    private volatile Artifact lastArtifact;

    public Task<Void> streamResponse(String userInput, Consumer<String> onChunk, Consumer<Void> onComplete) {
        return streamResponse(userInput, List.of(), onChunk, onComplete);
    }

    public Task<Void> streamResponse(String userInput, List<McpServer> servers,
                                     Consumer<String> onChunk, Consumer<Void> onComplete) {
        ArtifactResponse artifactResponse = selectArtifactResponse(userInput);
        String baseResponse;
        if (artifactResponse != null) {
            baseResponse = artifactResponse.text;
            lastArtifact = artifactResponse.artifact;
        } else {
            baseResponse = selectResponse(userInput);
            lastArtifact = null;
        }

        String response;
        if (servers != null && !servers.isEmpty()) {
            String serverNames = servers.stream()
                    .map(McpServer::getName)
                    .collect(Collectors.joining(", "));
            response = "**Using servers:** " + serverNames + "\n\n" + baseResponse;
        } else {
            response = baseResponse;
        }

        Task<Void> task = new Task<>() {
            @Override
            protected Void call() throws Exception {
                String[] words = response.split("(?<=\\s)|(?=\\s)");
                StringBuilder built = new StringBuilder();

                for (String word : words) {
                    if (isCancelled()) break;
                    built.append(word);
                    final String chunk = built.toString();
                    Platform.runLater(() -> onChunk.accept(chunk));

                    int delay = 15 + random.nextInt(20);
                    if (word.contains("\n")) delay += 40;
                    if (word.contains(".") || word.contains("?") || word.contains("!")) delay += 25;
                    Thread.sleep(delay);
                }

                Platform.runLater(() -> onComplete.accept(null));
                return null;
            }
        };

        Thread thread = new Thread(task);
        thread.setDaemon(true);
        thread.start();
        return task;
    }

    public Artifact getLastArtifact() {
        Artifact a = lastArtifact;
        lastArtifact = null;
        return a;
    }

    private ArtifactResponse selectArtifactResponse(String userInput) {
        String lower = userInput.toLowerCase();
        for (var entry : ARTIFACT_TRIGGERS.entrySet()) {
            if (lower.contains(entry.getKey())) {
                return entry.getValue();
            }
        }
        return null;
    }

    private String selectResponse(String userInput) {
        String lower = userInput.toLowerCase();

        for (var entry : TOPIC_RESPONSES.entrySet()) {
            if (lower.contains(entry.getKey())) {
                List<String> responses = entry.getValue();
                return responses.get(random.nextInt(responses.size()));
            }
        }

        return GENERAL_RESPONSES.get(random.nextInt(GENERAL_RESPONSES.size()));
    }

    private record ArtifactResponse(String text, Artifact artifact) {}
}
