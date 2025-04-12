"""Registry containing my custom tools."""

from portia import InMemoryToolRegistry
from my_custom_tools.file_reader_tool import FileReaderTool
from my_custom_tools.file_writer_tool import FileWriterTool

custom_tool_registry = InMemoryToolRegistry.from_local_tools(
    [
        FileReaderTool(),
        FileWriterTool(),
    ],
) 