package com.agentdesk.util;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Cross-platform utility for opening a URL in the system's default browser.
 *
 * <p>Intentionally avoids {@code java.awt.Desktop} because calling it from the
 * JavaFX Application Thread (or any thread in a JavaFX process that never
 * fully initialised AWT) prints the macOS warning:
 * <pre>
 *   [JRSAppKitAWT markAppIsDaemon]: Process manager already initialized:
 *   can't fully enable headless mode.
 * </pre>
 * and silently swallows the open request.
 *
 * <p>Instead we delegate to the OS-native command:
 * <ul>
 *   <li>macOS  — {@code open <url>}</li>
 *   <li>Linux  — {@code xdg-open <url>}</li>
 *   <li>Windows — {@code cmd /c start "" <url>}</li>
 * </ul>
 * The command is executed on a short-lived daemon thread so it never blocks
 * the JavaFX Application Thread.
 */
public final class BrowserUtil {

    private static final Logger log = LoggerFactory.getLogger(BrowserUtil.class);

    private BrowserUtil() {}

    /**
     * Opens {@code url} in the default browser.
     * Safe to call from any thread, including the JavaFX Application Thread.
     *
     * @param url the URL to open; must be non-null
     */
    public static void open(String url) {
        if (url == null || url.isBlank()) return;

        Thread t = new Thread(() -> {
            try {
                ProcessBuilder pb = buildCommand(url);
                pb.inheritIO();
                pb.start();
                log.debug("Opened URL in browser: {}", url);
            } catch (Exception e) {
                log.warn("Failed to open URL '{}': {}", url, e.getMessage());
            }
        }, "browser-open");
        t.setDaemon(true);
        t.start();
    }

    private static ProcessBuilder buildCommand(String url) {
        String os = System.getProperty("os.name", "").toLowerCase();
        if (os.contains("mac")) {
            return new ProcessBuilder("open", url);
        } else if (os.contains("win")) {
            // "start" is a shell built-in; needs cmd wrapper.
            // The empty first arg is the window title (required when the URL contains special chars).
            return new ProcessBuilder("cmd", "/c", "start", "", url);
        } else {
            // Linux / FreeBSD / other Unix
            return new ProcessBuilder("xdg-open", url);
        }
    }
}
