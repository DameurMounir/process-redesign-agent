from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from process_redesign_agent.decision import render_html_for_run
from process_redesign_agent.redesign import build_comparison


def build_demo_run() -> dict[str, object]:
    comparison = build_comparison(ROOT)
    return {
        "run_id": "PUBLIC-DEMO",
        "status": "AWAITING_HUMAN_SELECTION",
        "comparison_digest": "public-static-preview",
        "comparison": comparison,
        "created_at_utc": "STATIC",
        "decision": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    html = render_html_for_run(build_demo_run()) + "\n"
    target = ROOT / "docs" / "assets" / "default-comparison.html"
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != html:
            print("FAIL: public comparison HTML drifted", file=sys.stderr)
            return 1
        print("PASS: public comparison HTML is byte-stable")
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")
    print("PASS: wrote docs/assets/default-comparison.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
