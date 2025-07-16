from langchain_community.tools.wikipedia.tool import WikipediaQueryRun
from langchain_community.tools import Tool
from langchain_community.utilities.wikipedia import WikipediaAPIWrapper
from langchain_community.tools.google_search.tool import GoogleSearchRun

api_wrapper = WikipediaAPIWrapper()

search = WikipediaQueryRun(api_wrapper=api_wrapper)
search_tool = Tool(
    name="search",
    func=search.run,
    description="Search Wikipedia for information."
)
