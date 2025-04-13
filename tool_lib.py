from dotenv import load_dotenv
from portia import (
    Portia,
    example_tool_registry,
)
from agent_module import run_agent
from pydantic import BaseModel, Field
from portia.tool import Tool, ToolRunContext
import nest_asyncio
import asyncio

nest_asyncio.apply()


class userquerySchema(BaseModel):
    """Schema defining the inputs for the FileReaderTool."""

    user_query: str = Field(..., 
        description="the query from user",
    )


class QueryRunner(Tool[str]):
    """Executes the user query"""

    id: str = "run_user_query"
    name: str = "User Query runner"
    description: str = "executes user query to get data"
    args_schema: type[BaseModel] = userquerySchema
    output_schema: tuple[str, str] = ("str", "A string dump or JSON of the file content") # Changed to tuple type
    
    def run(self, _: ToolRunContext, user_query: str) -> str:
        try:
            response = run_agent(user_query)
            response_dict = {
                'markdown_report': response.markdown_report,
                'csv_path': response.csv_path,
                'metrics_dict': response.metrics_dict,
                'html_path': response.html_path,
                'png_path': response.png_path,
                'pdf_path': response.pdf_path,
                'enso_route': response.enso_route,
                'enso_route_file': response.enso_route_file
            }
            return str(response_dict)  # Return as single-item tuple
        except Exception as e:
            print(f"Error in agent response: {str(e)}")
            return {
                'markdown_report': f'no data with error \n {e}',
                'csv_path': '',
                'metrics_dict': '',
                'html_path': [''],
                'png_path': [''],
                'pdf_path': '',
                'enso_route': '',
                'enso_route_file': ''
            }

