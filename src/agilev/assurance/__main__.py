"""Read-only JSON admission command with explicit trusted-input locations."""
import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path

from .evaluation import evaluate


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def decode(text):
    def invalid_constant(value):
        raise ValueError("non-finite JSON value")
    return json.loads(text, object_pairs_hook=no_duplicates, parse_constant=invalid_constant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", action="store_true")
    parser.add_argument("--trusted-context", type=Path)
    parser.add_argument("--schemas", type=Path)
    args = parser.parse_args()
    if args.manifest:
        print(files(__package__).joinpath("compatibility.json").read_text())
        return 0
    if args.trusted_context is None or args.schemas is None:
        parser.error("--trusted-context and --schemas are required")
    try:
        text = sys.stdin.read(2_000_001)
        if len(text) > 2_000_000:
            raise ValueError("request too large")
        result = evaluate(decode(text), decode(args.trusted_context.read_text()), args.schemas)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ImportError):
        result = {"status": "rejected", "findings": [{"code": "INPUT_INVALID"}]}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "admitted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
