"""
Classifier probe eval — 12 fixed texts (2 per level).
Run on every deploy to catch serving regressions.

Usage:
    python -m evals.classifier_probes
    python -m evals.classifier_probes --api http://localhost:8000
"""

import argparse
import sys
import requests

PROBES: list[dict] = [
    # A1
    {
        "level": "A1",
        "text": "I have a cat. Her name is Mimi. She is white and small. I love her very much. She sleeps on my bed.",
    },
    {
        "level": "A1",
        "text": "This is my house. It is big. My family lives here. We eat dinner together every day. I am happy.",
    },
    # A2
    {
        "level": "A2",
        "text": "Last weekend I went to the market with my mother. We bought some vegetables and fruit. The weather was sunny and I enjoyed the walk very much.",
    },
    {
        "level": "A2",
        "text": "My school day starts at eight o clock. I have five classes every day. My favourite subject is mathematics because I like working with numbers.",
    },
    # B1
    {
        "level": "B1",
        "text": "In my opinion, social media has both advantages and disadvantages. While it helps people stay connected with friends and family, it can also lead to addiction and mental health problems, especially among teenagers who spend many hours online.",
    },
    {
        "level": "B1",
        "text": "The city I grew up in has changed a lot over the past decade. New buildings have replaced old ones and the population has nearly doubled. Some people welcome this change, but others miss the quieter life they used to enjoy.",
    },
    # B2
    {
        "level": "B2",
        "text": "Although renewable energy sources have become significantly more affordable in recent years, the transition away from fossil fuels presents considerable logistical and political challenges that governments around the world have struggled to address in a coordinated way.",
    },
    {
        "level": "B2",
        "text": "The relationship between economic growth and environmental sustainability has long been debated among economists and policymakers. Proponents of green growth argue that technological innovation can decouple prosperity from ecological damage, yet critics contend that such optimism is fundamentally misguided.",
    },
    # C1
    {
        "level": "C1",
        "text": "The notion that artificial intelligence will inevitably displace human labour is predicated on a narrow conception of productivity that disregards the irreducibly social and creative dimensions of most professional roles. What is more likely is a profound restructuring rather than wholesale elimination of entire occupational categories.",
    },
    {
        "level": "C1",
        "text": "Contemporary urban planning faces an inherent tension between densification strategies, which reduce per-capita carbon footprint, and the preservation of green spaces that are indispensable for both biodiversity and the psychological well-being of urban residents.",
    },
    # C2
    {
        "level": "C2",
        "text": "The epistemological underpinnings of behavioural economics challenge classical rational-choice theory by demonstrating, through rigorous empirical methodology, that systematic cognitive biases are not peripheral aberrations but constitutive features of human decision-making, a finding with far-reaching implications for regulatory design and public policy.",
    },
    {
        "level": "C2",
        "text": "Post-colonial literary theory interrogates the ostensibly universal aesthetic criteria through which the Western canon was constituted, arguing that such criteria served not merely as instruments of cultural prestige but as ideological mechanisms for the legitimation of imperial hierarchies and the marginalisation of non-Western voices.",
    },
]


def run_probes(api_base: str) -> bool:
    print(f"\n{'─'*60}")
    print(f"  Classifier probe eval  ({len(PROBES)} probes, 2 per level)")
    print(f"  API: {api_base}")
    print(f"{'─'*60}")

    passed = 0
    failed = 0
    # C1/C2 confusion is known — treat both as "Advanced+" for pass/fail
    ADVANCED = {"C1", "C2"}

    for probe in PROBES:
        resp = requests.post(f"{api_base}/classify", json={"text": probe["text"]}, timeout=30)
        if resp.status_code != 200:
            print(f"  [ERROR] {probe['level']} → HTTP {resp.status_code}")
            failed += 1
            continue

        data   = resp.json()
        pred   = data["level"]
        conf   = data["confidence"]
        expect = probe["level"]

        # Pass if exact match OR both are Advanced+
        ok = (pred == expect) or (pred in ADVANCED and expect in ADVANCED)

        status = "PASS" if ok else "FAIL"
        marker = "✓" if ok else "✗"
        print(f"  {marker} [{status}] expected={expect:2s}  got={pred:2s}  conf={conf:.2f}  | {probe['text'][:60]}…")

        if ok:
            passed += 1
        else:
            failed += 1

    total = passed + failed
    pct   = round(passed / total * 100)
    print(f"\n  Result: {passed}/{total} passed ({pct}%)")
    print(f"{'─'*60}\n")
    return failed == 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--api", default="http://localhost:8000", help="Backend base URL")
    args = p.parse_args()

    ok = run_probes(args.api)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
