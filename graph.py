from langgraph.graph import MessagesState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from query import rag_agent

class CustomMessageState(MessagesState):
    message: str
    

initial_message = [HumanMessage(content="Hello llama")]

llm = ChatOpenAI(
    model="llama3.2", base_url="http://localhost:11434/v1", temperature=0, api_key="llama3.2"
)
llm_rag = llm.bind_tools([rag_agent])
print(llm_rag.invoke("Hello"))