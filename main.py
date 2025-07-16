from dotenv import load_dotenv
from typing import List
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# Modern Pydantic v2 model with typing
class ResearchResponse(BaseModel):
    #topic: str
    summary: str
    #sources: List[str]
    #tools_used: List[str]

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
parser = PydanticOutputParser(pydantic_object=ResearchResponse)

# Agent prompt without forcing Pydantic format here
agent_prompt = ChatPromptTemplate.from_messages([
    ("system",
          """You are a helpful assistant.

Your job is to answer the user’s query using available tools if needed, 
but your response must follow these strict guidelines:
- Only return the final answer.
- The answer must be short and concise(maximum 3 sentences).
- Do NOT include any thoughts, reasoning steps, actions, or logs.
- If tools are used internally, do not expose them.
- If you cannot find an answer, say "I don't know" without any further explanation.
Keep your language professional and factual."""),
    ("placeholder", "{chat_history}"),
    ("human", "{query}"),
    ("placeholder", "{agent_scratchpad}"), # This is where the agent will write its thoughts, you can remove it
])

agent = create_tool_calling_agent(
    llm=llm,
    prompt=agent_prompt,
    tools=[]
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[],
    verbose=True
)

while True:
    query = input("Scrivi il tuo messaggio: ")
    if query.lower() in ["exit", "quit"]:
        break

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are a helpful assistant.
Answer concisely (max 3 sentences), professionally, and factually.
If you don't know, say "I don't know"."""), 
        ("human", "{query}")
    ])
    
    response = llm.invoke(prompt.format_prompt(query=query))
    
    format_prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Format the following text as JSON using this schema:\n{format_instructions}"),
        ("human", response.content),
    ]).partial(format_instructions=parser.get_format_instructions())
    
    format_response = llm.invoke(format_prompt.format_prompt())
    structured_response = parser.parse(format_response.content)

    print("\n✅ Structured Response:")
    print(structured_response.model_dump())
