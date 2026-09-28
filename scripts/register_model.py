import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.registry.model_registry import ModelRegistry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--version", type=str, required=True)
    parser.add_argument("--path", type=str, required=True)
    parser.add_argument("--stage", type=str, default="dev")
    args = parser.parse_args()

    registry = ModelRegistry()
    registry.register(args.name, args.version, args.path)
    if args.stage != "dev":
        registry.promote(args.name, args.version, args.stage)
    print(f"Registered {args.name} v{args.version} [{args.stage}]")


if __name__ == "__main__":
    main()
