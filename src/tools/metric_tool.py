from pydantic import BaseModel, Field
from portia import Tool
from typing import Optional
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
    """Tool for calculating metrics from CSV data"""
    
    def __init__(self):
        super().__init__(
            name="metric_calculator_tool",
            description="Calculates metrics from CSV data using Python code"
        )
    
    def execute(self, code: str, csv_file: str) -> str:
        """
        Execute Python code to calculate metrics from CSV data.
        
        Args:
            code: Python code to execute for metric calculation
            csv_file: Path to the CSV file containing the data
            
        Returns:
            str: Calculated metrics in tabular format
        """
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Create a local namespace with required libraries
            local_namespace = {
                'df': df,
                'pd': pd,
                'np': np
            }
            
            # Capture stdout to get the printed metrics
            output = StringIO()
            with redirect_stdout(output):
                exec(code, local_namespace)
            
            return output.getvalue()
            
        except Exception as e:
            return f"Failed to calculate metrics: {str(e)}" 