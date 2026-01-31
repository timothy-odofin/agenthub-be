from enum import Enum
from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    UnstructuredFileLoader,
    Docx2txtLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader,
    UnstructuredImageLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    JSONLoader,
    UnstructuredXMLLoader,
    UnstructuredHTMLLoader,
    UnstructuredEmailLoader,
    UnstructuredRTFLoader

)


class FileType(str, Enum):
    """Supported file types and their MIME types."""
    PDF = 'application/pdf'
    DOC = 'application/msword'
    DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    XLS = 'application/vnd.ms-excel'
    XLSX = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    PPT = 'application/vnd.ms-powerpoint'
    PPTX = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    TXT = 'text/plain'
    CSV = 'text/csv'
    JPEG = 'image/jpeg'
    PNG = 'image/png'
    TIFF = 'image/tiff'
    JSON = 'application/json'
    YAML = 'application/x-yaml'
    YML = 'application/x-yaml'
    MARKDOWN = 'text/markdown'
    MD = 'text/markdown'
    XML = 'application/xml'
    XML_ALT = 'text/xml'  # Alternative MIME type for XML
    HTML = 'text/html'
    HTM = 'text/html'
    CSS = 'text/css'
    JS = 'application/javascript'
    RTF = 'application/rtf'
    EML = 'message/rfc822'
    MSG = 'application/vnd.ms-outlook'
    ZIP = 'application/zip'
    RAR = 'application/x-rar-compressed'
    TAR = 'application/x-tar'
    GZIP = 'application/gzip'


def _construct_mapping():
    return {
        FileType.PDF: (UnstructuredPDFLoader, {
            "strategy": "hi-res",
            "mode": "elements"
        }),
        FileType.DOC: (UnstructuredFileLoader, {
            "mode": "elements",
            "strategy": "fast",
            "ocr_enabled": True,
            "preserve_formatting": True
        }),
        FileType.DOCX: (Docx2txtLoader, {
        }),
        FileType.XLS: (UnstructuredExcelLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True,
            "include_header": True,
            "include_formulas": True
        }),
        FileType.XLSX: (UnstructuredExcelLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True,
            "include_header": True,
            "include_formulas": True
        }),
        FileType.PPT: (UnstructuredPowerPointLoader, {
            "mode": "elements",
            "strategy": "fast",
            "ocr_enabled": True,
            "preserve_formatting": True
        }),
        FileType.PPTX: (UnstructuredPowerPointLoader, {
            "mode": "elements",
            "strategy": "fast",
            "ocr_enabled": True,
            "preserve_formatting": True
        }),
        FileType.JPEG: (UnstructuredImageLoader, {"mode": "elements", "strategy": "fast"}),
        FileType.PNG: (UnstructuredImageLoader, {"mode": "elements", "strategy": "fast"}),
        FileType.TIFF: (UnstructuredImageLoader, {"mode": "elements", "strategy": "fast"}),
        FileType.TXT: (TextLoader, {}),
        FileType.CSV: (TextLoader, {}),
        FileType.JSON: (JSONLoader, {
            "jq_schema": ".",  # Extract all content
            "text_content": False,  # Preserve JSON structure
            "metadata_func": lambda metadata: {"source_type": "json"}
        }),
        FileType.YAML: (TextLoader, {}),
        FileType.YML: (TextLoader, {}),
        FileType.MARKDOWN: (UnstructuredMarkdownLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True
        }),
        FileType.MD: (UnstructuredMarkdownLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True
        }),
        FileType.XML: (UnstructuredXMLLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True,
            "include_metadata": True,
            "include_tags": True
        }),
        FileType.XML_ALT: (UnstructuredXMLLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True,
            "include_metadata": True,
            "include_tags": True
        }),
        # HTML and Web Files
        FileType.HTML: (UnstructuredHTMLLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True,
            "include_links": True
        }),
        FileType.HTM: (UnstructuredHTMLLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True,
            "include_links": True
        }),
        FileType.CSS: (TextLoader, {}),
        FileType.JS: (TextLoader, {}),

        # Rich Text Format
        FileType.RTF: (UnstructuredRTFLoader, {
            "mode": "elements",
            "strategy": "fast",
            "preserve_formatting": True
        }),

        # Email Files
        FileType.EML: (UnstructuredEmailLoader, {
            "mode": "elements",
            "strategy": "fast",
            "include_headers": True,
            "include_attachments": True
        }),
        FileType.MSG: (UnstructuredEmailLoader, {
            "mode": "elements",
            "strategy": "fast",
            "include_headers": True,
            "include_attachments": True
        }),

        # Archive Files - These will need special handling in _load_document
        FileType.ZIP: (TextLoader, {}),
        FileType.RAR: (TextLoader, {}),
        FileType.TAR: (TextLoader, {}),
        FileType.GZIP: (TextLoader, {}),
    }
