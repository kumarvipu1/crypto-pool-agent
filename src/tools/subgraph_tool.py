"""GraphQL Subgraph Query Tool."""

from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from pydantic import BaseModel, Field
import os
import pandas as pd
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from typing import Dict, Any, List, Optional

class SubgraphQueryInput(BaseModel):
    """Input schema for the subgraph query tool."""
    query: str = Field(..., description="The GraphQL query to execute")
    output_file: str = Field(default="query_results.csv", description="Path to save the CSV file")
    flatten_nested: bool = Field(default=True, description="Whether to flatten nested data structures")

class SubgraphQueryOutput(BaseModel):
    """Output schema for the subgraph query tool."""
    file_path: str = Field(..., description="Path to the saved CSV file")
    row_count: int = Field(..., description="Number of rows in the dataset")
    columns: List[str] = Field(..., description="List of columns in the dataset")
    summary: Dict[str, Any] = Field(..., description="Statistical summary of the dataset")

class SubgraphQueryTool(Tool[SubgraphQueryOutput]):
    """Tool for querying subgraph data and saving to CSV.
    
    This tool executes GraphQL queries against a subgraph endpoint and saves the results
    to a CSV file. It can optionally flatten nested data structures and provides
    statistical summaries of the data.
    """
    
    id: str = "subgraph_query_tool"
    name: str = "Subgraph Query Tool"
    description: str = "Executes GraphQL queries against a subgraph and saves results to CSV"
    args_schema: type[BaseModel] = SubgraphQueryInput
    output_schema: tuple[str, str] = ("SubgraphQueryOutput", "Output containing file path and dataset summary")
    should_summarize: bool = False

    def __init__(self):
        super().__init__()
        transport = RequestsHTTPTransport(
            url=os.getenv("GRAPHQL_ENDPOINT"),
            verify=True,
            retries=3
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
    
    def run(self, ctx: ToolRunContext, query: str, output_file: str = "query_results.csv", flatten_nested: bool = True) -> SubgraphQueryOutput:
        """
        Execute a GraphQL query and save results to CSV.
        
        Args:
            ctx: The tool run context containing the input parameters
            query: The GraphQL query to execute
            output_file: Path to save the CSV file
            flatten_nested: Whether to flatten nested data structures
            
        Returns:
            SubgraphQueryOutput: The output containing file path and dataset summary
            
        Raises:
            ToolHardError: If the query execution fails
        """
        try:
            # Execute the query
            response = self.client.execute(gql(query))

            # Flatten the top-level field dynamically
            top_level_key = list(response.keys())[0]
            data = response[top_level_key]

            # Flatten nested data structures if requested
            flat_data = []
            if len(data) > 0:
                for item in data:
                    flat_item = item.copy()
                    if flatten_nested:
                        # Handle nested token data
                        if "token0" in item and isinstance(item["token0"], dict):
                            flat_item.update({
                                "token0_id": item["token0"].get("id"),
                                "token0_symbol": item["token0"].get("symbol"),
                                "token0_name": item["token0"].get("name"),
                            })
                            del flat_item["token0"]
                        if "token1" in item and isinstance(item["token1"], dict):
                            flat_item.update({
                                "token1_id": item["token1"].get("id"),
                                "token1_symbol": item["token1"].get("symbol"),
                                "token1_name": item["token1"].get("name"),
                            })
                            del flat_item["token1"]
                    flat_data.append(flat_item)

                # Convert to DataFrame and save
                df = pd.DataFrame(flat_data)
                df.to_csv(output_file, index=False)
                
                # Create output
                return SubgraphQueryOutput(
                    file_path=output_file,
                    row_count=len(df),
                    columns=df.columns.tolist(),
                    summary=df.describe().to_dict()
                )
            else:
                raise ToolHardError("Query returned no data")

        except Exception as e:
            raise ToolHardError(f"GraphQL query failed: {str(e)}") from e 