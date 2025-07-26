from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
import os
import getpass


if "GOOGLE_AI_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your API key: ")

if "GOOGLE_CSE_ID" not in os.environ:
    os.environ["GOOGLE_CSE_ID"] = getpass.getpass("Enter your Google CSE ID: ")

search = GoogleSearchAPIWrapper()

tool = Tool(
    name="google_search",
    description="Search Google for recent results.",
    func=search.run,
)

print(tool.run("How tall is the Space Needle?"))