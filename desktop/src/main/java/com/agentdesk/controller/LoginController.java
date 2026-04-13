package com.agentdesk.controller;

import javafx.fxml.FXML;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;
import javafx.stage.Stage;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

@Component
@Scope("prototype")
public class LoginController {

    @FXML private TextField emailField;
    @FXML private PasswordField passwordField;

    private Runnable onLoginSuccess;

    public void setOnLoginSuccess(Runnable handler) {
        this.onLoginSuccess = handler;
    }

    @FXML
    private void handleSsoLogin() {
        doLogin();
    }

    @FXML
    private void handleGoogleLogin() {
        doLogin();
    }

    @FXML
    private void handleEmailLogin() {
        doLogin();
    }

    private void doLogin() {
        if (onLoginSuccess != null) {
            onLoginSuccess.run();
        }
    }

    @FXML
    private void handleMinimize() {
        Stage stage = getStage();
        if (stage != null) stage.setIconified(true);
    }

    @FXML
    private void handleClose() {
        Stage stage = getStage();
        if (stage != null) stage.close();
    }

    private Stage getStage() {
        if (emailField != null && emailField.getScene() != null) {
            return (Stage) emailField.getScene().getWindow();
        }
        return null;
    }
}
