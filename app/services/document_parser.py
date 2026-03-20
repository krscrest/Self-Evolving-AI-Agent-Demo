import os
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.identity import DefaultAzureCredential
from app.config import settings


def parse_document(file_bytes: bytes) -> str:
    """Parse a PDF document using Azure Document Intelligence and return extracted text."""
    client = DocumentAnalysisClient(
        endpoint=settings.AZURE_DOC_INTELLIGENCE_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    poller = client.begin_analyze_document("prebuilt-layout", file_bytes)
    result = poller.result()

    extracted_text = []
    for page in result.pages:
        page_lines = []
        for line in page.lines:
            page_lines.append(line.content)
        extracted_text.append("\n".join(page_lines))

    # Also extract tables if present
    for table in result.tables:
        table_text = []
        rows = {}
        for cell in table.cells:
            row_idx = cell.row_index
            if row_idx not in rows:
                rows[row_idx] = {}
            rows[row_idx][cell.column_index] = cell.content
        for row_idx in sorted(rows.keys()):
            row = rows[row_idx]
            row_text = " | ".join(row.get(col, "") for col in sorted(row.keys()))
            table_text.append(row_text)
        extracted_text.append("\n[TABLE]\n" + "\n".join(table_text) + "\n[/TABLE]")

    return "\n\n".join(extracted_text)


def parse_document_from_path(file_path: str) -> str:
    """Parse a PDF from a file path."""
    with open(file_path, "rb") as f:
        return parse_document(f.read())
