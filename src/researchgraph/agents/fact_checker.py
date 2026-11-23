from researchgraph.prompts.system_prompts import FACT_CHECKER


async def check_facts(state, model):
    response = await model.ainvoke([
        ("system", FACT_CHECKER),
        ("human", (
            f"Question: {state['question']}\nFindings: {state['findings']}\n"
            f"Analysis: {state['analysis']}"
        )),
    ])
    return {"review": response.text}
