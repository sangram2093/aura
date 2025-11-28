"""
Minimal Confluence publish test.

Hardcode your PlantUML text in PLANTUML_TEXT and fill in the Confluence
connection values below. Then run:

    python confluence_publish_test.py

If successful, it will print the created page ID/link; otherwise it will raise.
"""

import json
import requests

# ---- Hardcode your PlantUML content here (e.g., results["plantuml_diff"]) ----
PLANTUML_TEXT = """
@startuml
title Sample Diff
skinparam backgroundColor #FFFFFF

actor "Actor A" as A
actor "Actor B" as B

A --> B : [C1] Reports

legend bottom
  Edge details (match IDs on arrows):
  C1: Actor A -> Actor B | Reports | cond=Sample condition; opt=Optional; freq=Weekly
endlegend
@enduml
"""

# ---- Confluence connection/config (fill these) ------------------------------
CONFLUENCE_BASE_URL = "https://your-domain.atlassian.net/wiki"  # e.g., https://your-domain.atlassian.net/wiki
CONFLUENCE_SPACE = "SPACEKEY"
CONFLUENCE_PARENT_PAGE_ID = None  # or "123456789" if you want to nest under a parent
CONFLUENCE_USERNAME = "you@domain.com"  # email/username for Confluence
CONFLUENCE_API_TOKEN = "your-api-token"  # API token/password
PAGE_TITLE = "PlantUML Publish Test"
INTRO_HTML = "<p>Confluence publish smoke test for PlantUML.</p>"


# ---- Publisher --------------------------------------------------------------
def build_confluence_macro(plantuml_text: str, intro_html: str | None = None) -> str:
    intro = intro_html or "<p>Auto-generated graph.</p>"
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
    intro_html: str | None,
    space_key: str,
    parent_page_id: str | None,
    base_url: str,
    username: str,
    api_token: str,
) -> dict:
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


def main() -> None:
    missing = [
        name
        for name, val in [
            ("CONFLUENCE_BASE_URL", CONFLUENCE_BASE_URL),
            ("CONFLUENCE_SPACE", CONFLUENCE_SPACE),
            ("CONFLUENCE_USERNAME", CONFLUENCE_USERNAME),
            ("CONFLUENCE_API_TOKEN", CONFLUENCE_API_TOKEN),
        ]
        if not val
    ]
    if missing:
        raise SystemExit(f"Missing config: {', '.join(missing)}")

    response = publish_to_confluence(
        title=PAGE_TITLE,
        plantuml_text=PLANTUML_TEXT,
        intro_html=INTRO_HTML,
        space_key=CONFLUENCE_SPACE,
        parent_page_id=CONFLUENCE_PARENT_PAGE_ID,
        base_url=CONFLUENCE_BASE_URL,
        username=CONFLUENCE_USERNAME,
        api_token=CONFLUENCE_API_TOKEN,
    )
    link = response.get("_links", {})
    web = link.get("webui") or ""
    base = link.get("base") or CONFLUENCE_BASE_URL.rstrip("/")
    print(f"Created page id={response.get('id')}, link={base}{web}")


if __name__ == "__main__":
    main()
