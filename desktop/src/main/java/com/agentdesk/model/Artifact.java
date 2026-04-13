package com.agentdesk.model;

public class Artifact {

    public enum ArtifactType {
        CODE, HTML, DOCUMENT, DOWNLOAD
    }

    private String title;
    private ArtifactType type;
    private String content;
    private String language;
    private String filename;

    public Artifact(String title, ArtifactType type, String content) {
        this.title = title;
        this.type = type;
        this.content = content;
    }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public ArtifactType getType() { return type; }
    public void setType(ArtifactType type) { this.type = type; }

    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }

    public String getLanguage() { return language; }
    public void setLanguage(String language) { this.language = language; }

    public String getFilename() { return filename; }
    public void setFilename(String filename) { this.filename = filename; }

    public static Artifact code(String title, String code, String language) {
        Artifact a = new Artifact(title, ArtifactType.CODE, code);
        a.setLanguage(language);
        return a;
    }

    public static Artifact html(String title, String html) {
        return new Artifact(title, ArtifactType.HTML, html);
    }

    public static Artifact document(String title, String content) {
        return new Artifact(title, ArtifactType.DOCUMENT, content);
    }

    public static Artifact download(String title, String filename, String content) {
        Artifact a = new Artifact(title, ArtifactType.DOWNLOAD, content);
        a.setFilename(filename);
        return a;
    }
}
