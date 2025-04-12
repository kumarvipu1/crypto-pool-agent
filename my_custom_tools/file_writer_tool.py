from pathlib import Path
import json
from portia import Tool, ToolRunContext
from typing import Annotated, Union, Dict, Any


class FileWriterTool(Tool[str]):
    """Writes content to a local file on Disk."""

    id: str = "file_writer_tool"
    name: str = "File writer tool"
    description: str = "Writes content to a local file on Disk"
    output_schema: tuple[str, str] = ("str", "A string describing the result of the write operation")

    def execute(self, ctx: ToolRunContext, 
                content: Annotated[str, "The content to write to the file"],
                filename: Annotated[str, "The location where the file should be written to"]) -> str:
        """Run the FileWriterTool."""
        
        file_path = Path(filename)
        suffix = file_path.suffix.lower()

        try:
            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if suffix == '.json':
                # If content is a string, try to parse it as JSON
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except json.JSONDecodeError:
                        pass
                
                # Write JSON with indentation
                with file_path.open('w', encoding='utf-8') as json_file:
                    json.dump(content, json_file, indent=4)
            else:
                # Write text content
                with file_path.open('w', encoding='utf-8') as text_file:
                    text_file.write(content)

            return f"Successfully wrote content to {filename}"
            
        except Exception as e:
            return f"Failed to write to file: {str(e)}" 