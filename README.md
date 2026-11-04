PAPERPILOT: CONTROLLABLE AI RAG ASSISTANT

Problem Identified:
Researchers commonly need to compare papers, validate claims, identify gaps, and inspect evidence across documents. Existing chat models:

- Forget uploaded-document context.
- Mix evidence without clear paper boundaries.
- Produce convincing answers without source attribution.
- Do not expose the documents or chunks supporting conclusions.
- Require users to formulate their own paper-search process.

  
Project Framing:
Researchers waste time manually searching, comparing, and synthesizing academic papers while existing AI tools provide unauthenticated answers that cannot be traced back to specific documents. PaperPilot is a source-grounded research assistant that isolates document collections per chat, retrieves relevant evidence from Chroma embeddings, and generates controllable outputs such as comparisons, literature syntheses, gap analyses, methodology audits, and evidence tables.
