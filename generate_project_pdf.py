from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT = Path("artifacts/PaperPilot_Project_Guide.pdf")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="CoverTitle", parent=styles["Title"], fontSize=30, leading=36, alignment=TA_CENTER, textColor=colors.HexColor("#18243A"), spaceAfter=18))
styles.add(ParagraphStyle(name="CoverSub", parent=styles["Normal"], fontSize=13, leading=19, alignment=TA_CENTER, textColor=colors.HexColor("#526173")))
styles.add(ParagraphStyle(name="H1Custom", parent=styles["Heading1"], fontSize=20, leading=24, textColor=colors.HexColor("#18243A"), spaceBefore=6, spaceAfter=10))
styles.add(ParagraphStyle(name="H2Custom", parent=styles["Heading2"], fontSize=14, leading=18, textColor=colors.HexColor("#355070"), spaceBefore=8, spaceAfter=6))
styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], fontSize=9.5, leading=14, textColor=colors.HexColor("#2B3442"), spaceAfter=5))
styles.add(ParagraphStyle(name="BulletCustom", parent=styles["BodyText"], fontSize=9.5, leading=14, leftIndent=16, firstLineIndent=-10, bulletIndent=4, spaceAfter=3))
styles.add(ParagraphStyle(name="CodeCustom", parent=styles["Code"], fontSize=7.8, leading=11, leftIndent=10, rightIndent=10, borderPadding=7, backColor=colors.HexColor("#EEF2F7"), textColor=colors.HexColor("#253247"), spaceBefore=4, spaceAfter=8))


def P(text, style="BodyCustom"):
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), styles[style])


def bullets(items):
    return [Paragraph("- " + escape(item), styles["BulletCustom"])[0:0] if False else Paragraph("- " + escape(item), styles["BulletCustom"])
            for item in items]


def section(story, title, paragraphs=None, items=None, code=None, table_data=None):
    story.append(Paragraph(escape(title), styles["H1Custom"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#D9E1EA"), spaceAfter=10))
    for paragraph in paragraphs or []:
        story.append(P(paragraph))
    for item in items or []:
        story.append(Paragraph("- " + escape(item), styles["BulletCustom"]))
    if code:
        story.append(Paragraph(escape(code).replace("\n", "<br/>"), styles["CodeCustom"]))
    if table_data:
        table = Table([[Paragraph(escape(str(cell)), styles["BodyCustom"])
                        for cell in row] for row in table_data], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#355070")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#C7D1DD")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F7FA")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setStrokeColor(colors.HexColor("#D9E1EA"))
    canvas.line(doc.leftMargin, height - 34, width - doc.rightMargin, height - 34)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#718096"))
    canvas.drawString(doc.leftMargin, height - 25, "PaperPilot - Project Guide")
    canvas.drawRightString(width - doc.rightMargin, 22, str(doc.page))
    canvas.restoreState()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    doc = BaseDocTemplate(str(OUTPUT), pagesize=A4, leftMargin=48, rightMargin=48,
                          topMargin=52, bottomMargin=42, title="PaperPilot Project Guide",
                          author="PaperPilot")
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=header_footer))

    story = []
    story.append(Spacer(1, 1.25 * inch))
    story.append(P("PAPERPILOT", "CoverSub"))
    story.append(Spacer(1, 0.25 * inch))
    story.append(P("PaperPilot", "CoverTitle"))
    story.append(P("A file-by-file beginner guide", "CoverTitle"))
    story.append(Spacer(1, 0.15 * inch))
    story.append(P("Source-grounded academic research with retrieval-augmented generation, isolated paper collections, and controllable report formats.", "CoverSub"))
    story.append(Spacer(1, 0.5 * inch))
    story.append(HRFlowable(width="45%", thickness=2, color=colors.HexColor("#355070"), hAlign="CENTER"))
    story.append(Spacer(1, 0.35 * inch))
    story.append(P("Architecture guide, setup guide, file explanations, research workflow, problem framing, limitations, and portfolio presentation", "CoverSub"))
    story.append(PageBreak())

    section(story, "1. Project Summary", paragraphs=[
        "PaperPilot is a web application that lets a user upload academic documents and ask evidence-focused questions about them. It combines retrieval, language-model reasoning, chat context, optional web search, and report formatting.",
        "The central idea is Retrieval-Augmented Generation, usually called RAG. Instead of asking an LLM to answer only from memory, PaperPilot first searches relevant text from uploaded documents, sends that text to the LLM with the user's question, and asks the LLM to produce an answer from the retrieved evidence.",
        "Each research chat is separate. Its documents belong to one vector collection, so questions in one paper workspace do not automatically retrieve chunks from another workspace."
    ])

    section(story, "2. The Problem It Addresses", items=[
        "General chatbots may answer with confident claims that are not supported by the user's documents.",
        "Standard chat interfaces do not reliably preserve an uploaded paper collection across follow-up questions.",
        "Comparing two or more papers normally requires repeated manual searches through PDFs.",
        "Researchers must separate useful findings, methods, limitations, citations, agreements, disagreements, and research gaps.",
        "An answer is difficult to verify if there is no trace back to the source document or PDF page.",
        "Research workflows need different outputs: overview, comparison, literature synthesis, evidence table, methodology audit, or executive summary."
    ])

    section(story, "3. Recommended Problem Statement", paragraphs=[
        "Problem: Researchers spend substantial time manually locating evidence, comparing findings across academic papers, and checking whether an answer is supported by the source text. Existing conversational AI can synthesize information, but often loses document boundaries and exposes no reliable source trail, increasing the risk of unsupported conclusions.",
        "Solution: PaperPilot is a source-aware research assistant that automatically indexes uploaded papers into separate Chroma collections, retrieves relevant evidence for each question, preserves chat context, and generates structured outputs with source filename and page information."
    ])

    section(story, "4. How the Application Works", items=[
        "The user creates or opens a research chat.",
        "The user uploads PDF, TXT, CSV, or Markdown documents.",
        "The app loads the documents, splits their text into chunks, creates embeddings, and stores the chunks in a per-chat Chroma database.",
        "The user asks a question and selects an answer format.",
        "LangGraph generates research queries and searches the relevant vector collection.",
        "A relevance evaluator decides whether retrieved document evidence is useful.",
        "If evidence is not relevant and web search is enabled, Tavily supplies web results.",
        "A summarizer converts evidence into a focused summary.",
        "The final-answer prompt combines the user request, report structure, conversation context, and retrieved evidence.",
        "The interface displays the answer and the source chunks used for it.",
        "The user may export the answer as Markdown or PDF and reuse the same indexed collection in later questions."
    ])

    section(story, "5. Simple End-to-End Example", paragraphs=[
        "User uploads alert.pdf and ELECTS.pdf into one research chat.",
        "The app creates embeddings for all text chunks and stores them under database/<unique-chat-id>/.",
        "User asks: Compare both papers and create a table.",
        "The graph may generate smaller queries for objectives, methodology, findings, limitations, and conclusions.",
        "Each query retrieves relevant chunks from the same collection.",
        "The evaluator checks whether the chunks answer the query.",
        "Summaries are sent to the final model with a ComparisonTable report format.",
        "The final model creates a comparison and the UI shows source chunks used by the process."
    ])

    story.append(PageBreak())
    section(story, "6. Root Files", table_data=[
        ["File or folder", "Simple purpose", "Important notes"],
        ["app.py", "Main Streamlit interface and application entry point.", "Displays sidebar, chat history, report formats, uploads, sources, and exports."],
        ["README.md", "Installation and usage documentation for cloning the project.", "Contains setup, API configuration, run commands, and limitations."],
        ["requirements.txt", "Lists Python packages needed by the app.", "Includes Streamlit, LangGraph, Hugging Face, Chroma, PDF, web search, testing, and export dependencies."],
        [".env.example", "Example environment-variable names without real secrets.", "Copy it to .env and add personal API keys locally."],
        [".env", "Local secret configuration.", "Ignored by Git. Never commit API keys or rotate public secrets immediately."],
        [".gitignore", "Tells Git which local files should not be committed.", "Ignores secrets, virtual environments, databases, caches, and chat storage."],
        ["langgraph.json", "Configuration for the LangGraph runtime/server.", "Points to the compiled researcher graph and local environment."],
        ["run_researcher.py", "Command-line or script entry for running the researcher graph.", "Useful for testing without the Streamlit interface."],
        ["generate_project_pdf.py", "Generates this documentation PDF.", "Creates artifacts/PaperPilot_Project_Guide.pdf."],
        ["tests/", "Automated focused tests.", "Tests metadata formatting, collection isolation, PDF output, and report presets."],
    ])

    section(story, "7. app.py Explained", items=[
        "Loads environment variables from .env.",
        "Creates and runs the Streamlit interface.",
        "Defines MAX_RESEARCH_QUERIES = 4 as an internal retrieval budget.",
        "generate_response() prepares recent chat context, calls researcher.stream(), collects research steps, retrieves source chunks, and returns the final answer.",
        "load_chats() reads saved local chat data and removes empty placeholder chats.",
        "save_chats() writes chat metadata and messages to .paperpilot/chats.json.",
        "create_chat() creates a UUID-based chat and document collection identifier.",
        "clear_chat() clears only messages for the active chat; it does not automatically delete indexed documents.",
        "main() renders the sidebar, selected chat, answer format, uploads, document controls, exports, and chat messages.",
        "Uploaded files are indexed automatically when selected and not already present in the active collection.",
        "The Sources Used area displays source filename, approximate PDF page, and retrieved chunk text.",
        "Markdown and PDF exports are generated on demand."
    ])

    story.append(PageBreak())
    section(story, "8. src/assistant Folder", table_data=[
        ["File", "Simple purpose", "Key responsibility"],
        ["configuration.py", "Defines configurable settings.", "Contains the default report structure and LangGraph runnable configuration fields."],
        ["graph.py", "Main LangGraph research workflow.", "Generates queries, retrieves documents, evaluates relevance, searches the web, summarizes evidence, and writes the final answer."],
        ["prompts.py", "Stores all model instructions.", "Controls query writing, document relevance, summarization, and final report formatting."],
        ["state.py", "Defines the typed graph state.", "Describes user instructions, research queries, retrieved documents, summaries, positions, and final output."],
        ["utils.py", "Shared helper functions.", "Calls the LLM, parses output, loads report presets, searches Tavily, formats citations, and processes uploads."],
        ["vector_db.py", "Manages Chroma storage and embeddings.", "Creates isolated collections, adds chunks, retrieves vectors, and deletes collections or documents."],
    ])

    section(story, "9. configuration.py", paragraphs=[
        "This file defines Configuration as a Python data class. A data class is simply a structured container of settings.",
        "The DEFAULT_REPORT_STRUCTURE gives the standard academic report an introduction, main body, key takeaways, and conclusion.",
        "Configuration.from_runnable_config() reads values from environment variables or LangGraph configurable settings. This allows runtime choices to reach graph nodes."
    ])

    section(story, "10. graph.py - The Research Workflow", items=[
        "generate_research_queries(): turns the user's request into focused search queries.",
        "search_queries(): advances batches of query work; it is mostly responsible for the research batch position.",
        "initiate_query_research(): sends every batch item into a search-and-summarize subgraph.",
        "retrieve_rag_documents(): retrieves six similar chunks from the active chat's Chroma collection.",
        "evaluate_retrieved_documents(): asks an LLM whether the retrieved chunks are relevant.",
        "route_research(): uses document evidence when relevant, optionally uses web search when not relevant, or stops the subsearch without unsupported output.",
        "web_research(): calls Tavily when web search is enabled.",
        "summarize_query_research(): summarizes indexed evidence or web evidence for one research query.",
        "generate_final_answer(): combines all summaries with the user's request and selected report structure.",
        "The graph uses Send to process query batches and StateGraph to define transitions between nodes."
    ])

    story.append(PageBreak())
    section(story, "11. prompts.py", paragraphs=[
        "Prompts are instructions written for language models. They are as important as application code because they determine how the system interprets user intent, evidence, and output formatting.",
        "RESEARCH_QUERY_WRITER_PROMPT asks the model to create no more than the configured number of concise research queries.",
        "RELEVANCE_EVALUATOR_PROMPT asks whether the retrieved paper chunks are relevant to the current query.",
        "SUMMARIZER_PROMPT instructs the model to extract verifiable findings and avoid repetition.",
        "REPORT_WRITER_PROMPT provides the user instruction, report layout, and retrieved information, then asks the model to follow source-grounded instructions and avoid invented claims."
    ])

    section(story, "12. state.py", paragraphs=[
        "This file defines Python TypedDict objects that describe graph state.",
        "A TypedDict gives named fields and lightweight editor/type checking without creating a full class object.",
        "ResearcherState carries the user's instruction, generated queries, summaries, batch position, and final answer.",
        "QuerySearchState carries each generated query, retrieved documents, relevance decision, web results, and search summary.",
        "Input and output types separate the data allowed at graph entry and graph exit."
    ])

    section(story, "13. utils.py", items=[
        "parse_output() removes optional <think> text and returns the final response content.",
        "format_documents_with_metadata() attaches source filenames and human-readable PDF page numbers to document evidence.",
        "invoke_llm() reads OPENROUTER_API_KEY, calls ChatOpenAI through OpenRouter, supports structured output, and retries transient failures three times.",
        "tavily_search() performs optional external web research.",
        "get_report_structures() scans report_structures/*.md and *.txt files and returns them as selectable report presets.",
        "process_uploaded_files() writes each upload temporarily, loads its content using a format-specific loader, adds source metadata, and calls add_documents().",
        "Temporary uploaded content is removed after processing."
    ])

    story.append(PageBreak())
    section(story, "14. vector_db.py", items=[
        "get_collection_path() converts a chat collection UUID into a safe database directory name.",
        "get_or_create_vector_db() creates a Chroma store for a collection or loads an existing collection.",
        "HuggingFaceEmbeddings() creates numeric representations of text used for similarity search.",
        "add_documents() chunks documents, creates embeddings, and inserts them into the collection.",
        "SemanticChunker first creates context-aware chunks; RecursiveCharacterTextSplitter then caps chunk size and overlap.",
        "delete_document() removes vectors from one collection where metadata source matches the filename.",
        "delete_collection() removes the entire collection directory.",
        "get_collection_document_count() counts the persisted vector records, which are useful as indexed chunk counts."
    ])

    section(story, "15. Embeddings Explained Simply", paragraphs=[
        "An embedding is a list of numbers representing the meaning of a piece of text. Two pieces with similar meanings usually have numbers close to each other in vector space.",
        "When a question is asked, the app converts that question into an embedding and searches for document chunks with nearby embeddings.",
        "The original text remains associated with the embedding, so retrieved results can show source filenames, page locations, and content excerpts.",
        "The current Hugging Face model is loaded by HuggingFaceEmbeddings(). It is stored in Hugging Face cache and reused; indexing does not need to download it every question."
    ])

    section(story, "16. Chat and Paper Storage", table_data=[
        ["Path", "What it stores"],
        [".paperpilot/chats.json", "Chat IDs, titles, collection IDs, messages, document names, settings, and processed upload signatures."],
        ["database/<collection-id>/", "Persistent Chroma vector records for one chat/paper collection."],
        ["files/", "Loading workspace created for document processing behavior."],
        ["temp_files/", "Short-lived copies of uploaded files while loaders process them."],
        ["report_structures/*.md or *.txt", "User-selectable answer formats."],
        ["artifacts/", "Generated downloadable documentation or exports."],
    ])

    section(story, "17. Report Structures", table_data=[
        ["Preset", "What it produces", "When to use it"],
        ["StandardReport", "Introduction, themes, takeaways, and conclusion.", "General academic overview."],
        ["ComparisonTable", "Filename-based dimensions and a comparison table.", "Comparing two or more papers."],
        ["LiteratureSynthesis", "Cross-paper themes, agreements, disagreements, and evidence strength.", "Synthesizing multiple sources into themes."],
        ["GapAnalysis", "Coverage gaps, importance, opportunities, and missing evidence.", "Finding research opportunities."],
        ["MethodologyAudit", "Design, data, validity, reproducibility, strengths, risks, and improvements.", "Evaluating whether a study is trustworthy and reproducible."],
        ["EvidenceTable", "Claim inventory with source support, confidence, and missing context.", "Checking individual claims."],
        ["ExecutiveBrief", "Short decision summary, implications, risks, and next actions.", "Presentation or business-oriented summary."],
    ])

    section(story, "18. Report Structure Behavior", paragraphs=[
        "Answer format is not a separate retrieval engine. It controls the queries generated from the request and the structure used for the final answer.",
        "Changing a report format should produce a different organization and research emphasis. It does not replace the indexed documents or create a second vector database.",
        "Preset files are user-editable text. The app loads the file content from report_structures/ and sends it inside REPORT_WRITER_PROMPT.",
        "The ComparisonTable mode is best selected explicitly; a normal chat request may not always cause the model to choose a comparison layout automatically."
    ])

    story.append(PageBreak())
    section(story, "19. API and Key Configuration", table_data=[
        ["Key", "Purpose", "Requirement"],
        ["OPENROUTER_API_KEY", "Allows the app to call an OpenRouter-hosted LLM through ChatOpenAI.", "Required."],
        ["TAVILY_API_KEY", "Allows optional external web research.", "Required only when web search is enabled."],
        ["HF_TOKEN", "Authenticates Hugging Face model downloads.", "Optional read-only token."],
        ["LANGCHAIN_API_KEY", "Optional LangSmith tracing.", "Optional."],
        ["LANGCHAIN_PROJECT", "Names the optional tracing project.", "Optional."],
    ])

    section(story, "20. API Calls Simplified", paragraphs=[
        "One request may generate several internal model calls. Research query generation creates the initial queries.",
        "For each query, document retrieval is local. It does not use an external LLM API.",
        "Relevance evaluation uses an API call.",
        "Evidence summarization uses an API call for every relevant query batch.",
        "The final report uses another API call.",
        "Web-search calls can add Tavily API usage, while document retrieval reuses local embeddings and Chroma storage."
    ])

    section(story, "21. Automatic Indexing", paragraphs=[
        "Automatic indexing means PaperPilot reacts when a new file is placed into the upload control.",
        "It calculates a file signature based on filename and size.",
        "A file already in active_chat['documents'] is not indexed again.",
        "New files are sent to process_uploaded_files(), which loads them and adds their chunks to the collection.",
        "After success, the document names and upload signatures are saved in chat metadata.",
        "Follow-up questions do not re-index existing files; they retrieve from the saved collection."
    ])

    section(story, "22. Document Removal and Chat Deletion", items=[
        "Remove deletes one document by its source metadata and also removes its name from chat metadata.",
        "Delete collection removes all vector records for the active chat.",
        "Clear chat removes message history but keeps document metadata and vector storage.",
        "Delete chat removes the collection and the chat record, then creates another draft chat when necessary.",
        "Removing a document from chat metadata without removing vectors can leave stale retrieval data; delete_document() addresses this by using Chroma metadata filtering."
    ])

    story.append(PageBreak())
    section(story, "23. Source Grounding and Provenance", paragraphs=[
        "Source grounding means claims should be tied to text from indexed documents rather than model memory or invention.",
        "PaperPilot attaches metadata such as source filename, collection ID, and PDF page when loaders provide it.",
        "Retrieved chunks are sent to the summarizer and visible to the user in the Sources Used panel.",
        "The prompt also asks the final writer not to invent titles, authors, results, methodology, or statistics.",
        "Source display improves verification but does not prove every sentence in the answer corresponds exactly to a single source. Stronger claim-level citation would require another extraction or verification step."
    ])

    section(story, "24. What RAG Solves", items=[
        "It gives the model current or private document context that was unavailable during model training.",
        "It narrows model input to the most relevant chunks instead of sending an entire library.",
        "It allows source filenames and pages to be associated with retrieved evidence.",
        "It can reduce unsupported answers, but it does not eliminate hallucination by itself.",
        "Its final quality depends on PDF extraction, chunking, embeddings, query quality, relevance filtering, and the final prompt."
    ])

    section(story, "25. Current Limitations", items=[
        "Chat persistence is local rather than cloud-synchronized.",
        "PDF extraction may miss tables, equations, images, scanned text, or complex layouts.",
        "SemanticChunker may be slow or memory-heavy for large documents.",
        "The UI currently exposes source chunks but not direct clickable PDF page links.",
        "The system retrieves a fixed number of chunks per query instead of adaptive dense coverage.",
        "There is no automatic answer fact-check score yet.",
        "There is no authentication or multi-user account system.",
        "Generated reports should still be checked against the original papers.",
        "Web evidence is separate from document evidence conceptually, but the UI and model prompts should clearly communicate this boundary."
    ])

    section(story, "26. Recommended Portfolio Framing", paragraphs=[
        "Use this as the concise project description: " +
        "PaperPilot is a controllable Retrieval-Augmented Generation platform for evidence-grounded academic research. It indexes uploaded papers into isolated Chroma collections, retrieves and evaluates relevant passages, preserves chat context, and generates structured outputs such as comparisons, gap analyses, methodology audits, literature syntheses, and evidence tables.",
        "Gap statement: Researchers need a source-aware way to compare papers, identify gaps, and verify claims across a private collection. Existing general-purpose chat interfaces do not reliably preserve document boundaries or provide source-transparent workflows.",
        "Solution statement: PaperPilot turns an uploaded paper collection into a controlled research workspace where retrieval, report structure, source inspection, chat history, and export are visible and reusable."
    ])

    section(story, "27. Resume Bullet Ideas", items=[
        "Built PaperPilot, a source-grounded academic RAG application using Streamlit, LangGraph, Hugging Face embeddings, Chroma, OpenRouter, and Tavily.",
        "Implemented per-chat vector collections, automatic document indexing, follow-up context, document removal, collection cleanup, and source provenance.",
        "Designed seven controllable report formats for literature comparison, synthesis, gap analysis, methodology auditing, evidence review, and executive summaries.",
        "Added source chunk inspection, API retry handling, Markdown/PDF exports, persistent chat storage, and focused pytest coverage.",
        "Reduced unsupported claims by requiring source filename and page metadata and including no-fabrication instructions in the report-writing prompt."
    ])

    story.append(PageBreak())
    section(story, "28. Setup Summary", code="""git clone <repository-url>
cd PaperPilot
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
# Add OPENROUTER_API_KEY and optional keys
streamlit run app.py
""")

    section(story, "29. Tests", paragraphs=[
        "The current tests are focused unit checks rather than complete browser or LLM integration tests.",
        "Document metadata formatting verifies source and human-readable page labels.",
        "Collection deletion verifies that one collection is removed while another remains.",
        "PDF export verifies that generated output starts with a valid PDF signature.",
        "Report preset loading verifies that .md and .txt preset files load correctly."
    ])

    section(story, "30. Suggested Future Improvements", items=[
        "Display clickable source links that jump to the PDF page.",
        "Store original uploaded files per chat so document metadata, names, and pages survive restart.",
        "Replace semantic chunking with a measured hybrid chunking strategy for speed and reproducibility.",
        "Add per-source retrieval scores and answer confidence indicators.",
        "Add automated citation verification that checks each answer claim against a source chunk.",
        "Add browser tests for upload, automatic indexing, chat switching, and exports.",
        "Add unit and integration tests that mock external APIs.",
        "Add user authentication and private database accounts.",
        "Add cloud persistence or optional database-backed chat storage.",
        "Migrate deprecated LangGraph StateGraph arguments and Send imports.",
        "Replace langchain-community deprecation surfaces with maintained integrations.",
        "Add license selection and public deployment instructions.",
        "Add an evaluation dataset of research questions with expected evidence and citations."
    ])

    section(story, "31. Final Mental Model", paragraphs=[
        "Think of PaperPilot as five connected layers:",
        "1. Interface: app.py lets a user manage chats, documents, answer formats, and exports.",
        "2. Storage: .paperpilot/chats.json remembers chat metadata; Chroma remembers document vectors.",
        "3. Document processing: utils.py loads files and vector_db.py creates embeddings and chunks.",
        "4. Research workflow: graph.py plans queries, retrieves evidence, evaluates relevance, summarizes, and formats an answer.",
        "5. Model instructions: prompts.py and report presets control research behavior and output structure."
    ])

    doc.build(story)
    return OUTPUT


if __name__ == "__main__":
    print(build())
