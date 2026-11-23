import json
import re

from researchgraph.prompts.system_prompts import REPORT_WRITER


async def write_report(state, model):
    verified = state["verified_findings"]
    gaps = list(state["gaps"])
    if verified:
        response = await model.ainvoke([
            ("system", REPORT_WRITER),
            ("human", json.dumps({"question": state["question"], "verified_findings": verified})),
        ])
        report = response.text
        allowed = {finding["source_url"] for finding in verified}
        cited = set(re.findall(r"\[[^\]]+\]\((https?://[^\s)]+)\)", report))
        if cited - allowed:
            gaps.append("Writer included citations outside the verified evidence; draft withheld.")
            report = "The generated draft failed citation validation. Verified evidence is listed below."
        elif not cited:
            gaps.append("Writer omitted inline source links.")
    else:
        report = "No evidence passed both research and independent verification."
    sources = "\n".join(
        f"- {finding['claim']} [Source]({finding['source_url']})" for finding in verified
    )
    if sources:
        report += "\n\n## Verified evidence\n" + sources
    if gaps or not state["approved"]:
        report = "# Incomplete report\n\n" + report
        report += "\n\n## Unresolved evidence gaps\n" + "\n".join(f"- {gap}" for gap in gaps)
    return {"report": report}
