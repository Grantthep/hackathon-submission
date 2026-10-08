"""Self-learning loop: replay the sample conversations, compare the bot's reply with
the real consultant's reply, and let the editor prompt fix the chatbot prompt.

    python train.py                 # learn from every sample
    python train.py --limit 10      # just the first 10
    python train.py --dry-run 3     # only show predicted vs real replies, don't change the prompt
"""
import argparse
import random
import time

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
        for attempt in range(3):
            try:
                result = assistant.improve(
                    s["clientSequence"], s["chatHistory"], s["consultantReply"],
                    note=f"{s['contactId']}: {s['scenario']}",
                )
                break
            except assistant.llm.LLMError as e:
                # Free tiers have per-minute limits; wait for the window to reset.
                print(f"[{i}/{len(samples)}] {s['contactId']} -> LLM error, retrying in 60s: {str(e)[:100]}", flush=True)
                time.sleep(60)
        else:
            print(f"[{i}/{len(samples)}] {s['contactId']} -> skipped after 3 failures", flush=True)
            continue
        if result["version"]:
            learned += 1
            status = f"v{result['version']}: " + "; ".join(result["changes"])
        else:
            status = f"rejected ({result['rejected']})" if result["rejected"] else "no change needed"
        print(f"[{i}/{len(samples)}] {s['contactId']} -> {status}", flush=True)
    print(f"\nDone. The prompt changed {learned} time(s). See GET /prompt for the version history.")


if __name__ == "__main__":
    main()
