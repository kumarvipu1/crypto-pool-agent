"""Chart Generator Tool."""

from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from pydantic import BaseModel, Field
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional

class ChartGeneratorInput(BaseModel):
    """Input schema for the chart generator tool."""
    code: str = Field(..., description="The Python code to execute to generate charts")
    csv_file: str = Field(..., description="The path to the CSV file containing the data")
    output_dir: str = Field(..., description="The directory to save the generated charts")
    chart_types: List[str] = Field(default=["html", "png"], description="Types of charts to generate")

class ChartGeneratorOutput(BaseModel):
    """Output schema for the chart generator tool."""
    html_files: List[str] = Field(default=[], description="Paths to generated HTML charts")
    png_files: List[str] = Field(default=[], description="Paths to generated PNG charts")
    error: Optional[str] = Field(None, description="Error message if generation failed")

class ChartGeneratorTool(Tool[ChartGeneratorOutput]):
    """Tool for generating charts from CSV data.
    
    This tool executes Python code to generate interactive and static charts from CSV data.
    It supports multiple output formats (HTML and PNG) and provides proper error handling.
    """
    
    id: str = "chart_generator_tool"
    name: str = "Chart Generator Tool"
    description: str = "Generates charts from CSV data using Plotly"
    args_schema: type[BaseModel] = ChartGeneratorInput
    output_schema: tuple[str, str] = ("ChartGeneratorOutput", "Output containing paths to generated chart files")
    should_summarize: bool = False

    def __init__(self):
        super().__init__()
    
    def run(self, ctx: ToolRunContext, code: str, csv_file: str, output_dir: str, chart_types: List[str] = ["html", "png"]) -> ChartGeneratorOutput:
        """
        Execute Python code to generate charts from CSV data.
        
        Args:
            ctx: The tool run context containing the input parameters
            code: The Python code to execute
            csv_file: Path to the CSV file
            output_dir: Directory to save charts
            chart_types: Types of charts to generate
            
        Returns:
            ChartGeneratorOutput: The paths to generated charts
            
        Raises:
            ToolHardError: If the chart generation fails
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Create a local namespace with required libraries
            local_namespace = {
                'df': df,
                'pd': pd,
                'px': px,
                'go': go,
                'plt': plt,
                'sns': sns,
                'output_dir': output_dir,
                'datetime': datetime
            }
            
            # Execute the code to generate charts
            exec(code, local_namespace)
            
            # Get list of generated files
            html_files = []
            png_files = []
            
            for file in os.listdir(output_dir):
                file_path = os.path.join(output_dir, file)
                if file.endswith('.html'):
                    html_files.append(file_path)
                elif file.endswith('.png'):
                    png_files.append(file_path)
            
            return ChartGeneratorOutput(
                html_files=html_files,
                png_files=png_files
            )
            
        except Exception as e:
            raise ToolHardError(f"Failed to generate charts: {str(e)}") from e 