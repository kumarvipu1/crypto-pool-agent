from pydantic import BaseModel, Field
from portia import Tool
from typing import Dict, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go

class ChartGeneratorSchema(BaseModel):
    code: str = Field(..., description="The Python code to execute to generate charts")
    csv_file: str = Field(..., description="The path to the CSV file containing the data")
    output_dir: str = Field(..., description="The directory to save the generated charts")

class ChartGeneratorTool(Tool):
    """Tool for generating charts from CSV data"""
    
    def __init__(self):
        super().__init__(
            name="chart_generator_tool",
            description="Generates charts from CSV data using Plotly"
        )
    
    def execute(self, code: str, csv_file: str, output_dir: str) -> str:
        """
        Execute Python code to generate charts from CSV data.
        
        Args:
            code: Python code to generate charts
            csv_file: Path to the CSV file containing the data
            output_dir: Directory to save the generated charts
            
        Returns:
            str: Summary of generated charts
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
                'output_dir': output_dir,
                'datetime': datetime
            }
            
            # Execute the code to generate charts
            exec(code, local_namespace)
            
            # Get list of generated files
            generated_files = [f for f in os.listdir(output_dir) if f.endswith(('.png', '.html'))]
            
            return f"Generated {len(generated_files)} charts in {output_dir}:\n" + "\n".join(generated_files)
            
        except Exception as e:
            return f"Failed to generate charts: {str(e)}" 