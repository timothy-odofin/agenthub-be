
from langchain.agents import create_react_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

from app.core.utils.single_ton import SingletonMeta
from app.services.agent.tools import tool_registry

class ReactAgent(metaclass=SingletonMeta):
    """
    Production-ready ReAct agent wrapper.
    Handles agent construction, prompt creation, and inference.
    """

    def __init__(self, llm,  verbose: bool = False):
        if hasattr(self, "_initialized"):
            return  # prevent re-initialization

        self.llm = llm
        self.tools = tool_registry.get_all_tools()
        self.verbose = verbose

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Use tools when needed. When user provides a question, think step by step. You should also give clarification when necessary."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=self.verbose
        )
        self._initialized = True

    def run(self, query: str) -> str:
        """
        Run a user query through the agent.
        """
        response = self.executor.invoke({"input": query})
        return response.get("output", "")
