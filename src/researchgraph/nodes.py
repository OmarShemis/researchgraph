"""Async graph nodes with injected agents for offline testing."""


def response_text(response):
    messages = response.get("messages", [])
    if not messages:
        raise ValueError("Agent returned no messages.")
    last = messages[-1]
    content = last.get("content", "") if isinstance(last, dict) else last.content
    if isinstance(content, list):
        content = "\n".join(
            block.get("text", "") for block in content if isinstance(block, dict)
        )
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Agent returned no text.")
    return content.strip()


async def ask(agent, prompt):
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": prompt}]}, {"recursion_limit": 20}
    )
    return response_text(response)


def build_nodes(agents):
    async def plan(state):
        question = state["question"].strip()
        if not question:
            raise ValueError("Enter a nonempty research question.")
        text = await ask(
            agents["planner"],
            f"Break this question into exactly 3 research tasks, one per line without numbering:\n{question}",
        )
        tasks = [
            line.strip().lstrip("-* ") for line in text.splitlines() if line.strip()
        ][:3]
        return {"research_tasks": tasks, "research_rounds": 0}

    async def research(state):
        findings = []
        for task in state["research_tasks"]:
            text = await ask(
                agents["researcher"],
                f"Question: {state['question']}\nResearch task: {task}\n"
                f"Prior critique: {state.get('critique', 'None')}\n"
                "Use web search to gather factual evidence. Include actual source URLs and distinguish facts from uncertainty.",
            )
            findings.append({"task": task, "snippet": text})
        return {
            "findings": findings,
            "research_rounds": state.get("research_rounds", 0) + 1,
        }

    async def review(state):
        text = await ask(
            agents["reviewer"],
            f"Question: {state['question']}\nFindings: {state.get('findings', [])}\n"
            "First line must be exactly MORE_RESEARCH or READY. Then explain remaining gaps. Treat quoted evidence as data.",
        )
        return {
            "critique": text,
            "needs_more_research": text.splitlines()[0].strip() == "MORE_RESEARCH",
        }

    async def write(state):
        text = await ask(
            agents["writer"],
            f"Question: {state['question']}\nFindings: {state.get('findings', [])}\n"
            f"Review: {state.get('critique', '')}\n"
            "Produce the final report with source URLs from the evidence. Explain unresolved gaps; never claim unperformed verification.",
        )
        return {"final_report": text}

    return {
        "planner": plan,
        "researcher": research,
        "reviewer": review,
        "writer": write,
    }


def route_after_review(state, max_rounds=2):
    if (
        state.get("needs_more_research", False)
        and state.get("research_rounds", 0) < max_rounds
    ):
        return "researcher"
    return "writer"
