import json

from deepagents import create_deep_agent
from langchain.agents.structured_output import ToolStrategy

from researchgraph.prompts.system_prompts import FACT_CHECKER
from researchgraph.state.evidence import VerificationReport, has_passage, read_sources


def create_fact_checker(model, tools):
    verification_tools = [tool for tool in tools if tool.name in {
        "mcp_web_search", "mcp_read_webpage",
    }]
    agent = create_deep_agent(
        model=model, tools=verification_tools, system_prompt=FACT_CHECKER,
        response_format=ToolStrategy(VerificationReport),
    )

    async def check_facts(state):
        result = await agent.ainvoke({"messages": [{
            "role": "user",
            "content": json.dumps({
                "question": state["question"], "plan": state["plan"],
                "findings": state["findings"], "analysis": state["analysis"],
                "research_gaps": state["research_gaps"],
            }),
        }]})
        review = result["structured_response"]
        sources = read_sources(result["messages"])
        checks = {check.claim_id: check for check in review.checks}
        gaps = list(state["research_gaps"]) + list(review.gaps)
        if len(checks) != len(review.checks):
            gaps.append("Fact checker returned duplicate claim IDs; review must be repeated.")
        verified = []
        for finding in state["findings"]:
            check = checks.get(finding["claim_id"])
            if check and check.verdict == "supported" and has_passage(
                check.source_url, check.supporting_text, sources,
            ):
                verified.append({**finding, "source_url": check.source_url,
                                 "supporting_text": check.supporting_text})
            else:
                action = check.correction if check else "Independently check this claim."
                gaps.append(f"{finding['claim_id']}: {finding['claim']} — {action or 'Read supporting evidence.'}")
        if not state["findings"]:
            gaps.append("No evidence-backed findings available for verification.")
        approved = bool(verified) and not gaps
        return {
            "verified_findings": verified, "approved": approved, "gaps": gaps,
            "review": json.dumps({"approved": approved, "corrections": gaps}, ensure_ascii=False),
        }

    return check_facts
