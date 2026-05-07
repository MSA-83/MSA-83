"""Agent orchestrator for multi-agent task execution with CrewAI."""

import asyncio
import uuid
from datetime import datetime

from agents.memory.agent_memory import AgentMemory, SharedMemory
from agents.orchestrator.crew import create_agent, create_crew
from agents.tools.agent_tools import get_agent_tools


class AgentOrchestrator:
    """Orchestrates task execution across CrewAI agents."""

    AGENT_TYPES = {
        "general": "General purpose agent for most tasks",
        "code": "Code generation and analysis agent",
        "research": "Research and information gathering agent",
        "analysis": "Data analysis and insights agent",
        "security": "Security auditing and analysis agent",
    }

    TYPE_MAP = {
        "general": "researcher",
        "code": "coder",
        "research": "researcher",
        "analysis": "analyst",
        "security": "security",
    }

    def __init__(self):
        self.active_tasks: dict[str, dict] = {}
        self.agent_memories: dict[str, AgentMemory] = {}
        self.shared_memory = SharedMemory("titanium-main")
        self._executor_pool: dict[str, asyncio.Task] = {}

    async def execute_task(
        self,
        task: str,
        agent_type: str = "general",
        use_memory: bool = True,
        priority: str = "normal",
    ) -> dict:
        """Execute a task using CrewAI agents."""
        if agent_type not in self.AGENT_TYPES:
            raise ValueError(f"Unknown agent type: {agent_type}")

        task_id = f"task-{uuid.uuid4().hex[:8]}"
        agent_id = f"{agent_type}-{task_id}"

        self.active_tasks[task_id] = {
            "task_id": task_id,
            "task": task,
            "agent_type": agent_type,
            "status": "running",
            "priority": priority,
            "use_memory": use_memory,
            "result": None,
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }

        memory_context = ""
        if use_memory:
            agent_memory = AgentMemory(agent_id)
            self.agent_memories[agent_id] = agent_memory
            memory_context = agent_memory.get_context(max_tokens=2000)

        enhanced_task = task
        if memory_context:
            enhanced_task = f"Relevant context from memory:\n\n{memory_context}\n\nTask: {task}"

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._run_crew_task,
            agent_type,
            enhanced_task,
        )

        self.active_tasks[task_id].update(
            {
                "status": "completed",
                "result": result.get("result", ""),
                "completed_at": datetime.utcnow().isoformat(),
            }
        )

        if use_memory and agent_id in self.agent_memories:
            self.agent_memories[agent_id].add(
                content=task,
                entry_type="task_result",
                metadata={"result": result.get("result", "")[:500]},
            )
            self.shared_memory.add(
                content=result.get("result", ""),
                source_agent=agent_id,
                metadata={"task_id": task_id},
            )

        return self.active_tasks[task_id]

    def _run_crew_task(self, agent_type: str, task: str) -> dict:
        """Run a CrewAI task synchronously."""
        crew_agent_type = self.TYPE_MAP.get(agent_type, "researcher")
        tools = get_agent_tools(crew_agent_type)

        agent = create_agent(
            agent_type=crew_agent_type,
            tools=tools,
        )

        crew = create_crew([crew_agent_type])
        crew.agents = [agent]

        try:
            result = asyncio.run(crew.execute(task))
            return result
        except Exception as e:
            return {
                "status": "failed",
                "result": f"Task execution failed: {str(e)}",
                "agents_used": 0,
            }

    async def get_task_status(self, task_id: str) -> dict | None:
        """Get the status of a specific task."""
        return self.active_tasks.get(task_id)

    async def cancel_task(self, task_id: str) -> dict:
        """Cancel a running task."""
        if task_id in self.active_tasks:
            self.active_tasks[task_id]["status"] = "cancelled"
            self.active_tasks[task_id]["completed_at"] = datetime.utcnow().isoformat()

            if task_id in self._executor_pool:
                self._executor_pool[task_id].cancel()
                del self._executor_pool[task_id]

            return {"task_id": task_id, "status": "cancelled"}
        return {"error": "Task not found"}

    async def get_all_agents_status(self) -> dict:
        """Get status of all agents."""
        return {
            "agents": {
                agent_type: {
                    "description": desc,
                    "status": "ready",
                    "tasks_in_queue": sum(
                        1
                        for t in self.active_tasks.values()
                        if t["agent_type"] == agent_type and t["status"] == "running"
                    ),
                }
                for agent_type, desc in self.AGENT_TYPES.items()
            },
            "active_tasks": len([t for t in self.active_tasks.values() if t["status"] == "running"]),
            "total_tasks": len(self.active_tasks),
        }

    async def get_agent_memory_stats(self) -> dict:
        """Get memory statistics across all agents."""
        stats = {}

        for agent_id, memory in self.agent_memories.items():
            stats[agent_id] = memory.get_stats()

        return {
            "agent_memories": stats,
            "shared_memory_entries": len(self.shared_memory.get_all()),
        }

    def get_agent_types(self) -> dict:
        """Get available agent types."""
        return self.AGENT_TYPES
