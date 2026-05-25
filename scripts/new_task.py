#!/usr/bin/env python3
"""Create an Agentic Agile-V task package."""
import argparse
import json
from pathlib import Path

TEMPLATE_MAP = {
    "feature": "feature_brief.md",
    "bug": "bug_brief.md",
    "hardware": "hardware_firmware_brief.md",
    "firmware": "hardware_firmware_brief.md",
}

DEFAULT_RISK = {
    "feature": "L2",
    "bug": "L2",
    "hardware": "L4",
    "firmware": "L4",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a task brief, agent plan, and evidence bundle.")
    parser.add_argument("--type", required=True, choices=sorted(TEMPLATE_MAP))
    parser.add_argument("--id", required=True, help="Task id, e.g. AAV-001")
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    task_dir = repo / "tasks" / args.id
    evidence_dir = repo / "evidence" / args.id

    if task_dir.exists() or evidence_dir.exists():
        raise SystemExit(f"Task or evidence directory already exists for {args.id}")

    brief_template = repo / "templates" / TEMPLATE_MAP[args.type]
    plan_template = repo / "templates" / "agent_plan.md"
    evidence_template = repo / "templates" / "evidence_bundle.json"

    brief = read_text(brief_template).replace("AAV-000", args.id).replace("Short feature title.", args.title).replace("Short bug title.", args.title).replace("Short hardware or firmware task title.", args.title)
    plan = read_text(plan_template).replace("AAV-000", args.id)
    bundle = json.loads(read_text(evidence_template))
    bundle["task_id"] = args.id
    bundle["title"] = args.title
    bundle["task_type"] = args.type
    bundle["risk_level"] = DEFAULT_RISK[args.type]
    bundle["brief_path"] = f"tasks/{args.id}/brief.md"
    bundle["plan_path"] = f"tasks/{args.id}/agent_plan.md"

    write_text(task_dir / "brief.md", brief)
    write_text(task_dir / "agent_plan.md", plan)
    write_text(task_dir / "test_plan.md", read_text(repo / "templates" / "test_plan.md").replace("AAV-000", args.id))
    write_text(task_dir / "review_checklist.md", read_text(repo / "templates" / "review_checklist.md"))
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "evidence_bundle.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    (evidence_dir / "logs").mkdir(parents=True, exist_ok=True)

    print(f"Created task package for {args.id}")
    print(f"Brief: {task_dir / 'brief.md'}")
    print(f"Evidence: {evidence_dir / 'evidence_bundle.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
