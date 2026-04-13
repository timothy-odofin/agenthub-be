package com.agentdesk.config;

import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import org.springframework.context.ApplicationContext;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
public class SpringFXMLLoader {

    private final ApplicationContext context;
    private final ResourceLoader resourceLoader;

    public SpringFXMLLoader(ApplicationContext context, ResourceLoader resourceLoader) {
        this.context = context;
        this.resourceLoader = resourceLoader;
    }

    public Parent load(String fxmlPath) throws IOException {
        FXMLLoader loader = new FXMLLoader();
        loader.setControllerFactory(context::getBean);
        loader.setLocation(resourceLoader.getResource("classpath:" + fxmlPath).getURL());
        return loader.load();
    }

    public <T> T loadWithController(String fxmlPath) throws IOException {
        FXMLLoader loader = new FXMLLoader();
        loader.setControllerFactory(context::getBean);
        loader.setLocation(resourceLoader.getResource("classpath:" + fxmlPath).getURL());
        loader.load();
        return loader.getController();
    }

    public FXMLLoader getLoader(String fxmlPath) throws IOException {
        FXMLLoader loader = new FXMLLoader();
        loader.setControllerFactory(context::getBean);
        loader.setLocation(resourceLoader.getResource("classpath:" + fxmlPath).getURL());
        return loader;
    }
}
