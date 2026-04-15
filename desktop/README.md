# ClaudeFX — Claude Desktop Clone in JavaFX

A faithful recreation of the Claude Desktop UI built with JavaFX 21.

## Features
- Sidebar with conversation list, search, and new chat button
- Chat area with streaming-style message responses
- User and assistant message bubbles (matching Claude's style)
- Welcome screen with suggestion chips
- Model selector toolbar
- User profile section
- Keyboard shortcuts (Enter to send, Shift+Enter for new line)
- Auto-resizing input area

## Requirements
- Java 17 or later (Java 21 recommended)
- Maven 3.8+

## Speech to text (offline)

The mic buttons can use [Vosk](https://alphacephei.com/vosk/) on your machine (no speech audio is sent to a server) or macOS Speech when `app.stt.provider` is `auto` and the native bridge is installed.

**Default English model (Vosk):** On first run, if the folder at `app.stt.model-path` is missing the Vosk layout, the app downloads the small English model (`vosk-model-small-en-us-0.15`) over HTTPS in the background—unless you set `app.stt.provider: os` (macOS native only) or `auto` when macOS native STT is available (so Vosk is not needed). If the model is already present, nothing is downloaded.

- Override the zip URL with `app.stt.auto-download-model-url` if you mirror the file.
- Disable automatic download with `app.stt.auto-download-model: false` and install a model manually from [Vosk models](https://alphacephei.com/vosk/models).

The extracted folder must contain the usual Vosk layout (including an `am` directory). Grant microphone permission when the OS prompts.

Set `app.stt.enabled: false` to disable STT checks.

### macOS native library (`vosk_recognizer_set_grm` / symbol not found)

The `com.alphacephei:vosk` JAR’s bundled `libvosk.dylib` can be out of sync with the Java bindings ([upstream issue](https://github.com/alphacep/vosk-api/issues/1235)). The app no longer loads Vosk at startup; if recognition still fails, build or obtain a matching `libvosk.dylib` and set:

```yaml
app:
  stt:
    native-library-path: /path/to/folder/containing/libvosk.dylib
```

## Run

```bash
cd claudefx
mvn javafx:run
```

## Build a runnable JAR

```bash
mvn package
```

## Project Structure

```
claudefx/
├── pom.xml
└── src/main/
    ├── java/
    │   ├── module-info.java
    │   └── com/claudefx/
    │       ├── ClaudeFXApp.java          # Entry point
    │       ├── controller/
    │       │   └── MainController.java   # Wires sidebar + chat
    │       ├── model/
    │       │   ├── Conversation.java     # Conversation model
    │       │   └── ChatMessage.java      # Message model
    │       ├── service/
    │       │   └── ChatService.java      # Simulated streaming
    │       └── component/
    │           ├── Sidebar.java          # Left sidebar
    │           ├── ChatArea.java         # Main chat view
    │           └── MessageBubble.java    # Message rendering
    └── resources/
        └── com/claudefx/css/
            └── theme.css                # Full UI theme
```

## Connecting to Real Claude API

To wire this up to the real Anthropic API, replace `ChatService.java`'s
`streamResponse` method with an actual HTTP call:

```java
// Use OkHttp or Java HttpClient to call:
// POST https://api.anthropic.com/v1/messages
// Headers: x-api-key, anthropic-version, content-type
// Body: { model, messages, stream: true, max_tokens }
// Parse SSE chunks and feed to the onChunk consumer
```

Add your API key via an environment variable `ANTHROPIC_API_KEY`.
