"""Titanium CrewAI agent implementation."""

from agents.orchestrator.config import AGENT_ROLES, AgentConfig


class TitaniumAgent:
    """Represents a single CrewAI agent with tools and memory."""

    def __init__(
        self,
        agent_type: str,
        llm_config: dict | None = None,
        tools: list | None = None,
        allow_delegation: bool = False,
    ):
        self.agent_type = agent_type
        self.config = AGENT_ROLES.get(agent_type, AGENT_ROLES["researcher"])
        self.llm_config = llm_config or AgentConfig.get_llm_config()
        self.tools = tools or []
        self.allow_delegation = allow_delegation
        self._crew_agent = None

    def get_agent(self):
        """Get the CrewAI agent instance."""
        if self._crew_agent is None:
            from crewai import Agent

            self._crew_agent = Agent(
                role=self.config["role"],
                goal=self.config["goal"],
                backstory=self.config["backstory"],
                llm=self._create_llm(),
                tools=self.tools,
                allow_delegation=self.allow_delegation,
                verbose=True,
            )

        return self._crew_agent

    def _create_llm(self):
        """Create LLM instance based on configuration."""
        provider = self.llm_config["provider"]

        if provider == "ollama":
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=self.llm_config["model"],
                base_url=self.llm_config["base_url"],
                temperature=self.llm_config["temperature"],
                num_predict=self.llm_config["max_tokens"],
            )
        elif provider == "groq":
            from langchain_groq import ChatGroq

            return ChatGroq(
                model=self.llm_config["model"],
                temperature=self.llm_config["temperature"],
                max_tokens=self.llm_config["max_tokens"],
            )
        else:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=self.llm_config["model"],
                temperature=self.llm_config["temperature"],
                max_tokens=self.llm_config["max_tokens"],
                openai_api_key=self.llm_config.get("api_key", ""),
                openai_api_base=self.llm_config.get("base_url", ""),
            )


class TitaniumCrew:
    """CrewAI crew orchestrator for Titanium."""

    def __init__(self):
        self.agents: list[TitaniumAgent] = []
        self._crew = None

    def add_agent(self, agent: TitaniumAgent):
        """Add an agent to the crew."""
        self.agents.append(agent)

    def get_crew(self):
        """Get the CrewAI crew instance."""
        if self._crew is None:
            from crewai import Crew, Process

            crew_agents = [a.get_agent() for a in self.agents]

            self._crew = Crew(
                agents=crew_agents,
                process=Process.sequential,
                verbose=True,
                memory=AgentConfig.MEMORY_ENABLED,
            )

        return self._crew

    async def execute(self, task_description: str) -> dict:
        """Execute a task with the crew."""
        from crewai import Task

        crew = self.get_crew()
        lead_agent = self.agents[0].get_agent() if self.agents else None

        task = Task(
            description=task_description,
            agent=lead_agent,
            expected_output="A comprehensive and well-structured response",
        )

        result = crew.kickoff(tasks=[task])

        return {
            "status": "completed",
            "result": result.raw if hasattr(result, "raw") else str(result),
            "agents_used": len(self.agents),
        }


def create_agent(
    agent_type: str,
    tools: list | None = None,
    allow_delegation: bool = False,
) -> TitaniumAgent:
    """Factory function to create a Titanium agent."""
    return TitaniumAgent(
        agent_type=agent_type,
        tools=tools,
        allow_delegation=allow_delegation,
    )


def create_crew(agent_types: list[str]) -> TitaniumCrew:
    """Factory function to create a crew with specified agent types."""
    crew = TitaniumCrew()
    for agent_type in agent_types:
        crew.add_agent(create_agent(agent_type))
    return crew
