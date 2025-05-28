"""
This module contains configuration variables and constants
that are used across different parts of the application.
"""


GEMINI_MODEL_FULLNAME="gemini/gemini-1.5-flash"
GEMINI_2_MODEL_FULLNAME="gemini/gemini-2.0-flash-exp"

# Available OpenAI models
OPENAI_MODELS = {
    "gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "description": "Fast and cost-effective model for basic extractions"
    },
    "gpt-4o": {
        "name": "GPT-4o", 
        "description": "Advanced model for complex extractions and superior understanding"
    }
}

# Available Gemini models
GEMINI_MODELS = {
    GEMINI_MODEL_FULLNAME: {
        "name": "Gemini 1.5 Flash",
        "description": "Fast and efficient for straightforward extractions"
    },
    GEMINI_2_MODEL_FULLNAME: {
        "name": "Gemini 2.0 Flash",
        "description": "Latest experimental Gemini model with enhanced capabilities"
    }
}

# Default model (can be overridden by user selection)
OPENAI_MODEL_FULLNAME="gpt-4o-mini"

MODELS_USED = {
    "gpt-4o-mini": {"OPENAI_API_KEY"},
    "gpt-4o": {"OPENAI_API_KEY"},
    GEMINI_MODEL_FULLNAME: {"GEMINI_API_KEY"},
    GEMINI_2_MODEL_FULLNAME: {"GEMINI_API_KEY"},
}

# Timeout settings for web scraping (page_timeout in minutes, others in seconds)
TIMEOUT_SETTINGS = {
    "page_timeout": 2.0,  # minutes - Timeout for page navigation or JS steps
    "delay_before_return_html": 0.1,  # seconds - Additional pause before final HTML capture
    "screenshot_wait_for": 2.0,  # seconds - Extra wait time before taking screenshots
    "scroll_delay": 0.2,  # seconds - Delay between scroll steps for full page scanning
    "mean_delay": 0.1,  # seconds - Base delay between crawls for multiple URLs
    "max_range": 0.3,  # seconds - Maximum range for random delays
}

# Timeout descriptions for UI (only page_timeout will be shown)
TIMEOUT_DESCRIPTIONS = {
    "page_timeout": "Maximum time to wait for page loading and JavaScript execution - increase for slow sites or to capture more dynamic content like ads",
}

NUMBER_SCROLL=2




SYSTEM_MESSAGE = """You are an intelligent text extraction and conversion assistant. Your task is to extract structured information 
                        from the given text and convert it into a pure JSON format. The JSON should contain only the structured data extracted from the text, 
                        with no additional commentary, explanations, or extraneous information. 
                        You could encounter cases where you can't find the data of the fields you have to extract or the data will be in a foreign language.
                        Please process the following text and provide the output in pure JSON format with no words before or after the JSON:"""

USER_MESSAGE = f"Extract the following information from the provided text:\nPage content:\n\n"
        




PROMPT_PAGINATION = """
You are an assistant that extracts pagination URLs from markdown content of websites. 
Your task is to identify and generate a list of pagination URLs based on a detected URL pattern where page numbers increment sequentially. Follow these instructions carefully:

-Identify the Pagination Pattern:
Analyze the provided markdown text to detect URLs that follow a pattern where only a numeric page indicator changes.
If the numbers start from a low value and increment, generate the full sequence of URLs—even if not all numbers are present in the text.

-Construct Complete URLs:
In cases where only part of a URL is provided, combine it with the given base URL (which will appear at the end of this prompt) to form complete URLs.
Ensure that every URL you generate is clickable and leads directly to the intended page.

-Incorporate User Indications:
If additional user instructions about the pagination mechanism are provided at the end of the prompt, use those instructions to refine your URL generation.
Output Format Requirements:

-Strictly output only a valid JSON object with the exact structure below:
""
{
    "page_urls": ["url1", "url2", "url3", ..., "urlN"]
}""


IMPORTANT:

Output only a single valid JSON object with no additional text, markdown formatting, or explanation.
Do not include any extra newlines or spaces before or after the JSON.
The JSON object must exactly match the following schema:
"""
