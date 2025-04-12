import streamlit as st
import json
from pathlib import Path
import base64
from PIL import Image
import os
from agent_module import run_agent, agent_response
import asyncio
import nest_asyncio
import uuid
import re
from datetime import datetime
from typing import Annotated, List, Optional, Tuple
from markdown_pdf import MarkdownPdf, Section
import streamlit.components.v1 as components
import pandas as pd
import json
import ast
from io import BytesIO
import plotly.io as pio
from portia import (
    Portia,
    example_tool_registry,
)
from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext
from portia import InMemoryToolRegistry
from tool_lib import QueryRunner
import json
import ast
pio.templates["custom"] = pio.templates["seaborn"]
pio.templates.default = "custom"
pio.templates["custom"].layout.autosize = True


# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize session state
if "file_hashes" not in st.session_state:
    st.session_state.file_hashes = {}
    


def convert_to_agent_response(json_str: str) -> agent_response:
    """
    Convert JSON string output from Portia to agent_response BaseModel
    
    Args:
        json_str: JSON string containing the Portia output
        
    Returns:
        agent_response: Populated agent_response BaseModel object
    """
    # Parse the JSON string
    data = json.loads(json_str)
    
    # Extract the 'value' from 'final_output'
    final_output_str = data['outputs']['final_output']['value']
    
    # Convert the string representation of dictionary to actual dictionary
    response_dict = ast.literal_eval(final_output_str)
    
    # Create and return agent_response object
    return agent_response(
        markdown_report=response_dict['markdown_report'],
        csv_path=response_dict['csv_path'],
        metrics_dict=response_dict['metrics_dict'],
        html_path=response_dict['html_path'],
        png_path=response_dict['png_path'],
        pdf_path=response_dict['pdf_path'],
        enso_route=response_dict['enso_route'],
        enso_route_file=response_dict['enso_route_file']
    )

@st.cache_data
def get_base64_image_src(img_path):
    """Caches and returns base64 encoded image source."""
    try:
        with open(img_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{img_data}" # Assuming png, adjust if needed
    except Exception as e:
        st.warning(f"Error loading document: {e}")
        return img_path
    

@st.cache_data
def get_resized_base64_image_src(img_path, max_width=1000, max_height=800):
    """Caches, resizes, and returns base64 encoded image source."""
    try:
        img = Image.open(img_path)
        img.thumbnail((max_width, max_height))  # Resize in place, aspect ratio preserved

        buffered = BytesIO()
        img.save(buffered, format="JPEG", optimize=True) # Use JPEG, optimize for size
        img_data = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_data}" # Changed to image/jpeg
    except Exception as e:
        st.warning(f"Error loading or resizing image: {e}")
        return get_base64_image_src(img_path)

@st.cache_data
def write_markdown_to_file(content: Annotated[str, "The markdown content to write"], 
                        filename: Annotated[str, "The name of the file (with or without .md extension)"] = "blog.md") -> str:
    """
    Write markdown content to a file with .md extension and create PDF with appended images.
    Uses Streamlit caching to prevent redundant file operations.
    """
    try:
        # Ensure filename has .md extension
        md_filename = filename.replace('.pdf', '.md') if filename.endswith('.pdf') else filename
        pdf_filename = filename.replace('.md', '.pdf')



        # Write markdown content
        with open(md_filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Create PDF
        pdf = MarkdownPdf()
        pdf.add_section(Section(content, toc=False))
        pdf.save(pdf_filename)
        
        return f"File {filename} has been created successfully."
        
    except Exception as e:
        st.error(f"Error writing file: {str(e)}")
        return f"Error creating file {filename}: {str(e)}"


FIXED_CONTAINER_CSS = """
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)){{
    background-color: transparent;
    position: {mode};
    width: inherit;
    background-color: inherit;
    {position}: {margin};
    z-index: 999;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)) div[data-testid="stVerticalBlock"]:has(div.fixed-container-{id}):not(:has(div.not-fixed-container)) > div[data-testid="element-container"] {{
    display: none;
}}
div[data-testid="stVerticalBlockBorderWrapper"]:has(div.not-fixed-container):not(:has(div[class^='fixed-container-'])) {{
    display: none;
}}
""".strip()

MARGINS = {
    "top": "2.875rem",
    "bottom": "60px",
}

def st_fixed_container(
    *,
    height = None,
    border = None,
    mode = "fixed",
    position = "top",
    margin = None,
    key = None,
):
    if margin is None:
        margin = MARGINS[position]
    global fixed_counter
    fixed_container = st.container()
    non_fixed_container = st.container()
    css = FIXED_CONTAINER_CSS.format(
        mode=mode,
        position=position,
        margin=margin,
        id=key,
    )
    with fixed_container:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='fixed-container-{key}'></div>",
            unsafe_allow_html=True,
        )
    with non_fixed_container:
        st.markdown(
            f"<div class='not-fixed-container'></div>",
            unsafe_allow_html=True,
        )

    with fixed_container:
        return st.container(height=height, border=border)


def download_button(object_to_download, download_filename, button_text):

    with st.spinner("Generating PDF..."):
        write_markdown_to_file(object_to_download, download_filename)

    with open(download_filename.replace("assets", ""), "rb") as pdf_file:
        pdf_bytes = pdf_file.read()

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    b64 = base64.b64encode(pdf_bytes).decode()

    custom_css = f""" 
        <style>
            #{button_id} {{
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: 0.25em 0.38em;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    dl_link = custom_css + f'<a download="{download_filename.replace("assets", "")}" id="{button_id}" href="data:file/txt;base64,{b64}">{button_text}</a><br></br>'

    return dl_link

# Cache the file loader
@st.cache_data
def load_image(image_path):
    try:
        return Image.open(image_path)
    except Exception as e:
        st.error(f"Error loading image: {e}")
        return None

@st.cache_data
def load_pdf_as_base64(pdf_path):
    try:
        with open(pdf_path.replace("assets", ""), "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        st.error(f"Error loading PDF: {e}")
        return None


# Create a new event loop for async operations
def get_agent_response(user_query):
    try:
        # Create a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the agent in the new event loop
        response = run_agent(user_query)
        
        # Close the loop
        loop.close()
        
        return response
    except Exception as e:
        st.error(f"Error in agent response: {str(e)}")
        return None

def set_page_config():
    """Configure the page with logo and custom styling"""
    st.set_page_config(
        page_title="Pool-Sweeper Agent",
        page_icon="📊",
        layout="wide"
    )
    
    # Add custom CSS for the logo and header
    st.markdown("""
        <style>
        /* Hide default Streamlit header */
        header[data-testid="stHeader"] {
            display: none;
        }
        
        /* Remove default margins and padding */
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
        }
        
        [data-testid="stAppViewContainer"] {
            padding-top: 0 !important;
            overflow: hidden !important;
        }

        section[data-testid="stSidebar"] {
            margin-top: 90px !important;
        }
        
        /* Frosted glass header */
        .logo-container {
            position: fixed;
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1.5rem 3rem;
            background: rgba(255, 255, 255, 0.7) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            margin: 0;
            width: 100vw;
            height: 90px;
            left: 50%;
            right: 50%;
            margin-left: -50vw;
            margin-right: -50vw;
            border-bottom: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            top: 0;
            z-index: 1000;
        }
        
        /* Left section with Agusto logo and title */
        .left-section {
            display: flex;
            align-items: center;
        }
        
        .agusto-logo {
            height: 60px;
            margin-right: 20px;
            object-fit: contain;
        }
        
        /* Right section with Vizyx logo and powered by text */
        .right-section {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            justify-content: center;
        }
        
        .vizyx-logo {
            height: 40px;
            object-fit: contain;
            margin-bottom: 4px;
        }
        
        .powered-by {
            color: #666;
            font-size: 12px;
            margin: 0;
            padding: 0;
        }

        /* Frosted glass footer */
        .footer-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            padding: 1rem 1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 -4px 30px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .footer-text {
            color: rgba(0, 0, 0, 0.7);
            font-size: 0.8rem;
        }

        /* Adjust main content to account for footer */
        .main-content {
            padding-top: 90px !important;
            padding-bottom: 60px !important;
            margin-top: 0 !important;
        }

        /* Prevent horizontal scroll */
        body {
            overflow-x: hidden !important;
        }

        .title-container {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 2px;  /* Reduced spacing between title and subtitle */
        }
        
        .main-title {
            color: #2a1f5f;
            font-size: 24px;
            margin: 0;
            padding: 0;
            font-weight: bold;
            line-height: 1;  /* Reduced line height */
        }
        
        .sub-title {
            color: #4f4f4f;
            font-size: 16px;
            margin: 2px 0 0 0;  /* Reduced top margin */
            padding: 0;
            line-height: 1;  /* Reduced line height */
        }

        /* Gradient background for the entire app */
        .stApp {
            background: linear-gradient(135deg, 
                #f5f7fa 10%, 
                #e8edf5 35%, 
                #e0e9f0 60%, 
                #d8e5eb 85%, 
                #d0e1e6 100%) !important;
            background-attachment: fixed !important;
        }

        /* Make main content area transparent to show gradient */
        [data-testid="stAppViewContainer"] {
            background: transparent !important;
        }

        /* Chat message styling with semi-transparent background */
        [data-testid="stChatMessage"] {
            border: 1px solid rgba(220, 220, 220, 0.8);
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
            background-color: rgba(255, 255, 255, 0.7) !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* Style user messages */
        [data-testid="stChatMessage"][data-testid="user"] {
            border-left: 4px solid #0066cc;
            background-color: rgba(255, 255, 255, 0.7) !important;
        }

        /* Style assistant messages */
        [data-testid="stChatMessage"][data-testid="assistant"] {
            border-left: 4px solid #00cc88;
            background-color: rgba(255, 255, 255, 0.7) !important;
            margin-top: 0.5rem; /* Reduced top margin by 50% */
        }

        /* Style columns inside chat messages */
        [data-testid="stChatMessage"] > div > div > div > div[data-testid="column"] {
            background-color: rgba(250, 250, 250, 0.3) !important;
            padding: 1rem;
            border-radius: 8px;
        }

        /* Style metrics section */
        [data-testid="stChatMessage"] .stMetric {
            background-color: rgba(255, 255, 255, 0.7) !important;
            padding: 0.5rem;
            border-radius: 5px;
            border: 1px solid rgba(240, 240, 240, 0.5);
        }

        /* Style document preview section */
        [data-testid="stChatMessage"] img {
            border: 1px solid rgba(0, 0, 0, 0.5);
            border-radius: 10px;
        }

        /* Style sidebar with gradient */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, 
                rgba(255, 255, 255, 0.9) 0%, 
                rgba(255, 255, 255, 0.8) 100%) !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        /* Keep header solid */
        .logo-container {
            background-color: white !important;
            border-bottom: 1px solid rgba(229, 229, 229, 0.5);
        }

        /* Style chat input container */
        .stChatInputContainer {
            background-color: rgba(255, 0, 0, 1) !important;
            border-radius: 10px;
            padding: 1rem;
            backdrop-filter: blur(5px);
            -webkit-backdrop-filter: blur(5px);
        }

        /* Add spacing between sections */
        [data-testid="stChatMessage"] .stMarkdown {
            margin-bottom: 1rem;
        }

        /* Ensure text remains readable */
        .stMarkdown {
            color: #1f1f1f !important;
        }

        /* Enhanced frosted glass effect for both header and footer */
        .glass-effect {
            background: rgba(255, 255, 255, 0.7) !important;
            backdrop-filter: blur(10px) saturate(100%) !important;
            -webkit-backdrop-filter: blur(10px) saturate(100%) !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1) !important;
        }

        /* Footer styling */
        .footer-content {
            position: fixed !important;
            bottom: 15px !important;
            left: 0 !important;
            right: 0 !important;
            height: 30px !important;
            display: flex !important;
            justify-content: space-between !important;
            align-items: center !important;
            padding: 0.3rem 3rem !important;
            font-size: 0.75rem !important;
            color: rgba(0, 0, 0, 0.6) !important;
            z-index: 998 !important;
            background: none !important;
        }

        /* Style the chat input container */
        .stChatInputContainer {
            padding: 10px;
        }
        
        /* Style the chat input box */
        .stChatInput {
            border: 1px solid grey !important;
            border-radius: 8px !important;
        }
        
        /* Style the chat input when focused */
        .stChatInput:focus {
            border: 1px solid grey !important;
            box-shadow: none !important;
        }
        </style>
    """, unsafe_allow_html=True)

def get_base64_encoded_image(image_path):
    """Get base64 encoded image"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

def main():
    # Set page configuration and styling
    set_page_config()
    
    # Display header with both logos
    pool_sweeper_logo_path = "assets/logo.png"
    
    # Header HTML
    header_html = f"""
        <div class="logo-container glass-effect">
            <div class="left-section">
                <img src="data:image/png;base64,{get_base64_encoded_image(pool_sweeper_logo_path)}" alt="Pool-Sweeper Logo" class="agusto-logo"/>
                <div class="title-container">
                    <h2 class="main-title">Pool-Sweeper Agent</h2>
                    <p class="sub-title">AI-Powered Liquidity Analysis</p>
                </div>
            </div>
        </div>
        <div class="main-content">
    """

    # Footer HTML
    footer_html = f"""
        <div class="footer-content">
            <span>© {datetime.now().year} By Buffer Overflow. For demonstration purposes only.</span>
        </div>
    """

    # Display header and footer
    st.markdown(header_html, unsafe_allow_html=True)
    
    # Initialize session state for chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.title("Pool-Sweeper")
    st.write("Welcome to the Pool-Sweeper - Agent for Liquidity Analysis")
    
    custom_tool_registry = InMemoryToolRegistry.from_local_tools(
    [
        QueryRunner()
    ])

    with st_fixed_container(mode="fixed", position="bottom"):
        st.markdown("""
        <style> 
        .stChatInputContainer > div {
        border-color: grey;
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("""
        <style>
        /* Style the chat input container */
        .stChatInputContainer {
            padding: 10px;
            background: rgba(255, 255, 255, 0.5) !important;
            backdrop-filter: blur(10px) !important;
            -webkit-backdrop-filter: blur(10px) !important;
            border-radius: 8px !important;
        }
        
        /* Style the chat input box */
        .stChatInput {
            border: 1px solid grey !important;
            border-radius: 8px !important;
            background: rgba(255, 255, 255, 0.7) !important;
        }
        
        /* Style the chat input when focused */
        .stChatInput:focus {
            border: 1px solid grey !important;
            box-shadow: none !important;
            background: rgba(255, 255, 255, 0.8) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        user_query = st.chat_input("Enter your query")



    if user_query:
        # Show spinner while processing
        with st.spinner(f"Processing response for: {user_query}..."):
            try:
                # Get response from agent
                portia = Portia(tools=custom_tool_registry)
                plan_run = portia.run(user_query)
                output = plan_run.model_dump_json(indent=2)
                response = convert_to_agent_response(output)
                
                if response:
                    # Validate metrics_dict before adding to history
                    if hasattr(response, 'metrics_dict'):
                        try:
                            # Test parsing of metrics_dict
                            if isinstance(response.metrics_dict, str):
                                json.loads(response.metrics_dict.replace("'", '"'))
                        except json.JSONDecodeError as e:
                            st.warning(f"Invalid metrics format in response: {str(e)}")
                            response.metrics_dict = "{}"  # Set empty metrics if invalid
                    else:
                        st.warning("Response missing metrics_dict attribute")
                        response.metrics_dict = "{}"

                    # Add to chat history (new messages at the beginning)
                    st.session_state.chat_history.insert(0, {
                        "query": user_query,
                        "response": response,
                        "timestamp": datetime.now().isoformat()  # Add timestamp for unique keys
                    })
                    # Trigger rerun to update the UI
                    st.rerun()
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")

    # Display chat history
    for idx, chat in enumerate(st.session_state.chat_history):
        # User message
        with st.chat_message("user"):
            st.write(chat["query"])
        
        # Assistant response
        with st.chat_message("assistant"):
            try:
                # Create two columns: one for content, one for document preview
                # Display markdown report with unique key
                st.markdown(
                    chat["response"].markdown_report.replace("![](assets/Agusto_logo.jpg)", "")
                )
                
                # Add download button for PDF with error handling and unique key
                if chat["response"].pdf_path:
                    st.markdown(
                                download_button(
                                    chat["response"].markdown_report,
                                    chat["response"].pdf_path,
                                    "Download Report PDF",
                                ),
                        unsafe_allow_html=True
                    )

                st.markdown("--------------------------------")
                
                st.markdown("\n\n\n\n\n")
                # Display document preview with error handling
                st.subheader("Data Preview")
                if chat["response"].html_path:
                    try:
                        
                        if chat["response"].html_path:
                            for html_path in chat["response"].html_path:
                                image_paths = html_path
                                try:
                                    try:
                                        # Try UTF-8 first
                                        with open(image_paths, 'r', encoding='utf-8') as file:
                                            html_text = file.read()
                                    except UnicodeDecodeError:
                                        # If UTF-8 fails, try with utf-8-sig (handles BOM)
                                        try:
                                            with open(image_paths, 'r', encoding='utf-8-sig') as file:
                                                html_text = file.read()
                                        except UnicodeDecodeError:
                                            # If that fails too, try with latin-1
                                            with open(image_paths, 'r', encoding='latin-1') as file:
                                                html_text = file.read()
                                    
                                    # Reduced height and added custom CSS to minimize spacing
                                    st.components.v1.html(html_text, width=1000, height=600, scrolling=True)
                                    st.markdown("""
                                        <style>
                                        /* Reduce spacing between HTML components */
                                        iframe {
                                            margin-bottom: -20px !important;
                                            margin-top: -20px !important;
                                        }
                                        </style>
                                    """, unsafe_allow_html=True)
                                except Exception as e:
                                    st.info(f"Error displaying HTML file: {str(e)}")
                                    if chat["response"].png_path:
                                        for png_path in chat["response"].png_path:
                                            image_paths = png_path
                                            st.image(image_paths)
                        elif chat["response"].png_path:
                            image_paths = chat["response"].png_path
                            try:
                                st.image(image_paths)
                            except Exception as e:
                                st.warning("Error displaying image")
                        else:
                            st.info(f"No document preview available")
                    except Exception as e:
                        st.warning(f"Error displaying document preview: {str(e)}")
            
            except Exception as e:
                st.warning(f"""
                Error displaying chat response
                Error type: {type(e).__name__}
                Error details: {str(e)}
                """
                )
            if chat["response"].enso_route != "":
                st.markdown("## Transaction Route")
                st.markdown(f"Enso Route: {chat['response'].enso_route}")
                
        st.markdown("--------------------------------")

    # Display footer at the end
    st.markdown(footer_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
