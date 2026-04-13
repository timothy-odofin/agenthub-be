package com.agentdesk.config;

import com.agentdesk.controller.LoginController;
import com.agentdesk.controller.MainController;
import javafx.animation.FadeTransition;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.stage.Stage;
import javafx.stage.StageStyle;
import javafx.util.Duration;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

@Component
public class StageInitializer {

    private final SpringFXMLLoader fxmlLoader;
    private final AppConfig appConfig;
    private Stage stage;
    private Scene scene;

    public StageInitializer(SpringFXMLLoader fxmlLoader, AppConfig appConfig) {
        this.fxmlLoader = fxmlLoader;
        this.appConfig = appConfig;
    }

    @EventListener
    public void onStageReady(StageReadyEvent event) throws Exception {
        stage = event.getStage();

        FXMLLoader loginLoader = fxmlLoader.getLoader("fxml/login-view.fxml");
        Parent loginRoot = loginLoader.load();
        LoginController loginController = loginLoader.getController();
        loginController.setOnLoginSuccess(this::transitionToMain);

        scene = new Scene(loginRoot, appConfig.getWindow().getWidth(), appConfig.getWindow().getHeight());
        scene.getStylesheets().add(getClass().getResource("/css/theme.css").toExternalForm());

        if ("dark".equalsIgnoreCase(appConfig.getTheme())) {
            scene.getStylesheets().add(getClass().getResource("/css/dark-theme.css").toExternalForm());
        }

        stage.setTitle(appConfig.getTitle());
        stage.setScene(scene);
        stage.setMinWidth(appConfig.getWindow().getMinWidth());
        stage.setMinHeight(appConfig.getWindow().getMinHeight());
        stage.initStyle(StageStyle.UNDECORATED);
        stage.show();
    }

    private void transitionToMain() {
        try {
            FXMLLoader mainLoader = fxmlLoader.getLoader("fxml/main-view.fxml");
            Parent mainRoot = mainLoader.load();
            MainController mainController = mainLoader.getController();

            mainController.setOnLogout(this::transitionToLogin);

            FadeTransition fadeOut = new FadeTransition(Duration.millis(200), scene.getRoot());
            fadeOut.setFromValue(1.0);
            fadeOut.setToValue(0.0);
            fadeOut.setOnFinished(e -> {
                scene.setRoot(mainRoot);
                mainRoot.setOpacity(0);
                FadeTransition fadeIn = new FadeTransition(Duration.millis(300), mainRoot);
                fadeIn.setFromValue(0.0);
                fadeIn.setToValue(1.0);
                fadeIn.play();
                mainController.onStageReady(stage);
            });
            fadeOut.play();
        } catch (Exception e) {
            System.err.println("Failed to load main view: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private void transitionToLogin() {
        try {
            FXMLLoader loginLoader = fxmlLoader.getLoader("fxml/login-view.fxml");
            Parent loginRoot = loginLoader.load();
            LoginController loginController = loginLoader.getController();
            loginController.setOnLoginSuccess(this::transitionToMain);

            FadeTransition fadeOut = new FadeTransition(Duration.millis(200), scene.getRoot());
            fadeOut.setFromValue(1.0);
            fadeOut.setToValue(0.0);
            fadeOut.setOnFinished(e -> {
                scene.setRoot(loginRoot);
                loginRoot.setOpacity(0);
                FadeTransition fadeIn = new FadeTransition(Duration.millis(300), loginRoot);
                fadeIn.setFromValue(0.0);
                fadeIn.setToValue(1.0);
                fadeIn.play();
            });
            fadeOut.play();
        } catch (Exception e) {
            System.err.println("Failed to load login view: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
