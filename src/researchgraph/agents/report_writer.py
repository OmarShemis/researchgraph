from researchgraph.prompts.system_prompts import REPORT_WRITER


async def write_report(state, model):
    response = await model.ainvoke([
        ("system", REPORT_WRITER),
        ("human", (
            f"Question: {state['question']}\nFindings: {state['findings']}\n"
            f"Analysis: {state['analysis']}\nFact check: {state['review']}"
        )),
    ])
    return {"report": response.text}
