import io
import json
import uuid
from pathlib import Path

import pyperclip
import streamlit as st
from src.assistant.graph import researcher
from src.assistant.utils import get_report_structures, process_uploaded_files
from src.assistant.vector_db import delete_collection, delete_document, get_collection_document_count
from src.assistant.configuration import DEFAULT_REPORT_STRUCTURE
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

MAX_RESEARCH_QUERIES = 4


def create_answer_pdf(title, answer, sources):
    """Create a downloadable PDF without writing a temporary report file."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [Paragraph(title.replace("&", "&amp;"), styles["Title"]), Spacer(1, 12)]

    for paragraph in answer.split("\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.replace("&", "&amp;"), styles["BodyText"]))
            story.append(Spacer(1, 4))

    if sources:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Sources", styles["Heading2"]))
        for source in sources:
            label = f"{source['source']} - {source['location']}"
            story.append(Paragraph(label.replace("&", "&amp;"), styles["BodyText"]))

    document.build(story)
    return buffer.getvalue()

def generate_response(user_input, enable_web_search, report_structure, max_search_queries, collection_id, chat_history=None):
    """
    Generate response using the researcher agent and stream steps
    """
    # Initialize state for the researcher
    history = "\n".join(
        f"{message['role'].title()}: {message['content']}"
        for message in (chat_history or [])[-8:]
    )
    instruction = (
        f"Recent conversation context:\n{history}\n\nCurrent request:\n{user_input}"
        if history else user_input
    )
    initial_state = {
        "user_instructions": instruction,
    }
    
    # Langgraph researcher config
    config = {"configurable": {
        "enable_web_search": enable_web_search,
        "report_structure": report_structure,
        "max_search_queries": max_search_queries,
        "collection_id": collection_id,
    }}

    # Create the status for the global "Researcher" process
    langgraph_status = st.status("**Researcher Running...**", state="running")

    # Force order of expanders by creating them before iteration
    with langgraph_status:
        generate_queries_expander = st.expander("Generate Research Queries", expanded=False)
        search_queries_expander = st.expander("Search Queries", expanded=True)
        final_answer_expander = st.expander("Generate Final Answer", expanded=False)

        steps = []
        sources = []

        try:
            # Run the researcher graph and stream outputs
            for output in researcher.stream(initial_state, config=config):
                for key, value in output.items():
                    expander_label = key.replace("_", " ").title()

                    if key == "generate_research_queries":
                        with generate_queries_expander:
                            st.write(value)
                    elif key.startswith("search_and_summarize_query"):
                        with search_queries_expander:
                            with st.expander(expander_label, expanded=False):
                                st.write(value)
                    elif key == "generate_final_answer":
                        with final_answer_expander:
                            st.write(value)

                    if key.startswith("search_and_summarize_query") and isinstance(value, dict):
                        for document in value.get("retrieved_documents", []):
                            metadata = getattr(document, "metadata", {}) or {}
                            page = metadata.get("page") or metadata.get("page_number")
                            location = f"page {int(page) + 1}" if str(page).isdigit() else "location unavailable"
                            sources.append({
                                "source": metadata.get("source", "Unknown source"),
                                "location": location,
                                "content": getattr(document, "page_content", ""),
                            })

                    steps.append({"step": key, "content": value})
        except Exception as exc:
            langgraph_status.update(
                state="complete",
                label="Research could not be completed"
            )
            return {"final_answer": f"Unable to complete the research request: {exc}", "sources": []}

    # Update status to complete
    langgraph_status.update(state="complete", label="**Using Langgraph** (Research completed)")

    # Return the final report
    answer = steps[-1]["content"] if steps else "No response generated"
    unique_sources = []
    seen_sources = set()
    for source in sources:
        key = (source["source"], source["location"], source["content"][:160])
        if key not in seen_sources:
            seen_sources.add(key)
            unique_sources.append(source)
    if isinstance(answer, dict) and "final_answer" in answer:
        final_answer = answer["final_answer"]
    elif isinstance(answer, dict):
        final_answer = str(answer)
    else:
        final_answer = str(answer)
    return {"final_answer": final_answer, "sources": unique_sources}

CHAT_STORE = Path(".paperpilot") / "chats.json"


def load_chats():
    if CHAT_STORE.exists():
        try:
            data = json.loads(CHAT_STORE.read_text(encoding="utf-8"))
            if data:
                chats = []
                for chat in data.get("chats", []):
                    has_activity = bool(chat.get("messages") or chat.get("documents"))
                    is_placeholder = chat.get("title") in (None, "", "New research chat", "Untitled chat")
                    if not has_activity and is_placeholder:
                        continue
                    if is_placeholder and chat.get("documents"):
                        chat["title"] = ", ".join(
                            Path(document).stem for document in chat["documents"][:3]
                        )
                    chats.append(chat)
                data["chats"] = chats
                if data.get("active_chat_id") not in {chat["id"] for chat in chats}:
                    data["active_chat_id"] = chats[0]["id"] if chats else None
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return None


def save_chats(chats, active_chat_id):
    CHAT_STORE.parent.mkdir(parents=True, exist_ok=True)
    CHAT_STORE.write_text(json.dumps({"active_chat_id": active_chat_id, "chats": chats}, ensure_ascii=False, indent=2), encoding="utf-8")


def create_chat(title="Untitled chat"):
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "collection_id": str(uuid.uuid4()),
        "messages": [],
        "documents": [],
        "processed_signature": "",
        "enable_web_search": False,
        "max_search_queries": 5,
        "selected_report": "StandardReport",
    }


def clear_chat(chat):
    chat["messages"] = []


def main():
    st.set_page_config(page_title="PaperPilot", layout="wide")

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: #0d1117; }
    [data-testid="stSidebar"] { background: #111827; border-right: 1px solid #263244; }
    [data-testid="stChatMessage"] { border: 1px solid #263244; border-radius: 8px; background: #111827; margin-bottom: 8px; }
    div.stButton > button { border-radius: 7px; }
    .brand { font-size: 20px; font-weight: 700; margin-bottom: 2px; }
    .subtle { color: #9ca3af; font-size: 13px; }
    .document-row { border: 1px solid #263244; border-radius: 7px; padding: 8px 10px; margin: 5px 0; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

    if "chats" not in st.session_state:
        stored = load_chats() or {}
        st.session_state.chats = stored.get("chats", [])
        if st.session_state.chats:
            st.session_state.active_chat_id = stored.get("active_chat_id") or st.session_state.chats[0]["id"]
        else:
            draft_chat = create_chat()
            st.session_state.chats = [draft_chat]
            st.session_state.active_chat_id = draft_chat["id"]
        if stored:
            save_chats(st.session_state.chats, st.session_state.active_chat_id)

    chats = st.session_state.chats
    active_chat = next((chat for chat in chats if chat["id"] == st.session_state.active_chat_id), chats[0])
    st.session_state.active_chat_id = active_chat["id"]

    with st.sidebar:
        st.markdown('<div class="brand">PaperPilot</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtle">Research workspace</div>', unsafe_allow_html=True)

        if st.button("+ New research chat", use_container_width=True, type="primary"):
            chat = create_chat()
            chats.insert(0, chat)
            st.session_state.active_chat_id = chat["id"]
            save_chats(chats, chat["id"])
            st.rerun()

        st.markdown("### Chats")
        visible_chats = [
            chat for chat in chats
            if chat.get("messages") or chat.get("documents") or chat.get("title") not in ("Untitled chat", "New research chat")
        ]
        if visible_chats:
            for chat in visible_chats:
                if st.button(chat["title"], key=f"chat_{chat['id']}", use_container_width=True):
                    st.session_state.active_chat_id = chat["id"]
                    save_chats(chats, chat["id"])
                    st.rerun()
        else:
            st.caption("No saved chat history")

        st.divider()
        st.markdown("### Research settings")

        report_structures = get_report_structures()
        if not report_structures:
            report_structures = {"StandardReport": {"content": DEFAULT_REPORT_STRUCTURE}}

        report_structures.setdefault("ComparisonTable", {
            "content": """
# Comparison Overview
- State the filenames being compared and the question being answered.

# Comparison Table
Create a Markdown table with one row for each comparable dimension and two source columns: one for each paper filename.
Use dimensions such as objective, methodology, dataset, key findings, limitations, and conclusion.
For unsupported values, write: Not provided in the indexed documents.

# Differences and Similarities
- Cite each filename.

# Bottom-Line Conclusion
- Summarize only what the indexed evidence supports.
"""
        })

        report_names = list(report_structures.keys())
        current_report = active_chat.get("selected_report", report_names[0])
        report_descriptions = {
            "StandardReport": "Balanced overview: introduction, themes, takeaways, and conclusion.",
            "ComparisonTable": "Side-by-side evidence matrix for papers with shared dimensions.",
            "LiteratureSynthesis": "Cross-paper themes, agreements, disagreements, and evidence strength.",
            "GapAnalysis": "Coverage gaps, research opportunities, and unresolved questions.",
            "MethodologyAudit": "Design, data, validity, reproducibility, strengths, and risks.",
            "EvidenceTable": "Claim-level table with source support, confidence, and missing context.",
            "ExecutiveBrief": "Short decision-oriented summary with risks and next actions.",
        }
        selected_report = st.selectbox(
            "Answer format",
            options=report_names,
            index=report_names.index(current_report) if current_report in report_names else 0,
            help="Choose how evidence is organized in the final answer."
        )
        st.caption(report_descriptions.get(selected_report, "Custom report format loaded from report_structures."))
        active_chat["selected_report"] = selected_report
        st.caption("Retrieval depth is managed automatically to balance coverage and API cost.")
        active_chat["enable_web_search"] = st.checkbox(
            "Enable web search", value=bool(active_chat.get("enable_web_search", False))
        )

        st.markdown("### Paper documents")
        uploaded_files = st.file_uploader(
            "Add PDFs or text files", type=["pdf", "txt", "csv", "md"],
            accept_multiple_files=True, key=f"uploader_{active_chat['id']}"
        )
        for document_name in active_chat["documents"]:
            document_column, remove_column = st.columns([4, 1])
            with document_column:
                st.markdown(f'<div class="document-row">{document_name}</div>', unsafe_allow_html=True)
            with remove_column:
                if st.button("Remove", key=f"remove_{active_chat['id']}_{document_name}", use_container_width=True):
                    delete_document(active_chat["collection_id"], document_name)
                    active_chat["documents"] = [name for name in active_chat["documents"] if name != document_name]
                    active_chat["processed_signature"] = "|".join(signature for signature in active_chat["processed_signature"].split("|") if not signature.startswith(document_name + ":")) if active_chat["processed_signature"] else ""
                    save_chats(chats, active_chat["id"])
                    st.rerun()

        if active_chat["documents"] and st.button("Delete collection", use_container_width=True):
            delete_collection(active_chat["collection_id"])
            active_chat["documents"] = []
            active_chat["processed_signature"] = ""
            save_chats(chats, active_chat["id"])
            st.rerun()

        new_files = [file for file in uploaded_files if file.name not in active_chat["documents"]]
        if uploaded_files and not new_files:
            st.caption("These documents are already indexed in this chat.")

        signature = "|".join(sorted(f"{file.name}:{file.size}" for file in new_files)) if new_files else ""
        if new_files and signature != active_chat["processed_signature"]:
            with st.status("Indexing documents automatically...", expanded=False) as status:
                if process_uploaded_files(new_files, active_chat["collection_id"]):
                    active_chat["processed_signature"] = "|".join(sorted(active_chat["processed_signature"].split("|") + signature.split("|"))) if active_chat["processed_signature"] else signature
                    active_chat["documents"] = list(dict.fromkeys(active_chat["documents"] + [file.name for file in new_files]))
                    save_chats(chats, active_chat["id"])
                    status.update(label="Documents indexed successfully", state="complete")
                    st.rerun()
                else:
                    status.update(label="Document indexing failed", state="error")

    st.title("PaperPilot")
    st.caption("Controllable RAG research assistant")

    header_left, header_right = st.columns([7, 1])
    with header_left:
        new_title = st.text_input(
            "Chat title",
            value=active_chat["title"],
            key=f"title_{active_chat['id']}",
            label_visibility="collapsed",
        )
        if new_title.strip() and new_title != active_chat["title"]:
            active_chat["title"] = new_title.strip()
            save_chats(chats, active_chat["id"])
        document_count = len(active_chat["documents"])
        vector_count = get_collection_document_count(active_chat["collection_id"])
        st.caption(f"{document_count} document(s) • {vector_count} indexed chunks" if document_count else "Collection: no documents indexed yet")
    with header_right:
        if st.button("Clear chat", use_container_width=True):
            clear_chat(active_chat)
            save_chats(chats, active_chat["id"])
            st.rerun()
        if st.button("Delete chat", use_container_width=True):
            delete_collection(active_chat["collection_id"])
            chats.remove(active_chat)
            st.session_state.active_chat_id = chats[0]["id"] if chats else None
            if not chats:
                new_chat = create_chat()
                chats.append(new_chat)
                st.session_state.active_chat_id = new_chat["id"]
            save_chats(chats, st.session_state.active_chat_id)
            st.rerun()

    for index, message in enumerate(active_chat["messages"]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                for source in message.get("sources", []):
                    with st.expander(f"Source: {source['source']} — {source['location']}", expanded=False):
                        st.write(source["content"])
                if st.button("Copy", key=f"copy_{active_chat['id']}_{index}"):
                    pyperclip.copy(message["content"])

    if user_input := st.chat_input("Ask about the papers, findings, or evidence..."):
        if active_chat["title"] in ("Untitled chat", "New research chat"):
            active_chat["title"] = user_input.strip()[:48]

        active_chat["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        report_structure = report_structures[active_chat["selected_report"]]["content"]
        assistant_response = generate_response(
            user_input,
            active_chat["enable_web_search"],
            report_structure,
            MAX_RESEARCH_QUERIES,
            active_chat["collection_id"],
            active_chat["messages"][:-1],
        )

        final_answer = assistant_response["final_answer"]
        sources = assistant_response["sources"]
        active_chat["messages"].append({"role": "assistant", "content": final_answer})
        active_chat["messages"][-1]["sources"] = sources
        save_chats(chats, active_chat["id"])

        with st.chat_message("assistant"):
            st.markdown(final_answer)
            with st.expander("Sources used", expanded=False):
                if sources:
                    for source in sources:
                        st.markdown(f"**{source['source']} — {source['location']}**")
                        st.write(source["content"])
                else:
                    st.caption("No indexed document chunks were retrieved.")
            if st.button("Copy", key=f"copy_{active_chat['id']}_latest"):
                pyperclip.copy(final_answer)
            st.download_button("Export Markdown", final_answer, file_name="paperpilot-answer.md", mime="text/markdown", key=f"md_{active_chat['id']}_latest")
            pdf_bytes = create_answer_pdf(active_chat["title"], final_answer, sources)
            st.download_button("Export PDF", pdf_bytes, file_name="paperpilot-answer.pdf", mime="application/pdf", key=f"pdf_{active_chat['id']}_latest")

    chat_markdown = "# " + active_chat["title"] + "\n\n"
    for message in active_chat["messages"]:
        role = "## User" if message["role"] == "user" else "## Assistant"
        chat_markdown += role + "\n\n" + message["content"] + "\n\n"
    st.sidebar.download_button("Export chat", chat_markdown, file_name="paperpilot-chat.md", mime="text/markdown", use_container_width=True)

if __name__ == "__main__":
    main()