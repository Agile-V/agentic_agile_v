#!/usr/bin/env python3
"""Simple risk classifier for Agentic Agile-V tasks."""
import argparse

QUESTIONS = [
    ("public_api", "Does it change a public API, interface contract, or persisted data?", 1),
    ("customer_visible", "Is behavior customer-visible or operationally visible?", 1),
    ("security", "Does it affect authentication, authorization, secrets, crypto, or security logging?", 2),
    ("personal_data", "Does it touch personal, customer, regulated, or proprietary data?", 2),
    ("cicd", "Does it affect CI/CD, deployment, infrastructure, or permissions?", 2),
    ("hardware", "Does it affect hardware, firmware, timing, pinout, power, or safety states?", 3),
    ("regulated", "Is the system regulated, safety-critical, irreversible, or money-moving?", 3),
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify task risk level.")
    parser.add_argument("--yes", action="append", default=[], help="Pre-answer a key as yes, e.g. --yes security")
    args = parser.parse_args()

    score = 0
    yes = set(args.yes)
    print("Answer y/n. Use Ctrl-C to exit.\n")
    for key, question, weight in QUESTIONS:
        if key in yes:
            answer = "y"
        else:
            answer = input(f"{question} [{key}] ").strip().lower()[:1]
        if answer == "y":
            score += weight

    if score == 0:
        level = "L0"
    elif score <= 1:
        level = "L1"
    elif score <= 3:
        level = "L2"
    elif score <= 5:
        level = "L3"
    else:
        level = "L4"

    print(f"\nSuggested risk level: {level}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
