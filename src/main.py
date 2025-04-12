import os
from dotenv import load_dotenv
from portia import Portia, Config, default_config
from portia.plan import Plan, Step, PlanContext
from .tools.subgraph_tool import SubgraphQueryTool
from .tools.metric_tool import MetricCalculatorTool
from .tools.chart_tool import ChartGeneratorTool
import json
from datetime import datetime
import re
import uuid

# Load environment variables
load_dotenv()

def get_portia_instance():
    # Create a config with additional data
    my_config = default_config(
        llm_provider="OPENAI",
        llm_model_name="gpt-4",
        additional_data={
            "SUBGRAPH_ENDPOINT": os.getenv("GRAPHQL_ENDPOINT"),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "LOGFIRE_TOKEN": os.getenv("LOGFIRE_TOKEN")
        }
    )
    
    # Make an array of your custom tools
    custom_tools = [
        SubgraphQueryTool(), 
        MetricCalculatorTool(), 
        ChartGeneratorTool()
    ]

    # Create the portia instance
    return Portia(config=my_config, tools=custom_tools)

def create_liquidity_plan(query_text: str):
    # Generate unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = f"query_results_{timestamp}.csv"
    
    # Define the steps for the plan
    steps = [
        Step(
            task="Fetch data from subgraph",
            tool_id="subgraph_query_tool",
            inputs={
                "gql_query": "{{query}}",  # Will be replaced with actual query
                "output_file": csv_file
            },
            output="$raw_data"
        ),
        Step(
            task="Calculate metrics from the data",
            tool_id="metric_calculator_tool",
            inputs={
                "code": "{{metric_code}}",  # Will be replaced with actual code
                "csv_file": csv_file
            },
            output="$metrics"
        ),
        Step(
            task="Generate charts from metrics",
            tool_id="chart_generator_tool",
            inputs={
                "code": "{{chart_code}}",  # Will be replaced with actual code
                "csv_file": csv_file,
                "output_prefix": f"chart_{timestamp}"
            },
            output="$charts"
        )
    ]
    
    # Create the plan context
    context = PlanContext(
        query=query_text,
        variables={
            "query": "",  # Will be filled by Portia
            "metric_code": "",  # Will be filled by Portia
            "chart_code": ""  # Will be filled by Portia
        }
    )
    
    # Create and return the plan
    return Plan(steps=steps, context=context)

def run_pipeline(query_text: str):
    """
    Run the Portia pipeline to process a user query.
    
    Args:
        query_text (str): The user's query text
        
    Returns:
        dict: A dictionary containing:
            - markdown_report: The markdown report text
            - pdf_path: Path to the generated PDF
            - html_path: List of paths to generated HTML files
            - png_path: List of paths to generated PNG files
    """
    try:
        # Get Portia instance
        portia = get_portia_instance()
        
        # Create the plan
        plan = create_liquidity_plan(query_text)
        
        # Execute the plan
        result = portia.execute(plan)
        
        # Generate unique filenames for output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_id = str(uuid.uuid4())[:8]
        
        # Create markdown report
        markdown_report = f"""# Liquidity Analysis Report
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Query
{query_text}

## Metrics
{result.get('$metrics', 'No metrics available')}

## Charts
{result.get('$charts', 'No charts available')}
"""
        
        # Save markdown report
        report_filename = f"report_{timestamp}_{report_id}.md"
        with open(report_filename, "w") as f:
            f.write(markdown_report)
        
        # Generate PDF path
        pdf_path = report_filename.replace(".md", ".pdf")
        
        # Get chart paths
        html_paths = []
        png_paths = []
        
        # Look for generated chart files
        for file in os.listdir():
            if file.startswith(f"chart_{timestamp}"):
                if file.endswith(".html"):
                    html_paths.append(file)
                elif file.endswith(".png"):
                    png_paths.append(file)
        
        return {
            "markdown_report": markdown_report,
            "pdf_path": pdf_path,
            "html_path": html_paths,
            "png_path": png_paths
        }
        
    except Exception as e:
        # Log the error
        print(f"Error in pipeline execution: {str(e)}")
        raise

if __name__ == "__main__":
    out = run_pipeline("What is the liquidity for DAI in the last 24 hours, and show me a chart of top volumes")
    print("Final output from pipeline:", out) 