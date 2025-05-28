# streamlit_app.py

import streamlit as st
from streamlit_tags import st_tags_sidebar
import pandas as pd
import json
import re
import sys
import asyncio
# ---local imports---
from scraper import scrape_urls
from pagination import paginate_urls
from markdown import fetch_and_store_markdowns
from assets import MODELS_USED
from api_management import get_supabase_client

# Only use WindowsProactorEventLoopPolicy on Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())



# Initialize Streamlit app
st.set_page_config(page_title="Universal Web Scraper", page_icon="🦑")
supabase=get_supabase_client()
if supabase==None:
    st.error("🚨 **Supabase is not configured!** This project requires a Supabase database to function.")
    st.warning("Follow these steps to set it up:")

    st.markdown("""
    1. **[Create a free Supabase account](https://supabase.com/)**.
    2. **Create a new project** inside Supabase.
    3. **Create a table** in your project by running the following SQL command in the **SQL Editor**:
    
    ```sql
    CREATE TABLE IF NOT EXISTS scraped_data (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unique_name TEXT NOT NULL,
    url TEXT,
    raw_data JSONB,        
    formatted_data JSONB, 
    pagination_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
    );
    ```

    4. **Go to Project Settings → API** and copy:
        - **Supabase URL**
        - **Anon Key**
    
    5. **Update your `.env` file** with these values:
    
    ```
    SUPABASE_URL=your_supabase_url_here
    SUPABASE_ANON_KEY=your_supabase_anon_key_here
    ```

    6. **Restart the project** close everything and reopen it, and you're good to go! 🚀
    """)
    st.stop()

st.title("🦑 Universal Web Scraper")
st.markdown("""
Extract structured data from any website using AI. Just provide:
1. The URL(s) you want to scrape
2. What you want to extract
3. Choose your preferred AI model
""")

# Initialize session state variables
if 'scraping_state' not in st.session_state:
    st.session_state['scraping_state'] = 'idle'  # Possible states: 'idle', 'waiting', 'scraping', 'completed'
if 'results' not in st.session_state:
    st.session_state['results'] = None
if 'driver' not in st.session_state:
    st.session_state['driver'] = None

# Sidebar components
st.sidebar.title("Web Scraper Settings")

# API Keys
with st.sidebar.expander("API Keys", expanded=False):
    # Loop over every model in MODELS_USED
    for model, required_keys in MODELS_USED.items():
        # required_keys is a set (e.g. {"GEMINI_API_KEY"})
        for key_name in required_keys:
            # Create a password-type text input for each API key
            st.text_input(key_name,type="password",key=key_name)
    st.session_state['SUPABASE_ANON_KEY'] = st.text_input("SUPABASE ANON KEY", type="password")

# Model selection
model_selection = st.sidebar.selectbox(
    "Select Model", 
    options=list(MODELS_USED.keys()), 
    index=0,
    help="Suggested models:\n- gpt-4o-mini: Standard model for complex extractions and understanding context\n- gemini-1.5-flash: Fast and efficient for straightforward extractions"
)
st.sidebar.markdown("---")
st.sidebar.write("## URL Input Section")
# Ensure the session state for our URL list exists
if "urls_splitted" not in st.session_state:
    st.session_state["urls_splitted"] = []

with st.sidebar.container():
    col1, col2 = st.columns([3, 1], gap="small")
    
    with col1:
        # A text area to paste multiple URLs at once
        if "text_temp" not in st.session_state:
            st.session_state["text_temp"] = ""

        url_text = st.text_area("Enter one or more URLs (space/tab/newline separated):",st.session_state["text_temp"], key="url_text_input", height=68)

    with col2:
        if st.button("Add URLs"):
            if url_text.strip():
                new_urls = re.split(r"\s+", url_text.strip())
                new_urls = [u for u in new_urls if u]
                st.session_state["urls_splitted"].extend(new_urls)
                st.session_state["text_temp"] = ""
                st.rerun()
        if st.button("Clear URLs"):
            st.session_state["urls_splitted"] = []
            st.rerun()

    # Show the URLs in an expander, each as a styled "bubble"
    with st.expander("Added URLs", expanded=True):
        if st.session_state["urls_splitted"]:
            bubble_html = ""
            for url in st.session_state["urls_splitted"]:
                bubble_html += (
                    f"<span style='"
                    f"background-color: #E6F9F3;"  # Very Light Mint for contrast
                    f"color: #0074D9;"            # Bright Blue for link-like appearance
                    f"border-radius: 15px;"       # Slightly larger radius for smoother edges
                    f"padding: 8px 12px;"         # Increased padding for better spacing
                    f"margin: 5px;"               # Space between bubbles
                    f"display: inline-block;"     # Ensures proper alignment
                    f"text-decoration: none;"     # Removes underline if URLs are clickable
                    f"font-weight: bold;"         # Makes text stand out
                    f"font-family: Arial, sans-serif;"  # Clean and modern font
                    f"box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);'"  # Subtle shadow for depth
                    f">{url}</span>"
                )
            st.markdown(bubble_html, unsafe_allow_html=True)
        else:
            st.write("No URLs added yet.")

st.sidebar.markdown("---")

# Extraction prompt
show_extraction = st.sidebar.toggle("Enable Extraction")
extraction_prompt = ""
if show_extraction:
    extraction_prompt = st.sidebar.text_area(
        'Enter your extraction prompt:',
        placeholder="Example: Extract all advertisements from the webpage, including their titles, descriptions, prices, and any relevant metadata.",
        help="Describe in detail what information you want to extract from the webpages."
    )

st.sidebar.markdown("---")

use_pagination = st.sidebar.toggle("Enable Pagination")
pagination_details = ""
if use_pagination:
    pagination_details = st.sidebar.text_input("Enter Pagination Details (optional)",help="Describe how to navigate through pages (e.g., 'Next' button class, URL pattern)")

st.sidebar.markdown("---")

# Main action button
if st.sidebar.button("LAUNCH", type="primary"):
    if st.session_state["urls_splitted"] == []:
        st.error("Please enter at least one URL.")
    elif show_extraction and not extraction_prompt.strip():
        st.error("Please enter an extraction prompt.")
    else:
        # Save user choices
        st.session_state['urls'] = st.session_state["urls_splitted"]
        st.session_state['extraction_prompt'] = extraction_prompt
        st.session_state['model_selection'] = model_selection
        st.session_state['use_pagination'] = use_pagination
        st.session_state['pagination_details'] = pagination_details
        
        # fetch or reuse the markdown for each URL
        unique_names = fetch_and_store_markdowns(st.session_state["urls_splitted"])
        st.session_state["unique_names"] = unique_names

        # Move on to "scraping" step
        st.session_state['scraping_state'] = 'scraping'

if st.session_state['scraping_state'] == 'scraping':
    try:
        with st.spinner("Processing..."):
            unique_names = st.session_state["unique_names"]  # from the LAUNCH step

            total_input_tokens = 0
            total_output_tokens = 0
            total_cost = 0
            
            # 1) Scraping logic
            all_data = []
            if show_extraction:
                in_tokens_s, out_tokens_s, cost_s, parsed_data = scrape_urls(
                    unique_names,
                    [st.session_state['extraction_prompt']],  # Pass the prompt as a single field
                    st.session_state['model_selection']
                )
                total_input_tokens += in_tokens_s
                total_output_tokens += out_tokens_s
                total_cost += cost_s

                # Store or display parsed data 
                all_data = parsed_data
                st.session_state['in_tokens_s'] = in_tokens_s
                st.session_state['out_tokens_s'] = out_tokens_s
                st.session_state['cost_s'] = cost_s

            # 2) Pagination logic
            pagination_info = None
            if st.session_state['use_pagination']:
                in_tokens_p, out_tokens_p, cost_p, page_results = paginate_urls(
                    unique_names,
                    st.session_state['model_selection'],
                    st.session_state['pagination_details'],
                    st.session_state["urls_splitted"]
                )
                total_input_tokens += in_tokens_p
                total_output_tokens += out_tokens_p
                total_cost += cost_p

                pagination_info = page_results
                st.session_state['in_tokens_p'] = in_tokens_p
                st.session_state['out_tokens_p'] = out_tokens_p
                st.session_state['cost_p'] = cost_p

            # 3) Save everything in session state
            st.session_state['results'] = {
                'data': all_data,
                'input_tokens': total_input_tokens,
                'output_tokens': total_output_tokens,
                'total_cost': total_cost,
                'pagination_info': pagination_info
            }
            st.session_state['scraping_state'] = 'completed'
    except Exception as e:
        st.error(f"An error occurred during scraping: {e}")
        st.session_state['scraping_state'] = 'idle'

# Display results
if st.session_state['scraping_state'] == 'completed' and st.session_state['results']:
    results = st.session_state['results']
    all_data = results['data']
    total_input_tokens = results['input_tokens']
    total_output_tokens = results['output_tokens']
    total_cost = results['total_cost']
    pagination_info = results['pagination_info']

    if show_extraction:
        st.subheader("Extraction Results")
        
        # Display the results in a more structured way
        if all_data:
            # Convert the data to a DataFrame for better display
            processed_data = []
            for url_data in all_data:
                url = url_data.get('url', 'N/A')
                extracted = url_data.get('extracted_data', {})
                print("extracted:", extracted)
                
                # Handle the extracted data directly
                if isinstance(extracted, dict) and 'extracted_data' in extracted:
                    items = extracted['extracted_data']
                    print("items:", items)
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                row = {'Source URL': url}
                                row.update(item)
                                processed_data.append(row)
                else:
                    print("No valid extracted_data found for:", url)
                
            if processed_data:
                # Dynamically create DataFrame from processed data
                df = pd.DataFrame(processed_data)

                # Optional: move 'Source URL' to the front if it exists
                if 'Source URL' in df.columns:
                    cols = ['Source URL'] + [col for col in df.columns if col != 'Source URL']
                    df = df[cols]
                
                # Create download buttons in a more prominent location
                st.markdown("### Download Options")
                col1, col2 = st.columns(2)
                with col1:
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        "📥 Download as CSV",
                        csv_data,
                        "scraped_data.csv",
                        "text/csv",
                        key='download-csv',
                        help="Download the extracted data in CSV format"
                    )
                with col2:
                    st.download_button(
                        "📥 Download as JSON",
                        df.to_json(orient="records"),
                        "scraped_data.json",
                        "application/json",
                        key='download-json',
                        help="Download the extracted data in JSON format"
                    )
                
                # Display the data in a table format with improved visibility
                st.markdown("### Data Preview")
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Show data statistics
                st.markdown("### Dataset Statistics")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Rows", len(df))
                with col2:
                    st.metric("Total Columns", len(df.columns))
            else:
                st.warning("No structured data was extracted from the content. Please check your extraction prompt and try again.")

        # Display token usage and cost information
        st.subheader("Processing Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Input Tokens", f"{total_input_tokens:,}")
        with col2:
            st.metric("Output Tokens", f"{total_output_tokens:,}")
        with col3:
            st.metric("Total Cost", f"${total_cost:.4f}")

    if pagination_info:
        st.subheader("Pagination Information")
        st.json(pagination_info)

