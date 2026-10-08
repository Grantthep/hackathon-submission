"""Self-learning loop: replay the sample conversations, compare the bot's reply with
the real consultant's reply, and let the editor prompt fix the chatbot prompt.

    python train.py                 # learn from every sample
    python train.py --limit 10      # just the first 10
    python train.py --dry-run 3     # only show predicted vs real replies, don't change the prompt
"""
import argparse
import random

from dotenv import load_dotenv

load_dotenv()

import assistant  # noqa: E402
import data  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="number of samples to learn from")
    parser.add_argument("--shuffle", action="store_true", help="random order (seeded)")
    parser.add_argument("--dry-run", type=int, metavar="N", help="print N comparisons, change nothing")
    args = parser.parse_args()

    samples = data.load_samples()
    if args.shuffle:
        random.Random(42).shuffle(samples)

    if args.dry_run:
        for s in samples[: args.dry_run]:
            print(f"\n=== {s['scenario']}\nCLIENT: {s['clientSequence']}")
            print(f"AI:     {assistant.generate_reply(s['clientSequence'], s['chatHistory'])}")
            print(f"REAL:   {s['consultantReply']}")
        return

    samples = samples[: args.limit] if args.limit else samples
    learned = 0
    for i, s in enumerate(samples, 1):
        result = assistant.improve(
            s["clientSequence"], s["chatHistory"], s["consultantReply"],
            note=f"{s['contactId']}: {s['scenario']}",
        )
        if result["version"]:
            learned += 1
            status = f"v{result['version']}: " + "; ".join(result["changes"])
        else:
            status = f"rejected ({result['rejected']})" if result["rejected"] else "no change needed"
        print(f"[{i}/{len(samples)}] {s['contactId']} -> {status}")
    print(f"\nDone. The prompt changed {learned} time(s). See GET /prompt for the version history.")


if __name__ == "__main__":
    main()
