"""Crypto Pool Analysis Agent."""

from portia import Portia, Config, LogLevel
from portia.tool_registry import ToolRegistry
from portia.execution_context import execution_context
from portia.cli import CLIExecutionHooks
from portia.plan_run import PlanRunState
import os
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
from src.tools.subgraph_tool import SubgraphQueryTool
from src.tools.metric_tool import MetricCalculatorTool
from src.tools.chart_tool import ChartGeneratorTool
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from markdown_pdf import MarkdownPdf, Section

# Load environment variables
load_dotenv()

@dataclass
class AgentState:
    """State for the liquidity analysis agent."""
    user_query: str
    pool_address: Optional[str] = None
    start_time: Optional[int] = None
    end_time: Optional[int] = None
    output_dir: str = ""

class AgentResponse:
    """Response from the liquidity analysis agent."""
    def __init__(
        self,
        markdown_report: str,
        csv_path: str,
        metrics_dict: Dict[str, Any],
        html_paths: List[str],
        png_paths: List[str],
        pdf_path: str
    ):
        self.markdown_report = markdown_report
        self.csv_path = csv_path
        self.metrics_dict = metrics_dict
        self.html_paths = html_paths
        self.png_paths = png_paths
        self.pdf_path = pdf_path

# Initialize tools
tools = [
    SubgraphQueryTool(),
    MetricCalculatorTool(),
    ChartGeneratorTool()
]

# Create tool registry
tool_registry = ToolRegistry(tools)

# Create Portia instance with system prompt
system_prompt = """
You are an analyst for a crypto trading company. Your goal is to analyze liquidity of a crypto token 
and provide users important information relevant to the user query with a detailed report.

You have access to the following tools:
1. subgraph_query: Executes GraphQL queries against crypto pool subgraphs
   - Input: GraphQL query and output file path
   - Output: File path and dataset summary

2. metric_calculator: Calculates metrics from the data
   - Input: Python code and CSV file path
   - Output: Calculated metrics in both table and dictionary format

3. chart_generator: Creates visualizations
   - Input: Python code, CSV file path, and output directory
   - Output: Paths to generated HTML and PNG charts

Follow these steps:
1. Understand the user query and identify required liquidity information
2. Frame a GraphQL query based on the schema
3. Use subgraph_query to fetch data
4. Use metric_calculator to compute relevant metrics
5. Use chart_generator to create visualizations
6. Create a comprehensive markdown report with:
   - Title and date
   - Key metrics and insights
   - Visualizations
   - Disclaimers for inferred information

The report should focus on the specific information requested in the query.
"""

portia = Portia(
    Config.from_default(default_log_level=LogLevel.DEBUG),
    tools=tool_registry,
    execution_hooks=CLIExecutionHooks(),
    system_prompt=system_prompt
)

async def run_agent(user_prompt: str, pool_address: Optional[str] = None,
                   start_time: Optional[int] = None, end_time: Optional[int] = None) -> AgentResponse:
    """
    Run the liquidity analysis agent.
    
    Args:
        user_prompt: The user's query about liquidity analysis
        pool_address: Optional pool address to analyze
        start_time: Optional start time for analysis
        end_time: Optional end time for analysis
        
    Returns:
        AgentResponse: The analysis results
    """
    # Create output directory
    output_dir = os.path.join("output", datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(output_dir, exist_ok=True)
    
    # Create agent state
    deps = AgentState(
        user_query=user_prompt,
        pool_address=pool_address,
        start_time=start_time,
        end_time=end_time,
        output_dir=output_dir
    )
    
    # Run the agent with execution context
    with execution_context(end_user_id="crypto_pool_analyzer", deps=deps):
        # Run the agent with the user's query
        plan_run = portia.run(user_prompt)
        
        # Handle any clarifications
        if plan_run.state == PlanRunState.NEED_CLARIFICATION:
            for clarification in plan_run.get_outstanding_clarifications():
                # Here you would typically prompt the user for clarification
                # For now, we'll just use a default response
                plan_run = portia.resolve_clarification(
                    plan_run=plan_run,
                    clarification=clarification,
                    response="default"
                )
            # Resume execution with clarifications
            plan_run = portia.resume(plan_run)
        
        # Process the results to match the expected AgentResponse format
        result = plan_run.result
        
        # Extract paths and data from the result
        csv_path = result.get("csv_path", "")
        metrics_dict = result.get("metrics", {})
        html_paths = result.get("html_paths", [])
        png_paths = result.get("png_paths", [])
        markdown_report = result.get("markdown_report", "")
        
        # Generate PDF report
        pdf_path = os.path.join(output_dir, "liquidity_analysis.pdf")
        pdf = MarkdownPdf()
        pdf.add_section(Section(markdown_report))
        pdf.save(pdf_path)
        
        # Create and return the AgentResponse
        return AgentResponse(
            markdown_report=markdown_report,
            csv_path=csv_path,
            metrics_dict=metrics_dict,
            html_paths=html_paths,
            png_paths=png_paths,
            pdf_path=pdf_path
        ) 