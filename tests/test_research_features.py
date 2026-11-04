from langchain_core.documents import Document

from src.assistant.utils import format_documents_with_metadata
from src.assistant.vector_db import delete_collection, get_collection_path


def test_document_metadata_includes_source_and_human_page(tmp_path, monkeypatch):
    documents = [Document(page_content="Evidence text", metadata={"source": "paper.pdf", "page": 2})]

    formatted = format_documents_with_metadata(documents)

    assert "Source: paper.pdf, page 3" in formatted
    assert "Evidence text" in formatted


def test_delete_collection_only_removes_requested_collection(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import src.assistant.vector_db as vector_db

    requested = vector_db.get_collection_path("chat-one")
    other = vector_db.get_collection_path("chat-two")
    vector_db.os.makedirs(requested, exist_ok=True)
    vector_db.os.makedirs(other, exist_ok=True)

    vector_db.delete_collection("chat-one")

    assert not vector_db.os.path.exists(requested)
    assert vector_db.os.path.exists(other)


def test_answer_pdf_starts_with_pdf_signature():
    from app import create_answer_pdf

    pdf_bytes = create_answer_pdf("Comparison", "Evidence-based answer", [{"source": "paper.pdf", "location": "page 2", "content": "Evidence"}])

    assert pdf_bytes.startswith(b"%PDF")


def test_builtin_report_presets_are_loaded(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from src.assistant.utils import get_report_structures

    presets = tmp_path / "report_structures"
    presets.mkdir()
    (presets / "ComparisonTable.md").write_text("# Comparison\n", encoding="utf-8")
    (presets / "GapAnalysis.txt").write_text("# Gaps\n", encoding="utf-8")

    structures = get_report_structures(str(presets))

    assert structures["ComparisonTable"]["content"] == "# Comparison\n"
    assert structures["GapAnalysis"]["content"] == "# Gaps\n"
