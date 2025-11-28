import pytest
from unittest.mock import patch
from anthropic_llm import call_claude

# Assuming the function you want to test is named `generate_summary`
from anthropic_llm import get_summary_with_context

@pytest.fixture
def mock_call_claude():
    with patch("anthropic_llm.call_claude") as mock:
        yield mock

def test_generate_summary(mock_call_claude):
    # Arrange
    mock_call_claude.return_value = "Mocked LLM Response"
    input_text = "This is a test regulation document."

    # Act
    result = get_summary_with_context(input_text)

    # Assert
    mock_call_claude.assert_called_once()  # Ensure the LLM call was made
    assert result == "Mocked LLM Response"  # Check the mocked response is returned