from deepagents import create_deep_agent
from langchain.agents.structured_output import ToolStrategy

from researchgraph.prompts.system_prompts import RESEARCHER
from researchgraph.state.evidence import ResearchFindings, has_passage, read_sources


def create_researcher(model, tools):
    agent = create_deep_agent(
        model=model, tools=tools, system_prompt=RESEARCHER,
        response_format=ToolStrategy(ResearchFindings),
    )

    async def research(state):
        result = await agent.ainvoke({"messages": [{
            "role": "user",
            "content": (
                f"Question: {state['question']}\nPlan: {state['plan']}\n"
                f"Previous findings: {state.get('findings', [])}\n"
                f"Review feedback: {state.get('review', '')}"
            ),
        }]})
        findings = result["structured_response"]
        sources = read_sources(result["messages"])
        evidence, gaps = [], list(findings.gaps)
        for number, finding in enumerate(findings.findings, 1):
            item = finding.model_dump()
            item["claim_id"] = f"C{number}"
            if has_passage(finding.source_url, finding.supporting_text, sources):
                evidence.append(item)
            else:
                gaps.append(f"Read a source containing actual supporting text for: {finding.claim}")
        if not evidence:
            gaps.append("No findings with confirmed webpage reads and matching supporting passages.")
        return {"findings": evidence, "research_gaps": gaps, "rounds": state.get("rounds", 0) + 1}

    return research
