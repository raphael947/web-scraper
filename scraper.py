# scraper.py

import json
from typing import List, Dict, Any
from assets import OPENAI_MODEL_FULLNAME, GEMINI_MODEL_FULLNAME
from llm_calls import call_llm_model
from markdown import read_raw_data
from api_management import get_supabase_client

supabase = get_supabase_client()

def save_formatted_data(unique_name: str, formatted_data):
    if isinstance(formatted_data, str):
        try:
            data_json = json.loads(formatted_data)
        except json.JSONDecodeError:
            data_json = {"raw_text": formatted_data}
    elif hasattr(formatted_data, "dict"):
        data_json = formatted_data.dict()
    else:
        data_json = formatted_data

    supabase.table("scraped_data").update({
        "formatted_data": data_json
    }).eq("unique_name", unique_name).execute()
    MAGENTA = "\033[35m"
    RESET = "\033[0m"  # Reset color to default
    print(f"{MAGENTA}INFO:Scraped data saved for {unique_name}{RESET}")

def generate_extraction_prompt(user_prompt: str) -> str:
    """Generate a system message for the extraction task."""
    return f"""You are a web content extraction assistant. Your task is to:

1. Analyze the provided webpage content
2. {user_prompt}
3. Extract ALL instances of the requested information
4. For each instance found, extract ALL the fields specified in the prompt
5. Return the extracted information in a structured JSON format that can be easily converted to CSV
6. If no relevant information is found, return an empty array

Format your response as a JSON object with this structure:
{{
    "extracted_data": [
        {{
            "field1": "value1",
            "field2": "value2",
            "field3": "value3",
            ...
        }},
        {{
            "field1": "value1",
            "field2": "value2",
            "field3": "value3",
            ...
        }},
        ...
    ]
}}

Important:
- Extract ALL instances that match the criteria
- Include ALL fields mentioned in the prompt for each instance
- Make sure each instance has the same fields/structure
- Use consistent field names across all instances
- If a field is not found, use "N/A" instead of leaving it empty"""

def scrape_urls(unique_names: List[str], extraction_prompts: List[str], selected_model: str) -> tuple[int, int, float, List[Dict[str, Any]]]:
    """
    For each unique_name:
      1) read raw_data from supabase
      2) extract content based on the prompt using selected LLM
      3) save formatted_data
      4) accumulate cost
    Return total usage + list of extracted data
    """
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost = 0
    extraction_results = []

    # Use the first prompt if multiple are provided (though we expect just one)
    extraction_prompt = extraction_prompts[0] if extraction_prompts else "Extract all relevant information from the webpage"
    system_message = generate_extraction_prompt(extraction_prompt)

    for uniq in unique_names:
        raw_data = read_raw_data(uniq)
        if not raw_data or not raw_data.get("content"):
            BLUE = "\033[34m"
            RESET = "\033[0m"
            print(f"{BLUE}No raw_data found for {uniq}, skipping.{RESET}")
            continue

        content = raw_data["content"]
        url = raw_data.get("url", "")

        # Call LLM with the extraction prompt
        try:
            extracted_data, token_counts, cost = call_llm_model(
                content, 
                None,  # No Pydantic model needed for prompt-based extraction
                selected_model,
                system_message
            )

            # Try to parse the response if it's a string
            if isinstance(extracted_data, str):
                try:
                    extracted_data = json.loads(extracted_data)
                except json.JSONDecodeError:
                    extracted_data = {"extracted_data": [{"content": extracted_data, "metadata": {"location": "unknown", "context": "full text"}}]}

            # Store the results
            save_formatted_data(uniq, extracted_data)

            # Update totals
            total_input_tokens += token_counts["input_tokens"]
            total_output_tokens += token_counts["output_tokens"]
            total_cost += cost

            # Add to results
            extraction_results.append({
                "unique_name": uniq,
                "url": url,
                "extracted_data": extracted_data
            })
        except Exception as e:
            print(f"Error processing {uniq}: {str(e)}")
            continue

    return total_input_tokens, total_output_tokens, total_cost, extraction_results
