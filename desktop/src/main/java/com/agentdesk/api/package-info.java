/**
 * HTTP client abstraction for calling remote APIs from the desktop app.
 * <p>
 * Prefer {@link ApiClient#getAsync}, {@link ApiClient#postAsync}, and {@link ApiClient#deleteAsync}
 * from the JavaFX UI thread, or run synchronous {@link ApiClient} methods only on a background
 * {@link java.util.concurrent.Executor} and apply results with
 * {@link javafx.application.Platform#runLater}.
 */
package com.agentdesk.api;
