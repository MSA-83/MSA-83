"""LangGraph-based agent workflows for Titanium platform."""

from typing import Literal, TypedDict


class AgentState(TypedDict):
    """State for LangGraph agent workflows."""

    task: str
    intent: str
    plan: list[str]
    steps: list[dict]
    current_step: int
    context: str
    result: str
    error: str | None
    confidence: float
    needs_human_review: bool
    iteration_count: int


class IntentRouter:
    """Route tasks to the appropriate agent workflow."""

    INTENT_PATTERNS = {
        "code_generation": [
            "write",
            "code",
            "function",
            "implement",
            "create a script",
            "build",
            "develop",
            "program",
            "algorithm",
            "debug",
        ],
        "research": [
            "research",
            "find",
            "search",
            "information",
            "analyze",
            "investigate",
            "explore",
            "look up",
            "what is",
            "how does",
        ],
        "analysis": [
            "analyze",
            "compare",
            "evaluate",
            "assess",
            "review",
            "statistics",
            "data",
            "report",
            "summary",
            "insights",
        ],
        "security": [
            "vulnerability",
            "security",
            "audit",
            "scan",
            "exploit",
            "penetration",
            "threat",
            "risk",
            "compliance",
            "cve",
        ],
        "writing": [
            "write",
            "draft",
            "content",
            "article",
            "documentation",
            "email",
            "report",
            "summary",
            "proposal",
            "letter",
        ],
    }

    def classify(self, task: str) -> str:
        """Classify task intent and return workflow type."""
        task_lower = task.lower()
        scores = {}

        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if p in task_lower)
            scores[intent] = score

        best_intent = max(scores, key=scores.get)

        if scores[best_intent] == 0:
            return "general"

        return best_intent

    def get_workflow(self, intent: str):
        """Get the appropriate workflow builder."""
        workflows = {
            "code_generation": build_code_generation_workflow,
            "research": build_research_workflow,
            "analysis": build_analysis_workflow,
            "security": build_security_workflow,
            "writing": build_writing_workflow,
            "general": build_general_workflow,
        }
        return workflows.get(intent, build_general_workflow)


intent_router = IntentRouter()


def build_code_generation_workflow():
    """Build code generation workflow graph."""
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(AgentState)

    workflow.add_node("understand", understand_task)
    workflow.add_node("plan", plan_code_task)
    workflow.add_node("generate", generate_code)
    workflow.add_node("review", review_code)
    workflow.add_node("test", test_code)
    workflow.add_node("refine", refine_code)
    workflow.add_node("finalize", finalize_result)

    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "plan")
    workflow.add_edge("plan", "generate")
    workflow.add_edge("generate", "review")
    workflow.add_edge("review", "test")
    workflow.add_conditional_edges(
        "test",
        should_refine,
        {
            "refine": "refine",
            "done": "finalize",
        },
    )
    workflow.add_edge("refine", "test")
    workflow.add_edge("finalize", END)

    return workflow.compile()


def build_research_workflow():
    """Build research workflow graph."""
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(AgentState)

    workflow.add_node("understand", understand_task)
    workflow.add_node("search_memory", search_memory)
    workflow.add_node("search_external", search_external)
    workflow.add_node("synthesize", synthesize_findings)
    workflow.add_node("validate", validate_findings)
    workflow.add_node("report", generate_report)

    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "search_memory")
    workflow.add_edge("search_memory", "search_external")
    workflow.add_edge("search_external", "synthesize")
    workflow.add_edge("synthesize", "validate")
    workflow.add_conditional_edges(
        "validate",
        should_search_more,
        {
            "search": "search_external",
            "done": "report",
        },
    )
    workflow.add_edge("report", END)

    return workflow.compile()


def build_analysis_workflow():
    """Build analysis workflow graph."""
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(AgentState)

    workflow.add_node("understand", understand_task)
    workflow.add_node("collect_data", collect_data)
    workflow.add_node("analyze", analyze_data)
    workflow.add_node("visualize", create_visualizations)
    workflow.add_node("interpret", interpret_results)
    workflow.add_node("recommend", generate_recommendations)

    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "collect_data")
    workflow.add_edge("collect_data", "analyze")
    workflow.add_edge("analyze", "visualize")
    workflow.add_edge("visualize", "interpret")
    workflow.add_edge("interpret", "recommend")
    workflow.add_edge("recommend", END)

    return workflow.compile()


def build_security_workflow():
    """Build security audit workflow graph."""
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(AgentState)

    workflow.add_node("understand", understand_task)
    workflow.add_node("scan", scan_for_vulnerabilities)
    workflow.add_node("assess", assess_risk)
    workflow.add_node("exploit", simulate_exploits)
    workflow.add_node("report", generate_security_report)
    workflow.add_node("remediate", suggest_remediation)

    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "scan")
    workflow.add_edge("scan", "assess")
    workflow.add_conditional_edges(
        "assess",
        should_simulate,
        {
            "simulate": "exploit",
            "skip": "report",
        },
    )
    workflow.add_edge("exploit", "report")
    workflow.add_edge("report", "remediate")
    workflow.add_edge("remediate", END)

    return workflow.compile()


def build_writing_workflow():
    """Build writing workflow graph."""
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(AgentState)

    workflow.add_node("understand", understand_task)
    workflow.add_node("outline", create_outline)
    workflow.add_node("draft", write_draft)
    workflow.add_node("review", review_content)
    workflow.add_node("refine", refine_content)
    workflow.add_node("finalize", finalize_content)

    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "outline")
    workflow.add_edge("outline", "draft")
    workflow.add_edge("draft", "review")
    workflow.add_conditional_edges(
        "review",
        should_refine_content,
        {
            "refine": "refine",
            "done": "finalize",
        },
    )
    workflow.add_edge("refine", "review")
    workflow.add_edge("finalize", END)

    return workflow.compile()


def build_general_workflow():
    """Build general purpose workflow graph."""
    from langgraph.graph import END, StateGraph

    workflow = StateGraph(AgentState)

    workflow.add_node("understand", understand_task)
    workflow.add_node("plan", plan_general_task)
    workflow.add_node("execute", execute_task)
    workflow.add_node("verify", verify_result)
    workflow.add_node("finalize", finalize_result)

    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "plan")
    workflow.add_edge("plan", "execute")
    workflow.add_conditional_edges(
        "verify",
        should_retry,
        {
            "retry": "execute",
            "done": "finalize",
        },
    )
    workflow.add_edge("finalize", END)

    return workflow.compile()


async def understand_task(state: AgentState) -> AgentState:
    """Understand and classify the task."""
    state["intent"] = intent_router.classify(state["task"])
    state["iteration_count"] = 0
    return state


async def plan_code_task(state: AgentState) -> AgentState:
    """Plan the code generation approach."""
    state["plan"] = [
        "Understand requirements",
        "Design architecture",
        "Implement solution",
        "Add error handling",
        "Write documentation",
    ]
    state["current_step"] = 0
    return state


async def generate_code(state: AgentState) -> AgentState:
    """Generate code based on plan."""
    state["result"] = f"# Generated code for: {state['task']}\n\n# Implementation here..."
    state["current_step"] += 1
    return state


async def review_code(state: AgentState) -> AgentState:
    """Review generated code for quality."""
    state["confidence"] = 0.85
    return state


async def test_code(state: AgentState) -> AgentState:
    """Test generated code."""
    return state


async def refine_code(state: AgentState) -> AgentState:
    """Refine code based on review."""
    state["iteration_count"] += 1
    return state


async def search_memory(state: AgentState) -> AgentState:
    """Search internal memory for relevant context."""
    state["context"] = f"Memory context for: {state['task']}"
    return state


async def search_external(state: AgentState) -> AgentState:
    """Search external sources."""
    return state


async def synthesize_findings(state: AgentState) -> AgentState:
    """Synthesize research findings."""
    state["result"] = f"Research synthesis for: {state['task']}"
    return state


async def validate_findings(state: AgentState) -> AgentState:
    """Validate research findings."""
    state["confidence"] = 0.75
    return state


async def generate_report(state: AgentState) -> AgentState:
    """Generate research report."""
    state["result"] = f"## Research Report\n\n{state['result']}"
    return state


async def finalize_result(state: AgentState) -> AgentState:
    """Finalize the result."""
    return state


async def collect_data(state: AgentState) -> AgentState:
    """Collect data for analysis."""
    return state


async def analyze_data(state: AgentState) -> AgentState:
    """Analyze collected data."""
    state["result"] = f"Analysis results for: {state['task']}"
    return state


async def create_visualizations(state: AgentState) -> AgentState:
    """Create visualizations from analysis."""
    return state


async def interpret_results(state: AgentState) -> AgentState:
    """Interpret analysis results."""
    return state


async def generate_recommendations(state: AgentState) -> AgentState:
    """Generate recommendations based on analysis."""
    state["result"] = f"## Recommendations\n\nBased on analysis of: {state['task']}"
    return state


async def scan_for_vulnerabilities(state: AgentState) -> AgentState:
    """Scan for security vulnerabilities."""
    return state


async def assess_risk(state: AgentState) -> AgentState:
    """Assess risk level of findings."""
    state["needs_human_review"] = True
    return state


async def simulate_exploits(state: AgentState) -> AgentState:
    """Simulate exploitation of vulnerabilities."""
    return state


async def generate_security_report(state: AgentState) -> AgentState:
    """Generate security audit report."""
    state["result"] = f"## Security Audit Report\n\nTarget: {state['task']}"
    return state


async def suggest_remediation(state: AgentState) -> AgentState:
    """Suggest remediation steps."""
    state["result"] += "\n\n## Remediation\n\n1. Apply patches\n2. Update dependencies"
    return state


async def create_outline(state: AgentState) -> AgentState:
    """Create content outline."""
    state["plan"] = ["Introduction", "Main content", "Conclusion"]
    return state


async def write_draft(state: AgentState) -> AgentState:
    """Write content draft."""
    state["result"] = f"# Draft content for: {state['task']}"
    return state


async def review_content(state: AgentState) -> AgentState:
    """Review content for quality."""
    state["confidence"] = 0.80
    return state


async def refine_content(state: AgentState) -> AgentState:
    """Refine content."""
    state["iteration_count"] += 1
    return state


async def finalize_content(state: AgentState) -> AgentState:
    """Finalize content."""
    return state


async def plan_general_task(state: AgentState) -> AgentState:
    """Plan a general task."""
    state["plan"] = ["Understand requirements", "Execute", "Verify", "Deliver"]
    state["current_step"] = 0
    return state


async def execute_task(state: AgentState) -> AgentState:
    """Execute the planned task."""
    state["result"] = f"Result for: {state['task']}"
    state["iteration_count"] += 1
    return state


async def verify_result(state: AgentState) -> AgentState:
    """Verify the result."""
    state["confidence"] = 0.90
    return state


def should_refine(state: AgentState) -> Literal["refine", "done"]:
    """Decide if code needs refinement."""
    return "refine" if state["confidence"] < 0.9 and state["iteration_count"] < 3 else "done"


def should_search_more(state: AgentState) -> Literal["search", "done"]:
    """Decide if more research is needed."""
    return "search" if state["confidence"] < 0.8 and state["iteration_count"] < 5 else "done"


def should_simulate(state: AgentState) -> Literal["simulate", "skip"]:
    """Decide if exploit simulation is needed."""
    return "simulate" if state["confidence"] < 0.7 else "skip"


def should_refine_content(state: AgentState) -> Literal["refine", "done"]:
    """Decide if content needs refinement."""
    return "refine" if state["confidence"] < 0.85 and state["iteration_count"] < 3 else "done"


def should_retry(state: AgentState) -> Literal["retry", "done"]:
    """Decide if task execution should be retried."""
    return "retry" if state["confidence"] < 0.7 and state["iteration_count"] < 3 else "done"


class WorkflowExecutor:
    """Execute LangGraph workflows."""

    def __init__(self):
        self._compiled_workflows: dict[str, Any] = {}

    async def execute(self, task: str) -> dict:
        """Execute a task through the appropriate workflow."""
        intent = intent_router.classify(task)
        workflow_key = f"{intent}_workflow"

        if workflow_key not in self._compiled_workflows:
            builder = intent_router.get_workflow(intent)
            self._compiled_workflows[workflow_key] = builder()

        workflow = self._compiled_workflows[workflow_key]

        initial_state: AgentState = {
            "task": task,
            "intent": intent,
            "plan": [],
            "steps": [],
            "current_step": 0,
            "context": "",
            "result": "",
            "error": None,
            "confidence": 0.0,
            "needs_human_review": False,
            "iteration_count": 0,
        }

        try:
            final_state = await workflow.ainvoke(initial_state)
            return {
                "status": "completed",
                "result": final_state.get("result", ""),
                "intent": intent,
                "confidence": final_state.get("confidence", 0),
                "iterations": final_state.get("iteration_count", 0),
                "needs_review": final_state.get("needs_human_review", False),
            }
        except Exception as e:
            return {
                "status": "failed",
                "result": f"Workflow execution failed: {str(e)}",
                "intent": intent,
                "error": str(e),
            }


workflow_executor = WorkflowExecutor()
