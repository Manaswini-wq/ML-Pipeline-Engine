import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    import uvicorn
    print(f"Starting ML Platform on {args.host}:{args.port}")
    uvicorn.run("src.serving.api:app", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
