from researchgraph.prompts.system_prompts import SUPERVISOR


async def supervise(state, model):
    response = await model.ainvoke([
        ("system", SUPERVISOR), ("human", state["question"]),
    ])
    return {"plan": response.text}
