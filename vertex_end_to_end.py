import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
import vertexai
from google.oauth2 import service_account
from vertexai.generative_models import GenerativeModel

# Ensure we import the local utils.py even if the script is run from another CWD
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils import extract_text_from_pdf, parse_graph_data

# Load environment variables from .env if present
load_dotenv()


# ---- Vertex AI helpers ---------------------------------------------------- #

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
DEFAULT_LOCATION = os.getenv("LOCATION", "us-central1")
DEFAULT_PROJECT = os.getenv("PROJECT_ID") or os.getenv("PROJECT_NAME")
DEFAULT_KEYFILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "keyfile.json")
DEFAULT_MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "8192"))


def init_vertexai_from_keyfile(
    keyfile_path: str,
    project: str,
    location: str,
) -> None:
    """Initialize Vertex AI using a service account key file (not WIF)."""
    credentials = service_account.Credentials.from_service_account_file(
        keyfile_path,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    vertexai.init(project=project, location=location, credentials=credentials)


def call_vertex(
    prompt: str,
    model_name: str = DEFAULT_MODEL,
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    temperature: float = 0.01,
    top_p: float = 0.1,
    top_k: int = 40,
    response_mime_type: Optional[str] = None,
) -> str:
    """Call a Gemini model and return plain text."""
    model = GenerativeModel(model_name)
    gen_config = {
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
    }
    if response_mime_type:
        gen_config["response_mime_type"] = response_mime_type

    response = model.generate_content(prompt, generation_config=gen_config)
    if hasattr(response, "text") and response.text:
        return response.text
    # Fallback if the SDK returns candidates only
    parts = []
    for candidate in getattr(response, "candidates", []) or []:
        for part in getattr(candidate, "content", []).parts:
            if getattr(part, "text", None):
                parts.append(part.text)
    return "".join(parts)


# ---- LLM prompts mirroring current app flow ------------------------------- #

def get_summary_with_context(text: str, context: Optional[str] = None, model_name: str = DEFAULT_MODEL) -> str:
    """Summarize regulation text using the same prompt/structure as anthropic_llm.py."""
    if context:
        prompt = f"""
            You are an AI assistant specialized in analyzing financial regulation documents to produce accurate, consistent, and structured summaries.

            Your task is to extract and explain the key operational, compliance, and reporting requirements, especially highlighting changes between previous and current regulatory expectations - including reporting methods, data fields, and submission timelines.

            Resolve any internal references and use only the content provided.

            Format the response with this structure:

            ---

            **Regulation Summary:**

            1. **Purpose and Objective:**
            State the regulatory intent - especially changes in reporting infrastructure and traceability.

            2. **Scope and Applicability:**
            List impacted entities, transaction types (e.g., OTC positions), and applicable metals or instruments.

            3. **Definitions and Eligibility:**
            Clarify critical terms like Settlement Type, LEI usage, Short Code, etc.

            4. **Reporting Requirements:**
            Compare new vs. old requirements: deadlines, submission channels (email vs. UDG), file types, validation steps.

            5. **Inclusion and Exclusion Criteria:**
            Detail positions to be included (e.g., all OTC positions, no threshold), and treatment of anonymous or non-LEI holders.

            6. **Data Rules and Validation Logic:**
            Describe XML structure, required fields (e.g., SeqNo, Report Reference), validation rules (e.g., OTC-008).

            7. **Operational Notes and Exceptions:**
            Mention nil reporting, dual submissions during parallel run, and third-party communication responsibilities.

            ---

            **Regulation Document:**
            {text}

            Reference of the past year regulation entity relationship is given for your reference below. Use it only for semantic difference matching. Make sure you figure out the differences very clear in the above text and previous year's summarized text and provide the summary for this year based on above text.

            {context}
        """
    else:
        prompt = f"""
            You are an AI assistant specialized in analyzing financial regulation documents to produce accurate, consistent, and structured summaries.

            Your task is to extract and explain the key operational, compliance, and reporting requirements, especially highlighting changes between previous and current regulatory expectations - including reporting methods, data fields, and submission timelines.

            Resolve any internal references and use only the content provided.

            Format the response with this structure:

            ---

            **Regulation Summary:**

            1. **Purpose and Objective:**
            State the regulatory intent - especially changes in reporting infrastructure and traceability.

            2. **Scope and Applicability:**
            List impacted entities, transaction types (e.g., OTC positions), and applicable metals or instruments.

            3. **Definitions and Eligibility:**
            Clarify critical terms like Settlement Type, LEI usage, Short Code, etc.

            4. **Reporting Requirements:**
            Compare new vs. old requirements: deadlines, submission channels (email vs. UDG), file types, validation steps.

            5. **Inclusion and Exclusion Criteria:**
            Detail positions to be included (e.g., all OTC positions, no threshold), and treatment of anonymous or non-LEI holders.

            6. **Data Rules and Validation Logic:**
            Describe XML structure, required fields (e.g., SeqNo, Report Reference), validation rules (e.g., OTC-008).

            7. **Operational Notes and Exceptions:**
            Mention nil reporting, dual submissions during parallel run, and third-party communication responsibilities.

            ---

            **Regulation Document:**
            {text}
        """
    return call_vertex(prompt, model_name=model_name)


def _extract_json_blob(raw_text: str) -> Dict:
    """
    Pick the first valid JSON object from the model response and validate it.
    Handles code fences and avoids over-greedy matching that breaks parsing.
    """
    text = raw_text.strip()

    # Direct parse attempt (handles pure JSON responses)
    try:
        return json.loads(text)
    except Exception:
        pass

    # Strip fenced blocks and try again
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence_match:
        fenced_text = fence_match.group(1)
        try:
            return json.loads(fenced_text)
        except Exception:
            text = fenced_text  # continue scanning using fenced content

    candidates: List[str] = []

    # Prefer fenced JSON blocks if present
    fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates.extend(fenced)

    # Scan for balanced brace blocks
    start = text.find("{")
    while start != -1:
        depth = 0
        end = None
        for idx, ch in enumerate(text[start:], start=start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
            if depth == 0:
                end = idx
                break
        if end is not None:
            candidates.append(text[start : end + 1])
            start = text.find("{", end + 1)
        else:
            break

    for cand in candidates:
        try:
            return json.loads(cand)
        except json.JSONDecodeError:
            continue

    raise ValueError("No valid JSON object found in LLM response")


def get_entity_relationship_with_context(
    summary_text: str,
    context: Optional[str] = None,
    model_name: str = DEFAULT_MODEL,
) -> Dict:
    """Extract entity relationships using the same prompt/logic as anthropic_llm.py."""
    base_prompt = f"""
        You are an AI assistant specialized in extracting structured semantic relationships from financial regulation summaries.

        Your task is to extract subject-verb-object relationships focused on weekly OTC position reporting by Members to LME, with key conditional and validation rules.

        For the given summary of the regulation, provide entity relationships in subject-verb-object, optionality, condition for relationship to be active, property of the object which is part of the condition, the frequency of condition validation and the actual thresholds where XYZ bank is licensed commercial bank. Consider the essential elements of an obligation such as active subject (creditor or obligee), passive subject (debtor or obligor) and prestation (object or subject matter of the obligation) and write the relationships in the above format with the perspective of XYZ bank as an obligor where the relationships will be useful for creating the standard operating procedures for the bank.
        The verb should correspond to obligation and the conditions which make the obligation mandatory should be reported as conditions. For e.g. XYZ bank grants a loan to any customer has no meaning from the obligation perspective but a granting of a loan is a condition which obligates XYZ bank to report the loan and associated attributes.
        You as an assistant should resolve all of the cross references within the document. Assign each entity a globally unique ID.

        ?? **Instructions**:

        - IGNORE isolated nodes and ONLY extract entities that participate in at least one relationship and are connected to root node
        - Avoid listing entities that are not connected to any verb-object pair
        - Merge similar entities (e.g., all LCBs as one node)
        - For each relationship, include:
            - Subject ID & Name
            - Verb (action)
            - Object ID & Name
            - Optionality
            - Condition for relationship to be active
            - Property of object used in the condition
            - Thresholds involved
            - Reporting frequency
            
        ### Format:
        Respond in **valid JSON only** using the structure below. Do not explain or include any additional commentary.

        ```json
        {{
            "entities": [
                {{"id": "E1", "name": "XYZ Bank (LCB)", "type": "organization"}}
            ],
            "relationships": [
                {{
                    "subject_id": "E1",
                    "subject_name": "XYZ Bank (LCB)",
                    "verb": "Reports",
                    "object_id": "E2",
                    "object_name": "Loan (to Prime Customer)",
                    "Optionality": "Conditional (Only if eligible loans exist)",
                    "Condition for Relationship to be Active": "...",
                    "Property of Object (part of condition)": "...",
                    "Thresholds": "...",
                    "frequency": "to be validated quarterly"
                }}
            ]
        }}

        -- 

        **Regulation Document:**:
        {summary_text}
    """

    if context:
        base_prompt += f"\nReference of the previous year's regulation summary and graph is given below. Use it only for semantic difference matching. Reuse existing structure, entities, and relationship patterns unless the regulation explicitly defines a new obligation.\n{context}"

    raw = call_vertex(base_prompt, model_name=model_name)
    return _extract_json_blob(raw)


# ---- Graph + PlantUML helpers --------------------------------------------- #

def to_canonical_graph(relationship_json: Dict) -> Dict:
    """Convert the entity relationship JSON to a canonical nodes/edges dict for PlantUML."""
    nodes = []
    edges = []

    for entity in relationship_json.get("entities", []):
        nodes.append(
            {
                "id": entity.get("id"),
                "label": entity.get("name", entity.get("id")),
                "type": entity.get("type", "process"),
            }
        )

    for rel in relationship_json.get("relationships", []):
        edges.append(
            {
                "source": rel.get("subject_id"),
                "target": rel.get("object_id"),
                "relation": rel.get("verb", ""),
                "condition": rel.get("Condition for Relationship to be Active", ""),
                "optionality": rel.get("Optionality", ""),
                "frequency": rel.get("frequency", ""),
            }
        )

    return {"nodes": nodes, "edges": edges}


def sanitize_id(raw: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in raw)


def generate_plantuml(graph: Dict, title: Optional[str] = None, scale: Optional[str] = "max 1200 width") -> str:
    nodes: List[Dict] = graph.get("nodes", [])
    edges: List[Dict] = graph.get("edges", [])

    lines: List[str] = ["@startuml"]
    if title:
        lines.append(f"title {title}")
    if scale:
        lines.append(f"scale {scale}")

    lines.append("skinparam backgroundColor #FFFFFF")
    lines.append("skinparam componentStyle rectangle")
    lines.append("skinparam ArrowColor #555555")
    lines.append("skinparam ArrowThickness 1")

    for node in nodes:
        node_id = sanitize_id(node["id"])
        label = node.get("label", node["id"])
        ntype = (node.get("type") or "process").lower()

        if ntype in ("actor", "party", "role", "person"):
            lines.append(f'actor "{label}" as {node_id}')
        elif ntype in ("system", "application", "repo", "trade_repository"):
            lines.append(f'node "{label}" as {node_id}')
        else:
            lines.append(f'component "{label}" as {node_id}')

    lines.append("")

    for edge in edges:
        src = sanitize_id(edge["source"])
        dst = sanitize_id(edge["target"])
        relation = edge.get("relation", "")
        condition = edge.get("condition", "")
        optionality = edge.get("optionality", "")
        frequency = edge.get("frequency", "")

        label_parts = [relation]
        if condition:
            label_parts.append(f"({condition})")
        if optionality:
            label_parts.append(f"[{optionality}]")
        if frequency:
            label_parts.append(f"{{{frequency}}}")

        label = " ".join([p for p in label_parts if p]).strip()
        if label:
            lines.append(f"{src} --> {dst} : {label}")
        else:
            lines.append(f"{src} --> {dst}")

    lines.append("@enduml")
    return "\n".join(lines)


def generate_plantuml_diff(old_graph: Dict, new_graph: Dict, title: Optional[str] = None, scale: Optional[str] = "max 1200 width") -> str:
    """Combined diff view: common edges gray, new green, removed red."""
    def edge_key(e: Dict) -> tuple:
        return (
            e.get("source"),
            e.get("target"),
            e.get("relation", ""),
            e.get("condition", ""),
            e.get("optionality", ""),
            e.get("frequency", ""),
        )

    old_edges = {edge_key(e): e for e in old_graph.get("edges", [])}
    new_edges = {edge_key(e): e for e in new_graph.get("edges", [])}

    common_keys = old_edges.keys() & new_edges.keys()
    added_keys = new_edges.keys() - old_edges.keys()
    removed_keys = old_edges.keys() - new_edges.keys()

    nodes_by_id: Dict[str, Dict] = {}
    for g in (old_graph, new_graph):
        for n in g.get("nodes", []):
            nodes_by_id.setdefault(n["id"], n)

    lines: List[str] = ["@startuml"]
    if title:
        lines.append(f"title {title}")
    if scale:
        lines.append(f"scale {scale}")

    lines.append("skinparam backgroundColor #FFFFFF")
    lines.append("skinparam componentStyle rectangle")
    lines.append("legend right")
    lines.append("  <color:#555555>Common</color>")
    lines.append("  <color:#008800>New</color>")
    lines.append("  <color:#BB0000>Removed</color>")
    lines.append("endlegend")

    for node in nodes_by_id.values():
        node_id = sanitize_id(node["id"])
        label = node.get("label", node["id"])
        ntype = (node.get("type") or "process").lower()

        if ntype in ("actor", "party", "role", "person"):
            lines.append(f'actor "{label}" as {node_id}')
        elif ntype in ("system", "application", "repo", "trade_repository"):
            lines.append(f'node "{label}" as {node_id}')
        else:
            lines.append(f'component "{label}" as {node_id}')

    lines.append("")

    for k in common_keys:
        e = new_edges[k]
        lines.append(_edge_line(e, color=None))

    for k in added_keys:
        e = new_edges[k]
        lines.append(_edge_line(e, color="#008800"))

    for k in removed_keys:
        e = old_edges[k]
        lines.append(_edge_line(e, color="#BB0000", dashed=True, prefix="REMOVED: "))

    lines.append("@enduml")
    return "\n".join(lines)


def _edge_line(edge: Dict, color: Optional[str], dashed: bool = False, prefix: str = "") -> str:
    src = sanitize_id(edge["source"])
    dst = sanitize_id(edge["target"])
    relation = edge.get("relation", "")
    condition = edge.get("condition", "")
    optionality = edge.get("optionality", "")
    frequency = edge.get("frequency", "")

    label_parts = [prefix or "", relation]
    if condition:
        label_parts.append(f"({condition})")
    if optionality:
        label_parts.append(f"[{optionality}]")
    if frequency:
        label_parts.append(f"{{{frequency}}}")

    label = " ".join([p for p in label_parts if p]).strip()
    arrow = "-->" if not dashed else "..>"
    if color:
        arrow = f'-[{color}]{arrow[1:]}'

    if label:
        return f"{src} {arrow} {dst} : {label}"
    return f"{src} {arrow} {dst}"


# ---- Confluence publishing ------------------------------------------------ #

def build_confluence_macro(plantuml_text: str, intro_html: Optional[str] = None) -> str:
    intro = intro_html or "<p>Auto-generated regulatory graph.</p>"
    return f"""{intro}
<ac:structured-macro ac:name="plantuml">
  <ac:plain-text-body><![CDATA[
{plantuml_text}
  ]]></ac:plain-text-body>
</ac:structured-macro>
"""


def publish_to_confluence(
    *,
    title: str,
    plantuml_text: str,
    intro_html: Optional[str],
    space_key: str,
    parent_page_id: Optional[str],
    base_url: str,
    username: str,
    api_token: str,
) -> Dict:
    macro_body = build_confluence_macro(plantuml_text, intro_html=intro_html)
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {
            "storage": {
                "value": macro_body,
                "representation": "storage",
            }
        },
    }
    if parent_page_id:
        payload["ancestors"] = [{"id": parent_page_id}]

    url = f"{base_url.rstrip('/')}/rest/api/content"
    resp = requests.post(
        url,
        auth=(username, api_token),
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ---- Pipeline driver ------------------------------------------------------ #

def run_pipeline(
    *,
    new_pdf: Path,
    old_pdf: Optional[Path],
    model_name: str,
    page_title: str,
) -> Dict:
    """Execute: read PDFs -> LLM -> graph -> PlantUML."""
    new_text = extract_text_from_pdf(str(new_pdf))
    old_text = extract_text_from_pdf(str(old_pdf)) if old_pdf else None

    old_summary = get_summary_with_context(old_text, model_name=model_name) if old_text else None
    new_summary = get_summary_with_context(new_text, context=old_summary, model_name=model_name)

    old_entities = get_entity_relationship_with_context(old_summary, model_name=model_name) if old_summary else None
    new_entities = get_entity_relationship_with_context(
        new_summary,
        context=json.dumps(old_entities) if old_entities else None,
        model_name=model_name,
    )

    new_canonical = to_canonical_graph(new_entities)
    new_graph_nx = parse_graph_data(new_entities)
    old_canonical = to_canonical_graph(old_entities) if old_entities else None

    plantuml_new = generate_plantuml(new_canonical, title=page_title)
    plantuml_diff = (
        generate_plantuml_diff(old_canonical, new_canonical, title=f"{page_title} (Diff)")
        if old_canonical
        else None
    )

    return {
        "old_summary": old_summary,
        "new_summary": new_summary,
        "old_entities": old_entities,
        "new_entities": new_entities,
        "old_graph_nx": parse_graph_data(old_entities) if old_entities else None,
        "new_graph_nx": new_graph_nx,
        "plantuml_new": plantuml_new,
        "plantuml_diff": plantuml_diff,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="End-to-end PDF -> Vertex AI -> Graph -> PlantUML -> Confluence test runner.",
    )
    parser.add_argument("--new-pdf", required=True, type=Path, help="Path to the new regulation PDF.")
    parser.add_argument("--old-pdf", type=Path, help="Optional old regulation PDF for diff.")
    parser.add_argument("--project", default=DEFAULT_PROJECT, help="GCP project ID.")
    parser.add_argument("--location", default=DEFAULT_LOCATION, help="Vertex AI location.")
    parser.add_argument("--keyfile", default=DEFAULT_KEYFILE, type=Path, help="Service account keyfile.json.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Gemini model name, e.g., gemini-1.5-flash.")
    parser.add_argument("--publish", action="store_true", help="Publish PlantUML to Confluence.")
    parser.add_argument("--confluence-url", default=os.getenv("CONFLUENCE_BASE_URL"), help="Confluence base URL (e.g., https://your-domain.atlassian.net/wiki).")
    parser.add_argument("--confluence-space", default=os.getenv("CONFLUENCE_SPACE"), help="Confluence space key.")
    parser.add_argument("--confluence-parent", default=os.getenv("CONFLUENCE_PARENT_PAGE_ID"), help="Parent page ID (optional).")
    parser.add_argument("--confluence-user", default=os.getenv("CONFLUENCE_USERNAME"), help="Confluence username/email.")
    parser.add_argument("--confluence-token", default=os.getenv("CONFLUENCE_API_TOKEN"), help="Confluence API token/password.")
    parser.add_argument("--title", help="Title for PlantUML/Confluence page; defaults to PDF name.")
    parser.add_argument("--plantuml-out", type=Path, help="Optional path to save the PlantUML text.")

    args = parser.parse_args()

    if not args.project or not args.location:
        raise SystemExit("Project and location are required (set PROJECT_ID/LOCATION or pass flags).")
    if not args.keyfile.exists():
        raise SystemExit(f"Keyfile not found: {args.keyfile}")

    init_vertexai_from_keyfile(str(args.keyfile), args.project, args.location)

    title = args.title or args.new_pdf.stem
    results = run_pipeline(
        new_pdf=args.new_pdf,
        old_pdf=args.old_pdf,
        model_name=args.model,
        page_title=title,
    )

    print("\n=== Summaries ===")
    if results["old_summary"]:
        print("\n[OLD]\n", results["old_summary"])
    print("\n[NEW]\n", results["new_summary"])

    print("\n=== Entity Relationships (JSON) ===")
    if results["old_entities"]:
        print("\n[OLD]\n", json.dumps(results["old_entities"], indent=2))
    print("\n[NEW]\n", json.dumps(results["new_entities"], indent=2))

    print("\n=== Graph Stats ===")
    if results["old_graph_nx"]:
        print(f"Old graph: {results['old_graph_nx'].number_of_nodes()} nodes, {results['old_graph_nx'].number_of_edges()} edges")
    print(f"New graph: {results['new_graph_nx'].number_of_nodes()} nodes, {results['new_graph_nx'].number_of_edges()} edges")

    print("\n=== PlantUML (new) ===")
    print(results["plantuml_new"])
    if args.plantuml_out:
        args.plantuml_out.write_text(results["plantuml_new"], encoding="utf-8")
        print(f"\nSaved PlantUML to {args.plantuml_out}")

    if results["plantuml_diff"]:
        print("\n=== PlantUML (diff) ===")
        print(results["plantuml_diff"])

    if args.publish:
        missing = [
            name
            for name, val in [
                ("CONFLUENCE_BASE_URL", args.confluence_url),
                ("CONFLUENCE_SPACE", args.confluence_space),
                ("CONFLUENCE_USERNAME", args.confluence_user),
                ("CONFLUENCE_API_TOKEN", args.confluence_token),
            ]
            if not val
        ]
        if missing:
            raise SystemExit(f"Missing Confluence config: {', '.join(missing)}")

        intro_html = f"<p>Generated from PDF: <strong>{args.new_pdf.name}</strong></p>"
        publish_title = title if not args.old_pdf else f"{title} (Comparison)"
        publish_body = results["plantuml_diff"] or results["plantuml_new"]

        response = publish_to_confluence(
            title=publish_title,
            plantuml_text=publish_body,
            intro_html=intro_html,
            space_key=args.confluence_space,
            parent_page_id=args.confluence_parent,
            base_url=args.confluence_url,
            username=args.confluence_user,
            api_token=args.confluence_token,
        )
        link = response.get("_links", {}).get("base", "") + response.get("_links", {}).get("webui", "")
        print(f"\nPublished to Confluence: {link or response.get('id')}")


if __name__ == "__main__":
    main()
