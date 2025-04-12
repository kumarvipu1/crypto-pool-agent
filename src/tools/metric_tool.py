"""Metric Calculator Tool."""

from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from tabulate import tabulate
from io import StringIO
from contextlib import redirect_stdout
from typing import Dict, Any, List, Optional

class MetricCalculatorInput(BaseModel):
    """Input schema for the metric calculator tool."""
    code: str = Field(..., description="The Python code to execute to run calculations")
    csv_file: str = Field(..., description="The path to the CSV file containing the data")
    output_format: str = Field(default="table", description="Output format: 'table' or 'dict'")

class MetricCalculatorOutput(BaseModel):
    """Output schema for the metric calculator tool."""
    metrics: Dict[str, Any] = Field(..., description="Calculated metrics")
    table_output: Optional[str] = Field(None, description="Metrics in tabular format")
    error: Optional[str] = Field(None, description="Error message if calculation failed")

class MetricCalculatorTool(Tool[MetricCalculatorOutput]):
    """Tool for calculating metrics from CSV data.
    
    This tool executes Python code to calculate metrics from CSV data. It supports
    both tabular and dictionary output formats and provides proper error handling.
    """
    
    id: str = "metric_calculator_tool"
    name: str = "Metric Calculator Tool"
    description: str = "Calculates metrics from CSV data using Python code"
    args_schema: type[BaseModel] = MetricCalculatorInput
    output_schema: tuple[str, str] = ("MetricCalculatorOutput", "Output containing calculated metrics and optional table format")
    should_summarize: bool = False

    def __init__(self):
        super().__init__()
    
    def run(self, ctx: ToolRunContext, code: str, csv_file: str, output_format: str = "table") -> MetricCalculatorOutput:
        """
        Execute Python code to calculate metrics from CSV data.
        
        Args:
            ctx: The tool run context containing the input parameters
            code: The Python code to execute
            csv_file: Path to the CSV file
            output_format: Output format ('table' or 'dict')
            
        Returns:
            MetricCalculatorOutput: The calculated metrics and optional table output
            
        Raises:
            ToolHardError: If the metric calculation fails
        """
        try:
            # Read the CSV file
            df = pd.read_csv(csv_file)
            
            # Create a local namespace with required libraries
            local_namespace = {
                'df': df,
                'pd': pd,
                'np': np,
                'tabulate': tabulate
            }
            
            # Capture stdout to get the printed metrics
            output = StringIO()
            metrics_dict = {}
            
            with redirect_stdout(output):
                # Execute the code
                exec(code, local_namespace)
                
                # Try to get metrics from the local namespace
                for var_name, var_value in local_namespace.items():
                    if isinstance(var_value, (pd.DataFrame, pd.Series, np.ndarray)):
                        metrics_dict[var_name] = var_value
                    elif isinstance(var_value, (int, float, str, bool)):
                        metrics_dict[var_name] = var_value
            
            # Create table output if requested
            table_output = None
            if output_format == "table":
                table_output = output.getvalue()
            
            return MetricCalculatorOutput(
                metrics=metrics_dict,
                table_output=table_output
            )
            
        except Exception as e:
            raise ToolHardError(f"Failed to calculate metrics: {str(e)}") from e 