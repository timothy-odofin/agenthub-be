package com.agentdesk.component;

import com.agentdesk.util.BrowserUtil;
import javafx.geometry.Insets;
import javafx.scene.Node;
import javafx.scene.control.Hyperlink;
import javafx.scene.control.Label;
import javafx.scene.control.Separator;
import javafx.scene.layout.VBox;
import javafx.scene.text.Text;
import javafx.scene.text.TextFlow;
import org.commonmark.node.*;
import org.commonmark.parser.Parser;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MarkdownRenderer {

    private static final Parser PARSER = Parser.builder().build();
    private static final Pattern URL_PATTERN = Pattern.compile(
            "(https?://[\\w\\-._~:/?#\\[\\]@!$&'()*+,;=%]+)"
    );

    public static VBox render(String markdown) {
        VBox container = new VBox(6);
        container.getStyleClass().add("md-container");
        container.setMaxWidth(680);

        if (markdown == null || markdown.isBlank()) {
            return container;
        }

        org.commonmark.node.Node document = PARSER.parse(markdown);
        renderChildren(document, container);
        return container;
    }

    private static void renderChildren(org.commonmark.node.Node parent, VBox container) {
        org.commonmark.node.Node child = parent.getFirstChild();
        while (child != null) {
            Node rendered = renderBlock(child);
            if (rendered != null) {
                container.getChildren().add(rendered);
            }
            child = child.getNext();
        }
    }

    private static Node renderBlock(org.commonmark.node.Node node) {
        if (node instanceof Heading heading) {
            return renderHeading(heading);
        } else if (node instanceof Paragraph paragraph) {
            return renderParagraph(paragraph);
        } else if (node instanceof FencedCodeBlock fenced) {
            return new CodeBlockView(fenced.getLiteral(), fenced.getInfo());
        } else if (node instanceof IndentedCodeBlock indented) {
            return new CodeBlockView(indented.getLiteral(), null);
        } else if (node instanceof BulletList bulletList) {
            return renderBulletList(bulletList);
        } else if (node instanceof OrderedList orderedList) {
            return renderOrderedList(orderedList);
        } else if (node instanceof BlockQuote blockQuote) {
            return renderBlockQuote(blockQuote);
        } else if (node instanceof ThematicBreak) {
            Separator sep = new Separator();
            sep.getStyleClass().add("md-hr");
            return sep;
        } else if (node instanceof HtmlBlock htmlBlock) {
            Text text = new Text(htmlBlock.getLiteral());
            text.getStyleClass().add("assistant-message-text");
            TextFlow flow = new TextFlow(text);
            flow.getStyleClass().add("md-paragraph");
            return flow;
        }
        return null;
    }

    private static Node renderHeading(Heading heading) {
        List<Node> inlineNodes = renderInlineChildren(heading);
        StringBuilder sb = new StringBuilder();
        for (Node n : inlineNodes) {
            if (n instanceof Text t) sb.append(t.getText());
            else if (n instanceof Hyperlink h) sb.append(h.getText());
        }

        Label label = new Label(sb.toString());
        String styleClass = switch (heading.getLevel()) {
            case 1 -> "md-h1";
            case 2 -> "md-h2";
            case 3 -> "md-h3";
            default -> "md-h4";
        };
        label.getStyleClass().add(styleClass);
        label.setWrapText(true);
        label.setMaxWidth(680);
        return label;
    }

    private static Node renderParagraph(Paragraph paragraph) {
        List<Node> inlineNodes = renderInlineChildren(paragraph);
        TextFlow flow = new TextFlow();
        flow.getStyleClass().add("md-paragraph");
        flow.setMaxWidth(680);
        flow.getChildren().addAll(inlineNodes);
        return flow;
    }

    private static Node renderBulletList(BulletList list) {
        VBox listBox = new VBox(2);
        listBox.getStyleClass().add("md-list");
        listBox.setPadding(new Insets(0, 0, 0, 4));

        org.commonmark.node.Node item = list.getFirstChild();
        while (item != null) {
            if (item instanceof ListItem listItem) {
                ListItemView itemView = new ListItemView("\u2022");
                renderListItemContent(listItem, itemView);
                listBox.getChildren().add(itemView);
            }
            item = item.getNext();
        }
        return listBox;
    }

    private static Node renderOrderedList(OrderedList list) {
        VBox listBox = new VBox(2);
        listBox.getStyleClass().add("md-list");
        listBox.setPadding(new Insets(0, 0, 0, 4));

        int number = list.getStartNumber();
        org.commonmark.node.Node item = list.getFirstChild();
        while (item != null) {
            if (item instanceof ListItem listItem) {
                ListItemView itemView = new ListItemView(number + ".");
                renderListItemContent(listItem, itemView);
                listBox.getChildren().add(itemView);
                number++;
            }
            item = item.getNext();
        }
        return listBox;
    }

    private static void renderListItemContent(ListItem listItem, ListItemView itemView) {
        org.commonmark.node.Node child = listItem.getFirstChild();
        while (child != null) {
            if (child instanceof Paragraph paragraph) {
                List<Node> inlines = renderInlineChildren(paragraph);
                TextFlow flow = new TextFlow();
                flow.getStyleClass().add("md-paragraph");
                flow.getChildren().addAll(inlines);
                itemView.addContent(flow);
            } else {
                Node rendered = renderBlock(child);
                if (rendered != null) {
                    itemView.addContent(rendered);
                }
            }
            child = child.getNext();
        }
    }

    private static Node renderBlockQuote(BlockQuote blockQuote) {
        VBox quoteBox = new VBox(4);
        quoteBox.getStyleClass().add("md-blockquote");
        quoteBox.setPadding(new Insets(8, 12, 8, 16));

        org.commonmark.node.Node child = blockQuote.getFirstChild();
        while (child != null) {
            Node rendered = renderBlock(child);
            if (rendered != null) {
                quoteBox.getChildren().add(rendered);
            }
            child = child.getNext();
        }
        return quoteBox;
    }

    private static List<Node> renderInlineChildren(org.commonmark.node.Node parent) {
        List<Node> nodes = new ArrayList<>();
        org.commonmark.node.Node child = parent.getFirstChild();
        while (child != null) {
            renderInline(child, nodes, false, false);
            child = child.getNext();
        }
        return nodes;
    }

    private static void renderInline(org.commonmark.node.Node node, List<Node> nodes,
                                     boolean bold, boolean italic) {
        if (node instanceof org.commonmark.node.Text textNode) {
            String literal = textNode.getLiteral();
            addTextWithAutoLinks(literal, nodes, bold, italic);
        } else if (node instanceof StrongEmphasis) {
            org.commonmark.node.Node child = node.getFirstChild();
            while (child != null) {
                renderInline(child, nodes, true, italic);
                child = child.getNext();
            }
        } else if (node instanceof Emphasis) {
            org.commonmark.node.Node child = node.getFirstChild();
            while (child != null) {
                renderInline(child, nodes, bold, true);
                child = child.getNext();
            }
        } else if (node instanceof Code code) {
            Label codeLabel = new Label(code.getLiteral());
            codeLabel.getStyleClass().add("md-inline-code");
            nodes.add(codeLabel);
        } else if (node instanceof Link link) {
            StringBuilder linkText = new StringBuilder();
            org.commonmark.node.Node child = link.getFirstChild();
            while (child != null) {
                if (child instanceof org.commonmark.node.Text t) {
                    linkText.append(t.getLiteral());
                }
                child = child.getNext();
            }
            Hyperlink hyperlink = new Hyperlink(linkText.toString());
            hyperlink.getStyleClass().add("md-link");
            hyperlink.setOnAction(e -> openUrl(link.getDestination()));
            nodes.add(hyperlink);
        } else if (node instanceof SoftLineBreak) {
            nodes.add(new Text(" "));
        } else if (node instanceof HardLineBreak) {
            nodes.add(new Text("\n"));
        } else if (node instanceof HtmlInline htmlInline) {
            Text text = new Text(htmlInline.getLiteral());
            text.getStyleClass().add("assistant-message-text");
            nodes.add(text);
        }
    }

    private static void addTextWithAutoLinks(String text, List<Node> nodes,
                                             boolean bold, boolean italic) {
        Matcher matcher = URL_PATTERN.matcher(text);
        int lastEnd = 0;

        while (matcher.find()) {
            if (matcher.start() > lastEnd) {
                nodes.add(createStyledText(text.substring(lastEnd, matcher.start()), bold, italic));
            }
            String url = matcher.group(1);
            Hyperlink link = new Hyperlink(url);
            link.getStyleClass().add("md-link");
            link.setOnAction(e -> openUrl(url));
            nodes.add(link);
            lastEnd = matcher.end();
        }

        if (lastEnd < text.length()) {
            nodes.add(createStyledText(text.substring(lastEnd), bold, italic));
        }
    }

    private static Text createStyledText(String content, boolean bold, boolean italic) {
        Text text = new Text(content);
        text.getStyleClass().add("assistant-message-text");
        if (bold) text.getStyleClass().add("md-bold");
        if (italic) text.getStyleClass().add("md-italic");
        return text;
    }

    private static void openUrl(String url) {
        BrowserUtil.open(url);
    }
}
