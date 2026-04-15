package com.agentdesk;

import com.agentdesk.config.StageReadyEvent;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.stage.Stage;
import org.springframework.boot.SpringApplication;
import org.springframework.context.ConfigurableApplicationContext;

public class AgentDesk extends Application {

    private ConfigurableApplicationContext springContext;

    @Override
    public void init() {
        springContext = SpringApplication.run(AgentDeskApplication.class);
    }

    @Override
    public void start(Stage primaryStage) {
        springContext.publishEvent(new StageReadyEvent(primaryStage));
    }

    @Override
    public void stop() {
        springContext.close();
        Platform.exit();
    }
}
