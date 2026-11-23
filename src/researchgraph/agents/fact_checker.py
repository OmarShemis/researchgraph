from deepagents import create_deep_agent

from researchgraph.prompts.system_prompts import FACT_CHECKER


def create_fact_checker(model, tools):
    verification_tools = [tool for tool in tools if tool.name in {
        "mcp_web_search", "mcp_read_webpage", "mcp_read_pdf",
    }]
    agent = create_deep_agent(
        model=model, tools=verification_tools, system_prompt=FACT_CHECKER,
    )

    async def check_facts(state):
        result = await agent.ainvoke({"messages": [{
            "role": "user",
            "content": (
                f"Question: {state['question']}\nFindings: {state['findings']}\n"
                f"Analysis: {state['analysis']}"
            ),
        }]})
        return {"review": result["messages"][-1].text}

    return check_facts
