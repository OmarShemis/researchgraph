from deepagents import create_deep_agent

from researchgraph.prompts.system_prompts import RESEARCHER


def create_researcher(model, tools):
    agent = create_deep_agent(model=model, tools=tools, system_prompt=RESEARCHER)

    async def research(state):
        result = await agent.ainvoke({"messages": [{
            "role": "user",
            "content": (
                f"Question: {state['question']}\nPlan: {state['plan']}\n"
                f"Previous findings: {state.get('findings', '')}\n"
                f"Review feedback: {state.get('review', '')}"
            ),
        }]})
        return {
            "findings": result["messages"][-1].text,
            "rounds": state.get("rounds", 0) + 1,
        }

    return research
