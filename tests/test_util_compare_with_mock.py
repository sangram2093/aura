import pytest
from unittest.mock import patch
from utils import parse_graph_data, compare_graphs


# @pytest.fixture
# def mock_parse_graph_data():
#     with patch("utils.parse_graph_data") as mock:
#         yield mock

new_graph_str ="""
{
  "edges": [
    {
      "from": "E1",
      "label": "submits",
      "title": "Verb: submits Optionality: Conditional Condition: Deutsche Bank granted no qualifying facilities during reporting week Property: Nil report indicating no qualifying transactions Thresholds: No qualifying loans above Rs. 15 million or Rs. 1 million Frequency: weekly when no qualifying loans exist",
      "to": "E4"
    },
    {
      "from": "E1",
      "label": "provides",
      "title": "Verb: provides Optionality: Conditional Condition: Central Bank requests prime customer lists Property: Updated list of prime customers with internal ratings Thresholds: No specific threshold Frequency: periodically upon Central Bank request",
      "to": "E3"
    },
    {
      "from": "E1",
      "label": "reports",
      "title": "Verb: reports Optionality: Conditional Condition: Deutsche Bank granted qualifying loans to prime customers during reporting week Property: Short-term loans and advances (6 months or less) to prime customers in domestic rupees Thresholds: Above Rs. 15 million (primary) or Rs. 1 million (secondary) Frequency: weekly for loans granted Friday to Thursday",
      "to": "E7"
    },
    {
      "from": "E1",
      "label": "maintains",
      "title": "Verb: maintains Optionality: Mandatory Condition: Deutsche Bank participates in AWPR reporting Property: Documented records (electronic or manual) of AWPR submissions with authorized signatory Thresholds: All AWPR-related transactions and submissions Frequency: continuously maintained",
      "to": "E6"
    },
    {
      "from": "E1",
      "label": "reports",
      "title": "Verb: reports Optionality: Conditional Condition: Deutsche Bank has overdraft utilization changes or rate changes during reporting week Property: Maximum utilized amount during week or utilization difference exceeding threshold Thresholds: Rs. 15 million for utilization differences (Rs. 1 million under secondary conditions) Frequency: weekly for overdrafts with qualifying changes",
      "to": "E8"
    },
    {
      "from": "E1",
      "label": "excludes",
      "title": "Verb: excludes Optionality: Mandatory Condition: Deutsche Bank grants loans to government sector or under formal subsidized schemes Property: Credit to government, refinance loans, widely available subsidized schemes Thresholds: All government sector and formal subsidized scheme loans regardless of amount Frequency: continuously applied to all reporting",
      "to": "E5"
    }
  ],
  "nodes": [
    {
      "group": "organization",
      "id": "E1",
      "label": "Deutsche Bank (LCB)"
    },
    {
      "group": "organization",
      "id": "E2",
      "label": "Central Bank of Sri Lanka"
    },
    {
      "group": "document",
      "id": "E3",
      "label": "Prime Customer List"
    },
    {
      "group": "document",
      "id": "E4",
      "label": "AWPR Report"
    },
    {
      "group": "financial_instrument",
      "id": "E5",
      "label": "Short-term Loans to Prime Customers"
    },
    {
      "group": "document",
      "id": "E6",
      "label": "Internal Records"
    },
    {
      "group": "financial_instrument",
      "id": "E7",
      "label": "Ten Lowest Interest Rate Loans"
    },
    {
      "group": "financial_instrument",
      "id": "E8",
      "label": "Overdraft Facilities"
    }
  ]
}
"""

old_graph_str = """
{
  "edges": [
    {
      "from": "E1",
      "label": "submits",
      "title": "Verb: submits Optionality: Conditional Condition: Deutsche Bank granted no qualifying facilities during reporting week Property: Nil report indicating no qualifying transactions Thresholds: No qualifying loans above Rs. 10 million or Rs. 1 million Frequency: weekly when no qualifying loans exist",
      "to": "E4"
    },
    {
      "from": "E1",
      "label": "provides",
      "title": "Verb: provides Optionality: Conditional Condition: Central Bank requests prime customer lists Property: Updated list of prime customers with internal ratings Thresholds: No specific threshold Frequency: periodically upon Central Bank request",
      "to": "E3"
    },
    {
      "from": "E1",
      "label": "reports",
      "title": "Verb: reports Optionality: Conditional Condition: Deutsche Bank granted qualifying loans to prime customers during reporting week Property: Short-term loans (3 months or less) to prime customers in domestic rupees Thresholds: Above Rs. 10 million (primary) or Rs. 1 million (secondary) Frequency: weekly for loans granted Friday to Thursday",
      "to": "E7"
    },
    {
      "from": "E1",
      "label": "maintains",
      "title": "Verb: maintains Optionality: Mandatory Condition: Deutsche Bank participates in AWPR reporting Property: Documented records (electronic or manual) of AWPR submissions Thresholds: All AWPR-related transactions and submissions Frequency: continuously maintained",
      "to": "E6"
    }
  ],
  "nodes": [
    {
      "group": "organization",
      "id": "E1",
      "label": "Deutsche Bank (LCB)"
    },
    {
      "group": "organization",
      "id": "E2",
      "label": "Central Bank of Sri Lanka"
    },
    {
      "group": "document",
      "id": "E3",
      "label": "Prime Customer List"
    },
    {
      "group": "document",
      "id": "E4",
      "label": "AWPR Report"
    },
    {
      "group": "financial_instrument",
      "id": "E5",
      "label": "Short-term Loans to Prime Customers"
    },
    {
      "group": "document",
      "id": "E6",
      "label": "Internal Records"
    },
    {
      "group": "financial_instrument",
      "id": "E7",
      "label": "Ten Lowest Interest Rate Loans"
    }
  ]
}
"""
def test_compare_graphs():
    
    # Mock the behavior of parse_graph_data
    #mock_parse_graph_data.side_effect = lambda graph: {"parsed": graph}  # Example parsed output
    old_graph = parse_graph_data(old_graph_str)
    new_graph = parse_graph_data(new_graph_str)
    # Act
    result = compare_graphs(old_graph, old_graph)
    assert len(result[0])==0  # Replace with actual expected result
    # Act
    result = compare_graphs(old_graph, new_graph)

    print(f" Results are {result[0]}")

    assert len(result[0]) == 0  # Replace with actual expected result
    # Add more assertions based on the expected behavior of `compare`