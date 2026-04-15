package com.agentdesk;

import javafx.application.Application;
import org.springframework.boot.autoconfigure.SpringBootApplication;

import java.util.logging.Level;
import java.util.logging.Logger;

@SpringBootApplication
public class AgentDeskApplication {

    public static void main(String[] args) {
        Logger.getLogger("com.sun.javafx.application.PlatformImpl").setLevel(Level.SEVERE);
        Application.launch(AgentDesk.class, args);
    }
}
