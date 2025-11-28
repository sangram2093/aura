import os
import json
import re
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Bedrock client
bedrock = boto3.client("bedrock-runtime", region_name="us-east-2")

# Get the Inference Profile ARN from environment
MODEL_ARN = os.getenv("BEDROCK_MODEL_ARN")  # e.g., arn:aws:bedrock:us-east-2:908924925940:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1-0

# Claude 3.5 Sonnet uses this version tag
ANTHROPIC_VERSION = "bedrock-2023-05-31"


# Unified Claude call
def call_claude(prompt):
    body = {
        "messages": [{"role": "user", "content": prompt}],
        "anthropic_version": ANTHROPIC_VERSION,
        "max_tokens": 4096,
        "temperature": 0.01,
        "top_p": 0.1
    }

    response = bedrock.invoke_model(
        modelId=MODEL_ARN,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body)
    )

    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text'].strip()


# Summary generation
def get_summary_with_context(text, context=None):
    if context:
        prompt = f"""
            You are an AI assistant specialized in analyzing financial regulation documents to produce accurate, consistent, and structured summaries.

            Your task is to extract and explain the key operational, compliance, and reporting requirements, especially highlighting changes between previous and current regulatory expectations — including reporting methods, data fields, and submission timelines.

            Resolve any internal references and use only the content provided.

            Format the response with this structure:

            ---

            **Regulation Summary:**

            1. **Purpose and Objective:**
            State the regulatory intent — especially changes in reporting infrastructure and traceability.

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

            Your task is to extract and explain the key operational, compliance, and reporting requirements, especially highlighting changes between previous and current regulatory expectations — including reporting methods, data fields, and submission timelines.

            Resolve any internal references and use only the content provided.

            Format the response with this structure:

            ---

            **Regulation Summary:**

            1. **Purpose and Objective:**
            State the regulatory intent — especially changes in reporting infrastructure and traceability.

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
    return call_claude(prompt)


# Entity relationship extraction
def get_entity_relationship_with_context(text, context=None):
    base_prompt = f"""
        You are an AI assistant specialized in extracting structured semantic relationships from financial regulation summaries.

        Your task is to extract subject-verb-object relationships focused on weekly OTC position reporting by Members to LME, with key conditional and validation rules.

        For the given summary of the regulation, provide entity relationships in subject-verb-object, optionality, condition for relationship to be active, property of the object which is part of the condition, the frequency of condition validation and the actual thresholds where XYZ bank is licensed commercial bank. Consider the essential elements of an obligation such as active subject (creditor or obligee), passive subject (debtor or obligor) and prestation (object or subject matter of the obligation) and write the relationships in the above format with the perspective of XYZ bank as an obligor where the relationships will be useful for creating the standard operating procedures for the bank.
        The verb should correspond to obligation and the conditions which make the obligation mandatory should be reported as conditions. For e.g. XYZ bank grants a loan to any customer has no meaning from the obligation perspective but a granting of a loan is a condition which obligates XYZ bank to report the loan and associated attributes.
        You as an assistant should resolve all of the cross references within the document. Assign each entity a globally unique ID.

        🔷 **Instructions**:

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
        {text}
    """

    if context:
        base_prompt += f"\nReference of the previous year's regulation summary and graph is given below. Use it only for semantic difference matching. Reuse existing structure, entities, and relationship patterns unless the regulation explicitly defines a new obligation.\n{context}"

    response_text = call_claude(base_prompt)
    match = re.search(r'(\{.*\})', response_text, re.DOTALL)
    if match:
        json_text = match.group(1)
        json.loads(json_text)  # Validate JSON
        return json_text
    else:
        raise ValueError("Invalid JSON returned by Claude")


# KOP generation
def get_kop_doc(new_summary, new_json_str):
    prompt = f"""
        You are an AI assistant for interpreting financial regulations and converting them into executable Key Operating Procedures (KOP) for back-office and compliance operations staff.

        The regulation pertains to the computation and submission of the **Average Weighted Prime Rate (AWPR)** by Licensed Commercial Banks (LCBs), typically on a weekly basis, to the Central Bank.

        Your output must be a **clear, step-by-step operating procedure** that enables the bank’s operations team to consistently comply with the regulation, covering eligibility filtering, calculation, reporting, validation, and submission.

        Use the following structure:

        ---

        **KOP Document – AWPR Regulation**

        **Purpose:**
        State the purpose of the AWPR regulation in simple terms — for example, to ensure transparent and consistent monitoring of prime lending rates in the financial system.

        **Scope:**
        Applies to all **Licensed Commercial Banks (LCBs)** operating in **Sri Lanka** that offer short-term loans or overdrafts to **prime customers**.

        **Functional Overview:**
        Briefly describe what the regulation requires:
        - Weekly reporting of newly disbursed or repriced prime loans and overdrafts
        - Filtering based on tenure and amount thresholds
        - Accurate interest rate computation per guidelines

        **Applications Involved:**
        List the systems or tools used in the process:
        - Core Banking Loan System
        - Interest Rate Management System
        - Excel-based Reporting Tool (or XML/CSV exporter)
        - Email Client or Submission Portal

        **Process Steps (Step-by-Step Instructions):**

        1. Extract all loan and overdraft transactions disbursed or repriced during the current reporting week.
        2. Filter transactions where:
        - The customer is classified as a **Prime Customer**
        - Tenure is **less than 3 months**
        - Loan/OD value is **greater than 10 million LKR**
        3. Exclude any of the following:
        - Government-backed or subsidized credit
        - Call money or interbank lending
        - Foreign currency denominated loans (unless specified)
        4. For eligible records:
        - Identify the **Disbursed Amount**, **Interest Rate**, and **Loan Tenure**
        - Validate that the interest rate used is current and correctly classified
        5. Calculate the **AWPR** using the formula:
        [
        AWPR = frac(sum (Loan Amount times Interest Rate)) divide by (sum (Loan Amount))
        ]
        6. Populate the reporting template with eligible loans and calculated AWPR
        7. Review the report for:
        - Duplicates
        - Incorrect rates or classifications
        - Missing Prime Customer IDs
        8. Submit the final report to the **Central Bank of Sri Lanka** by the stipulated deadline (e.g., Monday 10:00 AM) via:
        - Encrypted email, or
        - Designated regulatory portal (if applicable)

        **Validation Checklist:**
        - ✅ Only prime customers included
        - ✅ Minimum loan value and tenure criteria met
        - ✅ Interest rates match current rate sheets
        - ✅ Nil report submitted if no eligible transactions
        - ✅ Submission completed before cutoff

        **Template Snapshot (Optional):**
        Include or refer to the reporting format. Example columns:
        - Customer Type
        - Disbursed Amount
        - Interest Rate
        - Loan Type
        - Repriced (Yes/No)

        **Escalation:**
        In case of issues:
        - Technical issues → Contact Internal IT/Reporting Tool Team
        - Regulatory queries → Contact CBSL regulatory liaison officer or central point of contact

        ---

        **Input Regulation Summary:**
        {new_summary}
    """
    return call_claude(prompt)

# BRD generation
def get_brd_doc(new_summary, new_json_str):
    prompt = f"""
        You are an AI analyst and business consultant specialized in interpreting financial regulations, particularly those involving interest rate reporting requirements such as the Average Weighted Prime Rate (AWPR).

        Your task is to analyze the given AWPR regulation summary and generate a professional, structured Business Requirement Document (BRD) that can be used by compliance, operations, and IT teams in a financial institution.

        Focus on regulatory expectations from Licensed Commercial Banks (LCBs) with respect to data reporting, eligibility conditions, frequency, and calculation logic.

        ---

        **Generate the BRD with the following sections:**

        1. **Introduction**
        - Briefly explain the objective of the AWPR regulation.
        - Include the regulatory body, reporting obligation, and the rationale behind AWPR tracking.

        2. **Scope**
        - *In Scope*: Define the categories of loans, customer types (e.g., Prime Customers), and institutions required to report.
        - *Out of Scope*: Clearly mention any exclusions such as non-prime lending, interbank credit lines, or specific instruments.

        3. **Eligibility Criteria**
        - Define what constitutes an eligible loan/overdraft.
        - Include duration (e.g., <3 months), value threshold (e.g., >10 million LKR), and disbursement conditions.
        - Mention any conditions like excluding government-backed credit or concessional lending.

        4. **Reportability Rules**
        Use the format below to list different loan/overdraft scenarios:

        | Ref ID | Scenario                          | Reporting Rule Description                                         | Logic/Condition                                  |
        |--------|-----------------------------------|--------------------------------------------------------------------|--------------------------------------------------|
        | R1     | New Loan to Prime Customer        | Must be reported in current week’s AWPR                           | Tenure < 3 months, Value > 10M LKR              |
        | R2     | Repriced Loan with same terms     | Include if interest rate changes in the week                      | Exclude if no change in contractual terms        |
        | R3     | Overdraft converted to Loan       | Report as new loan if restructured in reporting window            | Maintain traceability of original credit facility |

        5. **Field Mapping**
        - Provide a mapping of required fields in the report (e.g., Prime Customer, Loan Value, Interest Rate).
        - Define data derivation logic for each field. Example:

            | Field Name         | Source System       | Description                           | Derivation Logic                          |
            |--------------------|---------------------|---------------------------------------|-------------------------------------------|
            | Disbursed Amount   | Loan Origination    | Amount given to borrower              | Exclude taxes/charges                     |
            | Interest Rate      | Core Banking System | Rate applicable at disbursement       | Use fixed rate or latest floating rate    |

        6. **Report Submission**
        - State the frequency (e.g., weekly, monthly).
        - Mention the submission method (e.g., email, portal upload).
        - Include cut-off time (e.g., by Monday 10:00 AM).
        - Clarify re-submission process in case of errors.

        7. **Validation and Exception Rules**
        - List any validation rules before submission (e.g., no empty interest rate fields).
        - Define how nil reporting should be handled (e.g., explicit zero submission if no eligible loans).
        - Specify exceptions allowed by the regulator.

        8. **Illustrative Scenarios**
        Provide 3–5 example scenarios in table format showing how different loans or overdrafts are reported:

        | Scenario Description                          | Included in Report? | Notes                                  |
        |----------------------------------------------|----------------------|----------------------------------------|
        | ₹15M working capital loan to prime customer  | Yes                  | Meets threshold and duration criteria |
        | Government-backed SME loan                   | No                   | Excluded due to subsidy                |
        | Overdraft converted to loan after 2 months   | Yes                  | Treated as new eligible loan           |

        ---

        Ensure that your BRD uses formal business language and abstract regulatory text into functional requirements. The document should be easy to interpret by both business analysts and technical teams.

        ---

        **Regulation Document Summary:**
        {new_summary}
    """
    return call_claude(prompt)

# Example usage
if __name__ == "__main__":
    sample_text = "XYZ Bank must report loans disbursed to prime customers above LKR 10 million."
    sample_context = "In the previous year, XYZ Bank reported only long-term loans to corporate clients."

    print("\n🔍 Summary:")
    summary = get_summary_with_context(sample_text, sample_context)
    print(summary)

    print("\n🔗 Entity Relationships (JSON):")
    entity_json = get_entity_relationship_with_context(summary, sample_context)
    print(entity_json)

    print("\n📄 Generated KOP Document:")
    kop_doc = get_kop_doc(summary, entity_json)
    print(kop_doc)