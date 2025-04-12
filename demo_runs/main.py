from dotenv import load_dotenv
from portia import (
    Portia,
    example_tool_registry,
)
from my_custom_tools.registry import custom_tool_registry

load_dotenv()

# Load example and custom tool registries into a single one
complete_tool_registry = example_tool_registry + custom_tool_registry

# Instantiate Portia with the tools above
portia = Portia(tools=complete_tool_registry)

# Execute the plan from the user query
plan_run = portia.run('Get the weather in the town with the longest name in England '
                     'and write it to demo_runs/weather.txt.')

# Serialise into JSON and print the output
print(plan_run.model_dump_json(indent=2)) 