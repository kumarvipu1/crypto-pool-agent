from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext
import pandas as pd
from tabulate import tabulate
from io import StringIO
import sys
from contextlib import redirect_stdout
import numpy as np
from typing import Dict, Any

class MetricCalculatorSchema(BaseModel):
    code: str = Field(..., description="The Python code to execute to run calculations")
    csv_file: str = Field(..., description="The path to the CSV file containing the data")

class MetricCalculatorTool(Tool):
    def __init__(self):
        super().__init__(
            id="metric_calculator_tool",
            name="Metric Calculator Tool",
            description="Calculates various metrics from CSV data using Python code",
            parameters={
                "code": {
                    "type": "string",
                    "description": "Python code to calculate metrics"
                },
                "csv_file": {
                    "type": "string",
                    "description": "Path to the CSV file containing data"
                }
            }
        )
        
    def execute(self, inputs: Dict[str, Any]) -> str:
        """
        Execute Python code to calculate metrics from CSV data.
        
        Args:
            inputs (Dict[str, Any]): Dictionary containing:
                - code: Python code to calculate metrics
                - csv_file: Path to the CSV file
                
        Returns:
            str: Calculated metrics in markdown format
        """
        try:
            # Read the CSV file
            df = pd.read_csv(inputs["csv_file"])
            
            # Create a local namespace for code execution
            namespace = {
                "df": df,
                "pd": pd,
                "np": np
            }
            
            # Execute the code
            exec(inputs["code"], namespace)
            
            # Get the metrics from the namespace
            metrics = namespace.get("metrics", {})
            
            # Format metrics as markdown
            markdown = "## Calculated Metrics\n\n"
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)):
                    markdown += f"### {metric_name}\n{value:,.2f}\n\n"
                else:
                    markdown += f"### {metric_name}\n{value}\n\n"
                    
            return markdown
            
        except Exception as e:
            return f"Error calculating metrics: {str(e)}" 