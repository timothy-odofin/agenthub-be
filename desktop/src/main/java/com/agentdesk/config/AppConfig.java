package com.agentdesk.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "app")
public class AppConfig {

    private String title = "AgentDesk";
    private String theme = "light";
    private Window window = new Window();

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getTheme() {
        return theme;
    }

    public void setTheme(String theme) {
        this.theme = theme;
    }

    public Window getWindow() {
        return window;
    }

    public void setWindow(Window window) {
        this.window = window;
    }

    public static class Window {
        private double width = 1200;
        private double height = 800;
        private double minWidth = 800;
        private double minHeight = 600;

        public double getWidth() {
            return width;
        }

        public void setWidth(double width) {
            this.width = width;
        }

        public double getHeight() {
            return height;
        }

        public void setHeight(double height) {
            this.height = height;
        }

        public double getMinWidth() {
            return minWidth;
        }

        public void setMinWidth(double minWidth) {
            this.minWidth = minWidth;
        }

        public double getMinHeight() {
            return minHeight;
        }

        public void setMinHeight(double minHeight) {
            this.minHeight = minHeight;
        }
    }
}
