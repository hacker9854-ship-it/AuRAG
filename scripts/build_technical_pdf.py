from __future__ import annotations

import os
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "output" / "pdf"
TMP_DIR = ROOT / "tmp" / "pdfs"
FIG_DIR = ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUT_DIR / "aurag-technical-documentation.pdf"


def register_fonts() -> tuple[str, str, str]:
    candidates = [
        (
            "Aptos",
            Path(os.environ.get("WINDIR", "C:/Windows"))
            / "Fonts"
            / "Aptos.ttf",
            Path(os.environ.get("WINDIR", "C:/Windows"))
            / "Fonts"
            / "Aptos-Bold.ttf",
        ),
        (
            "SegoeUI",
            Path(os.environ.get("WINDIR", "C:/Windows"))
            / "Fonts"
            / "segoeui.ttf",
            Path(os.environ.get("WINDIR", "C:/Windows"))
            / "Fonts"
            / "segoeuib.ttf",
        ),
    ]
    for family, regular, bold in candidates:
        if regular.exists() and bold.exists():
            pdfmetrics.registerFont(TTFont(family, str(regular)))
            pdfmetrics.registerFont(TTFont(f"{family}-Bold", str(bold)))
            return family, f"{family}-Bold", "Courier"
    return "Helvetica", "Helvetica-Bold", "Courier"


FONT, FONT_BOLD, MONO = register_fonts()

NAVY = colors.HexColor("#102A43")
INK = colors.HexColor("#243B53")
MUTED = colors.HexColor("#627D98")
TEAL = colors.HexColor("#0F766E")
TEAL_LIGHT = colors.HexColor("#E6FFFA")
BLUE = colors.HexColor("#0B6EAA")
BLUE_LIGHT = colors.HexColor("#E0F2FE")
GREEN = colors.HexColor("#15803D")
GREEN_LIGHT = colors.HexColor("#ECFDF5")
AMBER = colors.HexColor("#C2410C")
AMBER_LIGHT = colors.HexColor("#FFF7ED")
PURPLE = colors.HexColor("#6D28D9")
PURPLE_LIGHT = colors.HexColor("#F5F3FF")
LINE = colors.HexColor("#D9E2EC")
PAPER = colors.HexColor("#F8FAFC")
WHITE = colors.white


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="CoverTitle",
        fontName=FONT_BOLD,
        fontSize=30,
        leading=34,
        textColor=WHITE,
        alignment=TA_LEFT,
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        name="CoverSub",
        fontName=FONT,
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#D9E2EC"),
        alignment=TA_LEFT,
    )
)
styles.add(
    ParagraphStyle(
        name="Eyebrow",
        fontName=FONT_BOLD,
        fontSize=8,
        leading=10,
        textColor=TEAL,
        spaceAfter=6,
        uppercase=True,
    )
)
styles.add(
    ParagraphStyle(
        name="H1Custom",
        parent=styles["Heading1"],
        fontName=FONT_BOLD,
        fontSize=21,
        leading=25,
        textColor=NAVY,
        spaceBefore=7,
        spaceAfter=10,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="H2Custom",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        textColor=INK,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="H3Custom",
        parent=styles["Heading3"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        textColor=TEAL,
        spaceBefore=9,
        spaceAfter=4,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        name="BodyCustom",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=9.1,
        leading=13.4,
        textColor=INK,
        spaceAfter=6,
    )
)
styles.add(
    ParagraphStyle(
        name="SmallCustom",
        parent=styles["BodyText"],
        fontName=FONT,
        fontSize=7.8,
        leading=10.5,
        textColor=MUTED,
        spaceAfter=4,
    )
)
styles.add(
    ParagraphStyle(
        name="TableHead",
        fontName=FONT_BOLD,
        fontSize=7.7,
        leading=9.3,
        textColor=WHITE,
    )
)
styles.add(
    ParagraphStyle(
        name="TableCell",
        fontName=FONT,
        fontSize=7.6,
        leading=10,
        textColor=INK,
    )
)
styles.add(
    ParagraphStyle(
        name="TableCellBold",
        fontName=FONT_BOLD,
        fontSize=7.6,
        leading=10,
        textColor=INK,
    )
)
styles.add(
    ParagraphStyle(
        name="CodeCustom",
        fontName=MONO,
        fontSize=7.3,
        leading=9.2,
        textColor=colors.HexColor("#E6EDF3"),
    )
)
styles.add(
    ParagraphStyle(
        name="CalloutTitle",
        fontName=FONT_BOLD,
        fontSize=9.2,
        leading=12,
        textColor=INK,
        spaceAfter=3,
    )
)
styles.add(
    ParagraphStyle(
        name="CalloutBody",
        fontName=FONT,
        fontSize=8.4,
        leading=11.5,
        textColor=INK,
    )
)
styles.add(
    ParagraphStyle(
        name="TOC",
        fontName=FONT,
        fontSize=10,
        leading=15,
        textColor=INK,
        leftIndent=8,
    )
)
styles.add(
    ParagraphStyle(
        name="TOCNum",
        fontName=FONT_BOLD,
        fontSize=10,
        leading=15,
        textColor=TEAL,
        leftIndent=0,
    )
)


def P(text: str, style: str = "BodyCustom") -> Paragraph:
    return Paragraph(text, styles[style])


def bullet(text: str) -> Paragraph:
    return Paragraph(f"<font color='#0F766E'><b>•</b></font> {text}", styles["BodyCustom"])


def code(text: str) -> Table:
    lines = escape(text).replace("\n", "<br/>")
    table = Table([[Paragraph(lines, styles["CodeCustom"])]], colWidths=[6.55 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#102A43")),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#486581")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    return table


def callout(title: str, body: str, tone: str = "teal") -> Table:
    palette = {
        "teal": (TEAL_LIGHT, TEAL),
        "blue": (BLUE_LIGHT, BLUE),
        "amber": (AMBER_LIGHT, AMBER),
        "purple": (PURPLE_LIGHT, PURPLE),
        "green": (GREEN_LIGHT, GREEN),
    }
    bg, accent = palette[tone]
    inner = Table(
        [[P(title, "CalloutTitle")], [P(body, "CalloutBody")]],
        colWidths=[6.05 * inch],
    )
    inner.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("LINEBEFORE", (0, 0), (0, -1), 4, accent),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return inner


def table(data: list[list[str]], widths: list[float], header: bool = True) -> Table:
    converted = []
    for row_index, row in enumerate(data):
        converted.append(
            [
                P(cell, "TableHead" if header and row_index == 0 else "TableCell")
                for cell in row
            ]
        )
    t = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("LINEBELOW", (0, 0), (-1, 0), 1, TEAL),
        ]
        for row in range(1, len(data)):
            if row % 2 == 0:
                commands.append(("BACKGROUND", (0, row), (-1, row), PAPER))
    t.setStyle(TableStyle(commands))
    return t


class SectionBand(Flowable):
    def __init__(self, label: str, title: str, subtitle: str = ""):
        super().__init__()
        self.label = label
        self.title = title
        self.subtitle = subtitle
        self.width = 6.85 * inch
        self.height = 0.72 * inch

    def draw(self):
        c = self.canv
        c.setFillColor(NAVY)
        c.roundRect(0, 0, self.width, self.height, 7, fill=1, stroke=0)
        c.setFillColor(TEAL)
        c.roundRect(0, 0, 0.11 * inch, self.height, 4, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#B2F5EA"))
        c.setFont(FONT_BOLD, 7.5)
        c.drawString(0.25 * inch, self.height - 0.22 * inch, self.label.upper())
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 17)
        c.drawString(0.25 * inch, 0.23 * inch, self.title)


class Diagram(Flowable):
    def __init__(self, path: Path, caption: str, max_width: float = 6.85 * inch, max_height: float = 6.25 * inch):
        super().__init__()
        from PIL import Image as PILImage
        from PIL import ImageChops

        with PILImage.open(path).convert("RGB") as img:
            background = PILImage.new("RGB", img.size, "white")
            diff = ImageChops.difference(img, background)
            bbox = diff.getbbox()
            if bbox:
                pad = 18
                left = max(0, bbox[0] - pad)
                top = max(0, bbox[1] - pad)
                right = min(img.width, bbox[2] + pad)
                bottom = min(img.height, bbox[3] + pad)
                cropped = img.crop((left, top, right, bottom))
            else:
                cropped = img.copy()
            cropped_path = TMP_DIR / f"{path.stem}-cropped.png"
            cropped.save(cropped_path)

        self.path = cropped_path
        self.caption = caption
        self.max_width = max_width
        self.max_height = max_height

        with PILImage.open(self.path) as img:
            width, height = img.size
        scale = min(max_width / width, max_height / height)
        self.width = width * scale
        self.height = height * scale + 0.38 * inch
        self._image_width = width * scale
        self._image_height = height * scale

    def draw(self):
        self.canv.drawImage(
            str(self.path),
            (self.max_width - self._image_width) / 2,
            0.24 * inch,
            width=self._image_width,
            height=self._image_height,
            preserveAspectRatio=True,
            mask="auto",
        )
        self.canv.setFont(FONT, 7.5)
        self.canv.setFillColor(MUTED)
        self.canv.drawCentredString(self.max_width / 2, 0.07 * inch, self.caption)


def cover_page(story: list):
    story.append(Spacer(1, 0.15 * inch))
    hero = Table(
        [
            [P("TECHNICAL DOCUMENTATION", "Eyebrow")],
            [P("AuRAG", "CoverTitle")],
            [P("Industrial Knowledge Intelligence and Unified Operations Agent", "CoverSub")],
        ],
        colWidths=[6.35 * inch],
    )
    hero.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("LINEBEFORE", (0, 0), (0, -1), 6, TEAL),
                ("LEFTPADDING", (0, 0), (-1, -1), 18),
                ("RIGHTPADDING", (0, 0), (-1, -1), 18),
                ("TOPPADDING", (0, 0), (-1, 0), 14),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 16),
            ]
        )
    )
    story.append(hero)
    story.append(Spacer(1, 0.32 * inch))
    story.append(
        callout(
            "Document purpose",
            "A detailed engineering reference for the current repository implementation: architecture, data flow, retrieval, agent behavior, APIs, operator workflows, deployment, testing, and known boundaries.",
            "blue",
        )
    )
    story.append(Spacer(1, 0.28 * inch))
    story.append(
        Table(
            [
                [P("Repository snapshot", "SmallCustom"), P("September 27, 2026", "TableCellBold")],
                [P("Primary audience", "SmallCustom"), P("Engineers, architects, operators, reviewers", "TableCellBold")],
                [P("Runtime shape", "SmallCustom"), P("Next.js + FastAPI + Neo4j + Qdrant + Redis", "TableCellBold")],
                [P("Document status", "SmallCustom"), P("Implementation-aligned reference", "TableCellBold")],
            ],
            colWidths=[1.55 * inch, 4.8 * inch],
        )
    )
    story.append(Spacer(1, 0.75 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=TEAL))
    story.append(Spacer(1, 0.12 * inch))
    story.append(P("Prepared from source code, configuration, tests, deployment notes, and project documentation.", "SmallCustom"))
    story.append(PageBreak())


def toc(story: list):
    story.append(SectionBand("Navigation", "Contents", "How this document is organized"))
    story.append(Spacer(1, 0.2 * inch))
    entries = [
        ("01", "Executive Summary", "What AuRAG does and where its value comes from"),
        ("02", "System Architecture", "Runtime topology and architectural boundaries"),
        ("03", "Ingestion and Knowledge Graph", "How plant documents become linked evidence"),
        ("04", "Retrieval and Agent Orchestration", "Hybrid retrieval, routing, and grounded answers"),
        ("05", "Operator Experience", "Frontend workspaces and action loops"),
        ("06", "API and Domain Contracts", "Endpoints, payloads, and state transitions"),
        ("07", "Evaluation and Observability", "RAGAS, durable records, health, and events"),
        ("08", "Deployment and Operations", "Local stack, managed services, and release checks"),
        ("09", "Security, Reliability, and Data Governance", "Failure modes and trust boundaries"),
        ("10", "Testing and Validation", "Automated coverage and recorded evidence"),
        ("11", "Limitations and Roadmap", "Current scope boundaries and next closure items"),
        ("12", "Appendix", "Repository map, configuration, and endpoint index"),
    ]
    for number, title, subtitle in entries:
        story.append(
            Table(
                [[P(number, "TOCNum"), P(f"<b>{title}</b><br/><font color='#627D98'>{subtitle}</font>", "TOC")]],
                colWidths=[0.45 * inch, 6.1 * inch],
                style=TableStyle(
                    [
                        ("LINEBELOW", (0, 0), (-1, -1), 0.35, LINE),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                ),
            )
        )
    story.append(PageBreak())


def section(story: list, number: str, title: str, subtitle: str = ""):
    story.append(SectionBand(number, title, subtitle))
    story.append(Spacer(1, 0.16 * inch))


def build_story() -> list:
    story: list = []
    cover_page(story)
    toc(story)

    section(story, "01", "Executive Summary", "The product thesis, current implementation, and operating model")
    story.append(P("<b>AuRAG</b> is an industrial knowledge intelligence platform that turns fragmented plant records, equipment history, procedures, regulatory clauses, and telemetry signals into a grounded operational workflow. The primary interaction is a single operator console: ask a question, inspect the evidence graph, see the routed specialist, and move from a detected signal to a reviewed work order.", "BodyCustom"))
    story.append(P("The implementation combines a graph-first data model with multiple retrieval strategies. Neo4j stores the operational relationships and is also used for native vector search. Qdrant supplies an independent dense-vector index, BM25 supplies keyword recall, graph traversal supplies entity-aware evidence, and a local cross-encoder reranks the fused candidates.", "BodyCustom"))
    story.append(P("The application is intentionally fail-open at several boundaries. A scoring failure does not remove an answer, a mem0 failure does not block chat, a provider failure is surfaced as a clean API error, and work-order decisions use optimistic version checks to prevent stale edits from silently overwriting operator changes.", "BodyCustom"))
    story.append(Spacer(1, 0.08 * inch))
    story.append(callout("Core product proof", "Natural-language question -> specialist routing -> grounded answer -> citations -> graph evidence -> asynchronous quality score.", "teal"))
    story.append(Spacer(1, 0.15 * inch))
    story.append(table([
        ["Capability", "Current implementation"],
        ["Unified interface", "Next.js operator console with Command Center, Investigation, Predictive Watch, Evaluation, Knowledge Risk, Comparison, and Work Orders views."],
        ["Reasoning", "LangGraph Supervisor routes to Copilot, RCA, Compliance, or Lessons Learned."],
        ["Grounding", "Citation-whitelisted LLM responses with retrieved context and typed graph paths."],
        ["Actionability", "Telemetry warnings create durable predictive events and editable, accept/reject work-order drafts."],
        ["Quality", "Async RAGAS scoring for faithfulness, context precision, and answer relevancy, persisted as EvaluationRun."],
    ], [1.35 * inch, 5.5 * inch]))
    story.append(PageBreak())

    section(story, "02", "System Architecture", "Logical layers and dependency boundaries")
    story.append(P("The system is organized into five runtime planes: user experience, application API, knowledge intelligence, persistence/runtime services, and model providers. The FastAPI layer is an adapter and orchestration boundary; domain behavior remains in agents, retrieval, telemetry, ingestion, evaluation, and service modules.", "BodyCustom"))
    story.append(Diagram(FIG_DIR / "aurag-platform-architecture.png", "Figure 1. Current AuRAG platform architecture."))
    story.append(Spacer(1, 0.1 * inch))
    story.append(P("The browser never connects directly to Neo4j. Graph evidence is requested through <font name='Courier'>POST /api/graph</font>, which resolves answer-specific typed paths server-side. This keeps graph credentials and query construction on the backend and makes the frontend contract stable.", "BodyCustom"))
    story.append(table([
        ["Layer", "Responsibilities", "Key modules"],
        ["Frontend", "Operator navigation, chat, graph canvas, telemetry controls, evaluations, risk, comparison, and work-order review.", "frontend/app, frontend/components"],
        ["API", "Request validation, dependency injection, error flattening, REST and SSE contracts.", "backend/app/api, backend/app/main.py"],
        ["Intelligence", "Intent classification, specialized reasoning, retrieval fusion, telemetry matching, ingestion.", "agents, retrieval, telemetry, ingestion"],
        ["Persistence", "Graph entities, vectors, queue state, memory, evaluations, predictive events, decision audit.", "Neo4j, Qdrant, Redis/RQ, mem0"],
        ["Providers", "Routing/reasoning/judging, OCR/vision, embeddings, reranking.", "Groq, Gemini, sentence-transformers"],
    ], [0.85 * inch, 3.6 * inch, 2.4 * inch]))
    story.append(PageBreak())

    section(story, "03", "Ingestion and Knowledge Graph", "Convergent parsing, entity linking, and durable evidence")
    story.append(P("All ingestion paths converge on <font name='Courier'>ingestion.pipeline.ingest_file()</font>. Clean text is parsed directly, scanned images use Tesseract with a Gemini fallback, and P&ID diagrams use Gemini vision to produce page summaries, equipment mentions, and connection candidates. The pipeline uses closed-world matching: only known equipment and personnel are linked, preventing uncontrolled graph expansion from model hallucinations.", "BodyCustom"))
    story.append(Diagram(FIG_DIR / "aurag-ingestion-pipeline.png", "Figure 2. Ingestion convergence and dual vector indexing."))
    story.append(Spacer(1, 0.08 * inch))
    story.append(P("Document identity is content-hash based. Unchanged files are fast no-ops. Changed documents clear and rebuild their chunks and P&ID relationships, then update the content hash only after Neo4j and Qdrant indexing succeeds. That ordering preserves retryability when vector indexing or a provider call fails.", "BodyCustom"))
    story.append(P("Neo4j is the relationship authority. The current schema includes unique constraints for equipment, documents, chunks, people, work orders, failure events, regulatory clauses, procedures, evaluations, predictive events, notifications, and work-order decisions. A 384-dimensional cosine vector index is created over Chunk embeddings.", "BodyCustom"))
    story.append(Diagram(FIG_DIR / "aurag-knowledge-graph.png", "Figure 3. Persisted knowledge and operational relationship model.", max_height=5.7 * inch))
    story.append(PageBreak())

    section(story, "04", "Retrieval and Agent Orchestration", "From query intent to cited answer")
    story.append(P("The Supervisor is a LangGraph StateGraph. It classifies each query into one of four intents, applies a confidence floor of 0.6, and routes low-confidence or unknown classifications to Copilot as the general fallback. The classifier's raw intent and the agent that actually ran are both retained for debugging and observability.", "BodyCustom"))
    story.append(table([
        ["Route", "Question shape", "Evidence behavior"],
        ["Copilot", "General plant Q&A and document lookup.", "Hybrid GraphRAG: vectors, Qdrant, BM25, graph traversal, filters, and rerank."],
        ["RCA", "Why did a specific asset fail?", "Entity-anchored failure, work-order, procedure, and document traversal."],
        ["Compliance", "Is an asset compliant or what does a clause require?", "Clause-first evidence shaping, gap detection, quotations, and citations."],
        ["Lessons Learned", "What patterns recur across incidents?", "Cross-incident scan and pattern synthesis over failure/work-order history."],
    ], [1.15 * inch, 2.2 * inch, 3.5 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(P("Hybrid retrieval collects up to ten candidates per source, deduplicates by source key, applies explicit equipment/name and year filters, then reranks the remaining passages with the configured local cross-encoder. The answer layer receives a context-key whitelist, and model citations are filtered against that whitelist before they can reach the UI or graph resolver.", "BodyCustom"))
    story.append(Diagram(FIG_DIR / "aurag-query-lifecycle.png", "Figure 4. Query lifecycle from operator question to async score."))
    story.append(Spacer(1, 0.1 * inch))
    story.append(callout("Why the graph matters", "Dense retrieval finds semantically similar passages. Graph traversal adds the relationship path that connects a failure, asset, work order, procedure, person, clause, or predictive event into an inspectable answer trail.", "purple"))
    story.append(PageBreak())

    section(story, "05", "Operator Experience", "A workflow-oriented console for repeated operational use")
    story.append(P("The frontend is a Next.js 16 application with a persistent shell, route-aware titles, readiness polling, responsive workspaces, and typed API wrappers. The UI is structured around operational decisions rather than generic chat alone.", "BodyCustom"))
    story.append(table([
        ["Workspace", "Operator task", "Key behavior"],
        ["Command Center", "Start from a unified plant overview.", "Coverage tiles, workflow entry points, platform readiness, and guided operational prompts."],
        ["Investigation", "Ask, inspect, and validate an answer.", "Chat panel, routed-agent badge, citations, RAGAS pills, graph canvas, and evidence details."],
        ["Predictive Watch", "Move from signal to intervention.", "Equipment selector, drift slider, live scan, warning, durable event, draft work order, edit, accept, or reject."],
        ["Knowledge Risk", "Protect retiring expertise.", "Risk score, asset coverage, uncovered equipment, evidence, and recommended capture/successor actions."],
        ["Comparison", "Make GraphRAG value visible.", "Side-by-side graph answer and dense-only baseline with source overlap and relationship evidence."],
        ["Evaluation", "Review quality over time.", "Summary metrics, trend chart, filters, paginated EvaluationRun history, low-faithfulness queue."],
        ["Work Orders", "Review action state safely.", "Draft/In Review/Approved/Rejected status, versioned edits, decision reasons, and audit history."],
    ], [1.3 * inch, 2.05 * inch, 3.5 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(callout("Operator trust loop", "Every answer exposes what ran, what sources were used, how the answer maps into the graph, and whether asynchronous quality scoring completed. Predictive actions remain reviewable and versioned rather than silently becoming plant work.", "blue"))
    story.append(PageBreak())

    section(story, "06", "API and Domain Contracts", "Typed boundaries between UI, orchestration, and services")
    story.append(P("The FastAPI application mounts routers under <font name='Courier'>/api</font>. Endpoint handlers validate input, call domain services, and translate failures into stable JSON error shapes. The current CORS implementation reads <font name='Courier'>BACKEND_CORS_ORIGINS</font> from the environment.", "BodyCustom"))
    story.append(table([
        ["Surface", "Method", "Purpose"],
        ["/health/live", "GET", "Process liveness; does not require all providers."],
        ["/health/ready", "GET", "Dependency readiness across Neo4j, Qdrant, Redis, Groq, Gemini, and mem0."],
        ["/chat", "POST", "Recall memory, route query, return answer/citations/graph paths, create async score job."],
        ["/chat/scores/{score_id}", "GET", "Poll in-memory or durable EvaluationRun score state."],
        ["/graph", "POST", "Resolve typed answer graph paths into nodes and relationships."],
        ["/telemetry/scan", "POST", "Generate synthetic reading, match failure signature, and return warning."],
        ["/telemetry/draft", "POST", "Create or retrieve a durable predictive work-order draft."],
        ["/events/predictive", "GET", "Server-Sent Events stream with keep-alives and cursor support."],
        ["/notifications", "GET/POST", "List predictive notifications and mark them read."],
        ["/work-orders", "GET/POST/PATCH", "List, create, and edit persisted work-order drafts."],
        ["/work-orders/{id}/decisions", "POST", "Accept or reject with version check and reason for reject."],
        ["/knowledge-risk", "GET", "Rank personnel knowledge-retirement risk and asset coverage."],
        ["/comparison", "POST", "Run GraphRAG versus dense-only retrieval comparison."],
        ["/evaluations", "GET", "Query evaluation history and aggregate summary."],
        ["/ingestion/documents", "POST", "Accept a document upload and enqueue ingestion."],
    ], [1.7 * inch, 0.75 * inch, 4.4 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(P("Work-order edits and decisions use optimistic concurrency. The client sends <font name='Courier'>expected_version</font>; a mismatch produces a conflict rather than an overwrite. Every edit and decision becomes a WorkOrderDecision record with actor, reason, timestamps, and version transition.", "BodyCustom"))
    story.append(code("POST /api/work-orders/{id}/decisions\n{\n  \"decision\": \"reject\",\n  \"expected_version\": 2,\n  \"reason\": \"Field inspection found no actionable anomaly\",\n  \"actor\": \"local-operator\"\n}"))
    story.append(PageBreak())

    section(story, "07", "Evaluation and Observability", "Quality metadata is part of the product contract")
    story.append(P("Chat returns the answer first. When retrieved context exists, the API creates a durable EvaluationRun and starts a daemon-thread scoring job. The frontend polls the score endpoint and updates the answer in place. This keeps operator latency independent from judge-model latency while preserving a quality trail.", "BodyCustom"))
    story.append(table([
        ["Metric", "Meaning", "Product use"],
        ["Faithfulness", "Whether the answer is supported by retrieved context.", "Low-faithfulness warning and review queue."],
        ["Context precision", "Whether retrieved context is useful and focused.", "Retrieval quality signal."],
        ["Answer relevancy", "Whether the response addresses the question.", "Answer usefulness signal."],
        ["Routing confidence", "Classifier confidence before confidence-floor fallback.", "Explains the selected specialist and misroute risk."],
        ["Graph relationship evidence", "Count of answer-specific graph paths.", "Makes relational grounding visible."],
    ], [1.45 * inch, 3.1 * inch, 2.3 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(callout("Fail-open scoring", "If RAGAS dependencies, judge calls, or durable score updates fail, the answer remains available. The UI distinguishes scoring, scored, skipped-no-context, delayed, and error states.", "amber"))
    story.append(P("Predictive operations use two complementary delivery modes. The interactive UI scans synthetic drift and persists a PredictiveEvent when the warning threshold fires. The background TelemetryWorker scans configured equipment on an interval, deduplicates events through a cooldown window, and publishes new notification IDs for the SSE stream.", "BodyCustom"))
    story.append(code("TelemetryWorker.run_cycle(session)\n  drift = scheduled test phase\n  for equipment in configured_tags:\n      reading = generate_reading(...)\n      warning = match_reading(...)\n      if warning:\n          event = create_predictive_event(..., cooldown_seconds=1800)\n          publish_event(event.id)"))
    story.append(PageBreak())

    section(story, "08", "Deployment and Operations", "Local development, container runtime, and managed deployment")
    story.append(P("The repository supports a persistent local stack with Docker Compose: Neo4j 5.26 Community, Redis 7 Alpine, and Qdrant 1.18.0. Named volumes preserve graph, queue, and vector data across container restarts. The API image uses Python 3.12, runs as an unprivileged user, includes Tesseract, and exposes a process-only liveness check.", "BodyCustom"))
    story.append(table([
        ["Component", "Local command / location", "Operational note"],
        ["Infrastructure", "docker compose -f infra/docker-compose.yml up -d", "Neo4j, Redis, and Qdrant use named volumes."],
        ["API", ".venv\\Scripts\\python.exe -m uvicorn backend.app.main:app", "Run from repository root; port 8000."],
        ["Frontend", "npm.cmd --prefix frontend run dev", "Next.js dev server; usually port 3000."],
        ["Telemetry", "python -m telemetry.worker", "Continuous synthetic scan and event publication."],
        ["Ingestion watcher", "python -m ingestion.workers.watcher", "Watch directory to Redis/RQ handoff."],
        ["RQ worker", "rq worker aurag-ingest", "Use SimpleWorker on Windows."],
        ["Managed API", "render.yaml", "Render API plus telemetry and ingestion worker services."],
        ["Managed UI", "frontend/vercel.json", "Vercel project rooted at frontend/."],
    ], [1.35 * inch, 3.0 * inch, 2.5 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(P("Bootstrap is deliberately explicit: install dependencies, start infrastructure, apply schema and seed, then rebuild both vector indexes. Readiness is stricter than liveness and requires configured external providers to respond.", "BodyCustom"))
    story.append(code(".\u005cscripts\u005cbootstrap.ps1\n.\u005cscripts\u005cbootstrap.ps1 -SkipInstall -SkipInfra -InitializeData\n.\u005cscripts\u005csmoke.ps1"))
    story.append(PageBreak())

    section(story, "09", "Security, Reliability, and Data Governance", "Trust boundaries and failure behavior")
    story.append(P("AuRAG is currently a local/demo-oriented operator application rather than a multi-tenant security product. There is no authentication or authorization layer in the repository. User identity is used for mem0 scoping and work-order actor attribution, but it is not an access-control boundary.", "BodyCustom"))
    story.append(table([
        ["Concern", "Current control", "Residual risk / next action"],
        ["Secrets", "Provider keys come from .env; Docker image excludes local .env.", "Use managed secret storage and rotation for production."],
        ["Graph access", "Browser accesses graph through backend proxy only.", "Add auth and query-level authorization before multi-tenant use."],
        ["LLM citations", "Citations are whitelist-filtered to retrieved context keys.", "Add stronger claim-level verification for high-stakes workflows."],
        ["Provider failure", "API endpoints return structured 503 errors; scoring fails open.", "Add circuit breakers, retry budgets, and operator diagnostics."],
        ["Stale edits", "Work orders use expected_version and audit decisions.", "Add broader idempotency keys to all mutating external calls."],
        ["Memory", "mem0 records are user-scoped and expire after 30 days.", "Document retention policy and provide deletion controls."],
        ["Uploads", "50 MB default cap, storage backend abstraction, async queue.", "Add malware scanning, content-type policy, and tenant isolation."],
        ["CORS", "Configured origins are read from BACKEND_CORS_ORIGINS.", "Verify exact Vercel production and preview origins in browser smoke."],
    ], [1.2 * inch, 2.9 * inch, 2.75 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(callout("Important deployment boundary", "Readiness requires Neo4j, Qdrant, Redis, Groq, Gemini, and configured mem0. A service can be alive while the operator workflow is not ready; release checks must use both endpoints.", "amber"))
    story.append(PageBreak())

    section(story, "10", "Testing and Validation", "Automated checks and recorded implementation evidence")
    story.append(P("The repository contains 107 Python test functions across agent, backend, evaluation, ingestion, retrieval, and telemetry suites, plus frontend Vitest and Playwright coverage. The tests are organized by domain rather than by endpoint alone, which keeps pure logic independently testable and API adapters thin.", "BodyCustom"))
    story.append(table([
        ["Area", "Python test files", "Primary contract tested"],
        ["Agents", "tests/agents/*", "Routing, citations, LLM wrappers, RCA, compliance, lessons learned, validation."],
        ["Backend", "tests/backend/*", "Health, chat, graph, telemetry, events, evaluation, comparison, memory, work orders, risk, ingestion."],
        ["Ingestion", "tests/ingestion/*", "Retry, storage, OCR fallback, extraction validation, worker behavior, Gemini utility."],
        ["Retrieval", "tests/retrieval/*", "Plain vector, hybrid fusion, rerank, Qdrant configuration."],
        ["Telemetry", "tests/telemetry/*", "Worker cycle behavior and precision thresholds."],
        ["Evaluation", "tests/evaluation/*", "RAGAS validation and comparison benchmark."],
        ["Frontend", "frontend/**/*.test.tsx + e2e/*.spec.ts", "Component contracts, mobile workflows, operator workflows, API/session utilities."],
    ], [1.0 * inch, 2.6 * inch, 3.25 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(P("Recorded project evidence includes ingestion ground truth of 13/13 expected mentions with zero spurious mentions, hybrid retrieval ground truth of 5/5 queries, agent citation validation of 8/8, supervisor validation of 8/8, monotonic telemetry drift sweeps across six seeded events, and passing frontend lint/build evidence. These are repository-reported validation results; run the current smoke suite against live dependencies before calling a deployment ready.", "BodyCustom"))
    story.append(callout("Verification command set", "Use the full smoke script for live dependency validation. Use -SkipMutatingChecks when only read-oriented checks are appropriate; the full script intentionally leaves a generated smoke work order in Rejected status.", "green"))
    story.append(code(".\\.venv\\Scripts\\python.exe -m pytest\nnpm.cmd --prefix frontend test\nnpm.cmd --prefix frontend run lint\nnpm.cmd --prefix frontend run build\n.\\scripts\\smoke.ps1"))
    story.append(PageBreak())

    section(story, "11", "Limitations and Roadmap", "What is implemented, what is partial, and what remains")
    story.append(P("The current repository has moved beyond the earlier initial architecture baseline: knowledge-retirement risk, GraphRAG comparison, durable predictive events, work-order decisions, evaluation history, configurable CORS, and mem0 adapters are now present in code. The following boundaries remain relevant to engineering decisions.", "BodyCustom"))
    story.append(table([
        ["Boundary", "Current state", "Recommended closure"],
        ["Authentication", "No auth/permissions; local operator identity only.", "Introduce identity provider, role model, tenant boundaries, and audit access policy."],
        ["Telemetry realism", "Synthetic readings and one seeded failure mode per equipment tag.", "Add real historian integration and multiple competing failure signatures per asset."],
        ["P&ID semantics", "Connections are linked when endpoints match known equipment.", "Add line/instrument entities and validate connectivity semantics at scale."],
        ["RAGAS baseline", "Durable history and trend endpoints exist, but judge scores remain model/run sensitive.", "Version evaluation prompts/models and maintain stable benchmark baselines."],
        ["Memory operations", "Fail-open mem0 adapter with TTL metadata.", "Add retention controls, deletion workflow, and provider health metrics."],
        ["Deployment acceptance", "Render/Vercel artifacts and smoke script exist.", "Run fresh managed browser smoke including exact production CORS."],
        ["Release governance", "Repository snapshot is rich but release status depends on live infrastructure.", "Commit a reproducible release baseline and attach smoke evidence."],
    ], [1.35 * inch, 2.8 * inch, 2.7 * inch]))
    story.append(Spacer(1, 0.14 * inch))
    story.append(P("The practical next milestone is a truthful end-to-end environment: provision or restore Neo4j, rebuild the Python runtime if needed, start Qdrant and Redis, apply seed and vector indexes, start API and frontend, and run the smoke suite. Only after that should a managed deployment be labeled operationally ready.", "BodyCustom"))
    story.append(PageBreak())

    section(story, "12", "Appendix", "Repository map, configuration, and quick reference")
    story.append(P("Repository map", "H2Custom"))
    story.append(table([
        ["Path", "Role"],
        ["backend/", "FastAPI application, API routers, core adapters, and domain services."],
        ["agents/", "Supervisor state graph, specialist agents, LLM wrappers, validation."],
        ["retrieval/", "Embeddings, Neo4j vector, Qdrant, BM25, graph traversal, fusion, reranking."],
        ["ingestion/", "Parsing, OCR, P&ID vision, entity extraction, storage, watcher, queue tasks."],
        ["telemetry/", "Synthetic readings, signature matching, worker, warning and draft logic."],
        ["evaluation/", "RAGAS scoring and validation."],
        ["frontend/", "Next.js operator console, typed API wrappers, unit/e2e tests."],
        ["infra/", "Docker Compose and Neo4j schema/seed."],
        ["scripts/", "Bootstrap and live smoke verification."],
        ["data/", "Synthetic plant source documents and scans."],
    ], [1.4 * inch, 5.45 * inch]))
    story.append(Spacer(1, 0.16 * inch))
    story.append(P("Key environment variables", "H2Custom"))
    story.append(table([
        ["Variable", "Purpose"],
        ["NEO4J_URI / NEO4J_USERNAME / NEO4J_PASSWORD", "Graph database connection."],
        ["QDRANT_URL / QDRANT_API_KEY", "Dense vector store connection."],
        ["REDIS_URL", "Ingestion queue and worker connection."],
        ["GROQ_API_KEY / GROQ_JUDGE_MODEL", "Routing, reasoning, and judge models."],
        ["GEMINI_API_KEY / GEMINI_INGESTION_MODEL", "OCR, P&ID vision, and optional reasoning."],
        ["MEM0_API_KEY / MEM0_DIR", "Cross-session memory provider and runtime state."],
        ["BACKEND_CORS_ORIGINS", "Comma-separated allowed browser origins."],
        ["INGEST_WATCH_DIR / INGEST_STORAGE_BACKEND", "Continuous ingestion source and storage mode."],
        ["TELEMETRY_INTERVAL_SECONDS / TELEMETRY_EQUIPMENT_TAGS", "Background predictive scan cadence and scope."],
    ], [2.65 * inch, 4.2 * inch]))
    story.append(Spacer(1, 0.16 * inch))
    story.append(P("Document provenance", "H2Custom"))
    story.append(P("This PDF was generated from the AuRAG repository at C:\\ace\\products\\AuRAG on September 27, 2026. It reflects source code and project documentation available in that workspace. Runtime availability, provider credentials, database contents, and deployment readiness can change independently of the document and must be verified with the live smoke suite.", "BodyCustom"))
    story.append(Spacer(1, 0.3 * inch))
    story.append(callout("End state", "Core product implementation is broad and internally coherent. Production readiness remains an operational verification problem: infrastructure, credentials, browser CORS, and release evidence must all be green together.", "teal"))
    return story


def draw_header_footer(canvas, doc):
    canvas.saveState()
    page = canvas.getPageNumber()
    if page > 2:
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(0.72 * inch, 0.58 * inch, 7.78 * inch, 0.58 * inch)
        canvas.setFont(FONT_BOLD, 7.5)
        canvas.setFillColor(TEAL)
        canvas.drawString(0.72 * inch, 0.36 * inch, "AURAG  /  TECHNICAL DOCUMENTATION")
        canvas.setFont(FONT, 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(7.78 * inch, 0.36 * inch, f"{page:02d}")
    canvas.restoreState()


def main():
    doc = BaseDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.62 * inch,
        bottomMargin=0.72 * inch,
        title="AuRAG Technical Documentation",
        author="AuRAG Engineering",
        subject="Industrial Knowledge Intelligence platform",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=draw_header_footer)])
    doc.build(build_story())
    print(OUTPUT)


if __name__ == "__main__":
    main()
