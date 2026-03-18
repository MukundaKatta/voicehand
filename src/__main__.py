"""CLI for voicehand."""
import sys, json, argparse
from .core import Voicehand

def main():
    parser = argparse.ArgumentParser(description="VoiceHand — Voice Computer Control. Hands-free computer control using voice commands and AI.")
    parser.add_argument("command", nargs="?", default="status", choices=["status", "run", "info"])
    parser.add_argument("--input", "-i", default="")
    args = parser.parse_args()
    instance = Voicehand()
    if args.command == "status":
        print(json.dumps(instance.get_stats(), indent=2))
    elif args.command == "run":
        print(json.dumps(instance.process(input=args.input or "test"), indent=2, default=str))
    elif args.command == "info":
        print(f"voicehand v0.1.0 — VoiceHand — Voice Computer Control. Hands-free computer control using voice commands and AI.")

if __name__ == "__main__":
    main()
