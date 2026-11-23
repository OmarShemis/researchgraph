from researchgraph.prompts.system_prompts import ANALYST


async def analyze(state, model):
    response = await model.ainvoke([
        ("system", ANALYST),
        ("human", f"Question: {state['question']}\nFindings: {state['findings']}"),
    ])
    return {"analysis": response.text}
