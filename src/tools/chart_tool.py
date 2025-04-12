from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any

class ChartGeneratorSchema(BaseModel):
    code: str = Field(..., description="The Python code to execute to generate charts")
    csv_file: str = Field(..., description="The path to the CSV file containing the data")
    output_prefix: str = Field(..., description="Prefix for the output files")

class ChartGeneratorTool(Tool):
    def __init__(self):
        super().__init__(
            id="chart_generator_tool",
            name="Chart Generator Tool",
            description="Generates charts from CSV data using Python code",
            parameters={
                "code": {
                    "type": "string",
                    "description": "Python code to generate charts"
                },
                "csv_file": {
                    "type": "string",
                    "description": "Path to the CSV file containing data"
                },
                "output_prefix": {
                    "type": "string",
                    "description": "Prefix for output files (HTML and PNG)"
                }
            }
        )
        
    def execute(self, inputs: Dict[str, Any]) -> str:
        """
        Execute Python code to generate charts from CSV data.
        
        Args:
            inputs (Dict[str, Any]): Dictionary containing:
                - code: Python code to generate charts
                - csv_file: Path to the CSV file
                - output_prefix: Prefix for output files
                
        Returns:
            str: Paths to generated files in markdown format
        """
        try:
            # Read the CSV file
            df = pd.read_csv(inputs["csv_file"])
            
            # Create output directory if it doesn't exist
            os.makedirs("output", exist_ok=True)
            
            # Create a local namespace for code execution
            namespace = {
                "df": df,
                "pd": pd,
                "plt": plt,
                "sns": sns,
                "output_prefix": inputs["output_prefix"]
            }
            
            # Execute the code
            exec(inputs["code"], namespace)
            
            # Get the generated file paths
            html_path = f"output/{inputs['output_prefix']}.html"
            png_path = f"output/{inputs['output_prefix']}.png"
            
            # Format response as markdown
            markdown = "## Generated Charts\n\n"
            markdown += f"### Interactive Chart\n[View Interactive Chart]({html_path})\n\n"
            markdown += f"### Static Chart\n![Chart]({png_path})\n\n"
            
            return markdown
            
        except Exception as e:
            return f"Error generating charts: {str(e)}" 