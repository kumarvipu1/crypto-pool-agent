from pathlib import Path
import pandas as pd
import json
from portia import Tool, ToolRunContext
from typing import Annotated, Union, Dict, Any


class FileReaderTool(Tool[str]):
    """Finds and reads content from a local file on Disk."""

    id: str = "file_reader_tool"
    name: str = "File reader tool"
    description: str = "Finds and reads content from a local file on Disk"
    output_schema: tuple[str, str] = ("str", "A string dump or JSON of the file content")

    def execute(self, ctx: ToolRunContext, filename: Annotated[str, "The location where the file should be read from"]) -> Union[str, Dict[str, Any]]:       
        """Run the FileReaderTool."""
        
        file_path = Path(filename)
        suffix = file_path.suffix.lower()

        if file_path.is_file():
            if suffix == '.csv':
                return pd.read_csv(file_path).to_string()
            elif suffix == '.json':
                with file_path.open('r', encoding='utf-8') as json_file:
                    data = json.load(json_file)
                    return data
            elif suffix in ['.xls', '.xlsx']:
                return pd.read_excel(file_path).to_string()
            elif suffix in ['.txt', '.log']:
                return file_path.read_text(encoding="utf-8")
            else:
                return f"Unsupported file type: {suffix}"
        else:
            return f"File not found: {filename}" 