import requests
from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext
import os
import json
import pandas as pd
from typing import Dict, Any

class SubgraphQuerySchema(BaseModel):
    gql_query: str = Field(..., description="The GraphQL query to run")
    output_file: str = Field(..., description="The name of the CSV file to save the results")

class SubgraphQueryTool(Tool):
    def __init__(self):
        super().__init__(
            id="subgraph_query_tool",
            name="Subgraph Query Tool",
            description="Executes GraphQL queries against a subgraph and saves results to CSV",
            parameters={
                "gql_query": {
                    "type": "string",
                    "description": "The GraphQL query to execute"
                },
                "output_file": {
                    "type": "string",
                    "description": "Path to save the CSV output"
                }
            }
        )
        
    def execute(self, inputs: Dict[str, Any]) -> str:
        """
        Execute a GraphQL query and save results to CSV.
        
        Args:
            inputs (Dict[str, Any]): Dictionary containing:
                - gql_query: The GraphQL query to execute
                - output_file: Path to save the CSV output
                
        Returns:
            str: Status message indicating success or failure
        """
        try:
            # Get the GraphQL endpoint from environment
            endpoint = os.getenv("GRAPHQL_ENDPOINT")
            if not endpoint:
                raise ValueError("GRAPHQL_ENDPOINT environment variable not set")
            
            # Execute the query
            response = requests.post(
                endpoint,
                json={"query": inputs["gql_query"]},
                headers={"Content-Type": "application/json"}
            )
            
            # Check for errors
            if "errors" in response.json():
                raise ValueError(f"GraphQL query failed: {response.json()['errors']}")
            
            # Extract data from response
            data = response.json()["data"]
            
            # Convert to DataFrame
            df = pd.json_normalize(data)
            
            # Save to CSV
            df.to_csv(inputs["output_file"], index=False)
            
            return f"Successfully executed query and saved results to {inputs['output_file']}"
            
        except Exception as e:
            return f"Error executing query: {str(e)}" 