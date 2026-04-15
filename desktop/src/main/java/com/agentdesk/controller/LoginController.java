package com.agentdesk.controller;

import com.agentdesk.api.ApiExceptionMapper;
import com.agentdesk.service.AuthService;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.PasswordField;
import javafx.scene.control.ProgressIndicator;
import javafx.scene.control.TextField;
import javafx.stage.Stage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Scope;
import org.springframework.stereotype.Component;

/**
 * Controller for {@code login-view.fxml}.
 *
 * <h3>Flow</h3>
 * <ol>
 *   <li>User fills in email + password and clicks "Sign in".</li>
 *   <li>The form is locked (inputs disabled, spinner shown, error cleared).</li>
 *   <li>{@link AuthService#login(String, String)} is called off the JavaFX thread.</li>
 *   <li>On success → {@link #onLoginSuccess} callback fires on the JavaFX thread.</li>
 *   <li>On failure → user-facing error is shown and the form is re-enabled.</li>
 * </ol>
 *
 * <h3>SSO / Google</h3>
 * Not yet implemented server-side; clicking those buttons shows a "not yet available" message.
 */
@Component
@Scope("prototype")
public final class LoginController {

    private static final Logger log = LoggerFactory.getLogger(LoginController.class);

    // ---- injected by Spring --------------------------------------------------
    private final AuthService        authService;
    private final ApiExceptionMapper exceptionMapper;

    // ---- injected by FXMLLoader ---------------------------------------------
    @FXML private TextField          emailField;
    @FXML private PasswordField      passwordField;
    @FXML private Button             signInBtn;
    @FXML private Label              errorLabel;
    @FXML private ProgressIndicator  loadingIndicator;

    // ---- wired by the view host ---------------------------------------------
    private Runnable onLoginSuccess;

    public LoginController(AuthService authService, ApiExceptionMapper exceptionMapper) {
        this.authService     = authService;
        this.exceptionMapper = exceptionMapper;
    }

    /** Called by the view host so this controller can notify the app to switch scenes. */
    public void setOnLoginSuccess(Runnable handler) {
        this.onLoginSuccess = handler;
    }

    // -------------------------------------------------------------------------
    // FXML event handlers
    // -------------------------------------------------------------------------

    @FXML
    private void handleEmailLogin() {
        final String identifier = emailField.getText().trim();
        final String password   = passwordField.getText();

        clearError();

        if (identifier.isEmpty()) {
            showError("Please enter your email or username.");
            emailField.requestFocus();
            return;
        }
        if (password.isEmpty()) {
            showError("Please enter your password.");
            passwordField.requestFocus();
            return;
        }

        setFormLocked(true);

        authService.login(identifier, password)
                .whenComplete((response, throwable) -> Platform.runLater(() -> {
                    setFormLocked(false);
                    if (throwable != null) {
                        showError(exceptionMapper.toUserMessage(throwable));
                        log.warn("Login UI error: {}", exceptionMapper.toUserMessage(throwable));
                        return;
                    }
                    if (!response.success()) {
                        final String msg = response.message() != null && !response.message().isBlank()
                                ? response.message()
                                : "Sign-in failed. Check your credentials.";
                        showError(msg);
                        return;
                    }
                    log.info("Login successful — switching to main view");
                    if (onLoginSuccess != null) {
                        onLoginSuccess.run();
                    }
                }));
    }

    @FXML
    private void handleSsoLogin() {
        showError("Okta SSO is not yet available in the desktop client.");
    }

    @FXML
    private void handleGoogleLogin() {
        showError("Google login is not yet available in the desktop client.");
    }

    @FXML
    private void handleMinimize() {
        final Stage stage = getStage();
        if (stage != null) {
            stage.setIconified(true);
        }
    }

    @FXML
    private void handleClose() {
        final Stage stage = getStage();
        if (stage != null) {
            stage.close();
        }
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private void setFormLocked(boolean locked) {
        emailField.setDisable(locked);
        passwordField.setDisable(locked);
        signInBtn.setDisable(locked);
        loadingIndicator.setVisible(locked);
        loadingIndicator.setManaged(locked);
    }

    private void showError(String message) {
        errorLabel.setText(message);
        errorLabel.setVisible(true);
        errorLabel.setManaged(true);
        emailField.getStyleClass().remove("login-input-error");
        passwordField.getStyleClass().remove("login-input-error");
    }

    private void clearError() {
        errorLabel.setVisible(false);
        errorLabel.setManaged(false);
        errorLabel.setText("");
        emailField.getStyleClass().remove("login-input-error");
        passwordField.getStyleClass().remove("login-input-error");
    }

    private Stage getStage() {
        if (emailField != null && emailField.getScene() != null) {
            return (Stage) emailField.getScene().getWindow();
        }
        return null;
    }
}

