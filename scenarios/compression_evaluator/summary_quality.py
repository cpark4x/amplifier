#!/usr/bin/env python3
"""
Summary Quality Evaluator

Evaluates whether a summary is high quality like Blinkist - not just compressed,
but actually BETTER and more valuable than reading/listening to the original.

Usage:
    python summary_quality.py evaluate <original_file> <summary_file>
"""

import sys
import json
from pathlib import Path
from anthropic import Anthropic


def evaluate_summary_quality(original: str, summary: str) -> dict:
    """Evaluate summary quality from a reader/listener perspective."""
    client = Anthropic()

    prompt = f"""You are a professional content quality evaluator specializing in summaries and condensed content.

Your task: Evaluate whether this SUMMARY is high quality from a consumer perspective.
Think like a Blinkist editor - the summary should be MORE valuable than the original for busy people.

ORIGINAL TEXT (for reference):
{original}

SUMMARY TO EVALUATE:
{summary}

Evaluate on these dimensions (scale 0-10):

1. **Clarity & Insight**: Does it distill complex ideas into clear, memorable insights?
   - Are key concepts explained simply?
   - Are there "aha moments" that crystallize understanding?
   - Would a listener walk away with clear takeaways?

2. **Actionability**: Can the listener DO something with this information?
   - Are there practical tips or recommendations?
   - Is it clear how to apply these insights?
   - Would this change someone's behavior or thinking?

3. **Engagement**: Is this enjoyable and engaging to consume?
   - Does it maintain interest throughout?
   - Is the pacing appropriate for audio?
   - Are there compelling examples or stories?

4. **Completeness**: Does it capture the full picture?
   - Are all major themes covered?
   - Is anything critically important missing?
   - Would a listener feel satisfied they got the "whole story"?

5. **Value Density**: Is every minute worth the listener's time?
   - Does it respect the listener's time?
   - Is there filler or repetition?
   - Could it be even more concise without losing value?

6. **Better Than Original**: Is this BETTER than consuming the original?
   - Would you recommend the summary over the full text?
   - Does it save time without sacrificing understanding?
   - Is it more digestible and memorable?

For each dimension:
- Score (0-10)
- Brief justification
- Specific examples or issues

Also provide:
- **Overall Quality Score** (0-10): Is this Blinkist-quality?
- **Recommendation**: Should we ship this? (YES/NO/REVISE)
- **Strengths**: What makes this summary excellent? (list 3-5)
- **Weaknesses**: What could be better? (list 3-5)
- **Improvement Actions**: Specific edits to make it better (list 3-5)

Respond in JSON format:
{{
  "clarity_insight": {{"score": X, "justification": "...", "examples": ["..."]}},
  "actionability": {{"score": X, "justification": "...", "examples": ["..."]}},
  "engagement": {{"score": X, "justification": "...", "examples": ["..."]}},
  "completeness": {{"score": X, "justification": "...", "examples": ["..."]}},
  "value_density": {{"score": X, "justification": "...", "examples": ["..."]}},
  "better_than_original": {{"score": X, "justification": "...", "examples": ["..."]}},
  "overall_score": X,
  "recommendation": "YES|NO|REVISE",
  "strengths": ["...", "...", "..."],
  "weaknesses": ["...", "...", "..."],
  "improvement_actions": ["...", "...", "..."]
}}"""

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=4000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Extract JSON from response
    response_text = message.content[0].text

    # Find JSON in response (might be wrapped in markdown code blocks)
    if "```json" in response_text:
        json_start = response_text.find("```json") + 7
        json_end = response_text.find("```", json_start)
        json_text = response_text[json_start:json_end].strip()
    elif "```" in response_text:
        json_start = response_text.find("```") + 3
        json_end = response_text.find("```", json_start)
        json_text = response_text[json_start:json_end].strip()
    else:
        json_text = response_text.strip()

    return json.loads(json_text)


def calculate_blinkist_score(evaluation: dict) -> float:
    """Calculate weighted Blinkist-style quality score (0-100)."""
    weights = {
        "clarity_insight": 0.25,
        "actionability": 0.20,
        "engagement": 0.15,
        "completeness": 0.15,
        "value_density": 0.15,
        "better_than_original": 0.10
    }

    weighted_sum = sum(
        evaluation[key]["score"] * weight
        for key, weight in weights.items()
    )

    # Scale to 0-100
    return (weighted_sum / 10) * 100


def format_quality_report(evaluation: dict, stats: dict) -> str:
    """Format evaluation results as a readable report."""
    report = []
    report.append("=" * 80)
    report.append("SUMMARY QUALITY REPORT (Blinkist-Style Evaluation)")
    report.append("=" * 80)
    report.append("")

    # Statistics
    report.append("STATISTICS:")
    report.append(f"  Original:   {stats['original_words']} words (~{stats['original_minutes']:.1f} min listen)")
    report.append(f"  Summary:    {stats['summary_words']} words (~{stats['summary_minutes']:.1f} min listen)")
    report.append(f"  Time Saved: {stats['time_saved']:.1f} minutes ({stats['compression_ratio']:.1%} of original)")
    report.append("")

    # Recommendation
    recommendation_emoji = {
        "YES": "✅",
        "NO": "❌",
        "REVISE": "⚠️"
    }
    emoji = recommendation_emoji.get(evaluation['recommendation'], "")
    report.append(f"RECOMMENDATION: {emoji} {evaluation['recommendation']}")
    report.append(f"OVERALL QUALITY SCORE: {evaluation['overall_score']:.1f}/10")
    report.append(f"BLINKIST-STYLE RATING: {calculate_blinkist_score(evaluation):.1f}/100")
    report.append("")

    # Dimension scores
    report.append("DIMENSION SCORES:")
    dimensions = [
        ("Clarity & Insight", "clarity_insight"),
        ("Actionability", "actionability"),
        ("Engagement", "engagement"),
        ("Completeness", "completeness"),
        ("Value Density", "value_density"),
        ("Better Than Original", "better_than_original")
    ]

    for name, key in dimensions:
        dim = evaluation[key]
        report.append(f"  {name:.<30} {dim['score']:.1f}/10")
        report.append(f"    {dim['justification']}")
        if dim.get('examples'):
            for example in dim['examples'][:2]:
                report.append(f"    • {example}")
        report.append("")

    # Strengths
    if evaluation.get('strengths'):
        report.append("STRENGTHS:")
        for strength in evaluation['strengths']:
            report.append(f"  ✓ {strength}")
        report.append("")

    # Weaknesses
    if evaluation.get('weaknesses'):
        report.append("WEAKNESSES:")
        for weakness in evaluation['weaknesses']:
            report.append(f"  ✗ {weakness}")
        report.append("")

    # Improvement Actions
    if evaluation.get('improvement_actions'):
        report.append("IMPROVEMENT ACTIONS:")
        for i, action in enumerate(evaluation['improvement_actions'], 1):
            report.append(f"  {i}. {action}")
        report.append("")

    report.append("=" * 80)

    return "\n".join(report)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command != "evaluate":
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

    if len(sys.argv) != 4:
        print("Usage: python summary_quality.py evaluate <original_file> <summary_file>")
        sys.exit(1)

    original_file = Path(sys.argv[2])
    summary_file = Path(sys.argv[3])

    if not original_file.exists():
        print(f"Error: Original file not found: {original_file}")
        sys.exit(1)
    if not summary_file.exists():
        print(f"Error: Summary file not found: {summary_file}")
        sys.exit(1)

    original = original_file.read_text()
    summary = summary_file.read_text()

    # Calculate statistics (assuming ~150 words per minute for audio)
    WORDS_PER_MINUTE = 150
    stats = {
        "original_words": len(original.split()),
        "summary_words": len(summary.split()),
    }
    stats["original_minutes"] = stats["original_words"] / WORDS_PER_MINUTE
    stats["summary_minutes"] = stats["summary_words"] / WORDS_PER_MINUTE
    stats["time_saved"] = stats["original_minutes"] - stats["summary_minutes"]
    stats["compression_ratio"] = stats["summary_words"] / stats["original_words"] if stats["original_words"] > 0 else 0

    print("Evaluating summary quality...")
    print(f"Original: {stats['original_words']} words (~{stats['original_minutes']:.1f} min)")
    print(f"Summary: {stats['summary_words']} words (~{stats['summary_minutes']:.1f} min)")
    print(f"Time saved: {stats['time_saved']:.1f} minutes")
    print()

    # Evaluate
    evaluation = evaluate_summary_quality(original, summary)

    # Print report
    report = format_quality_report(evaluation, stats)
    print(report)

    # Output JSON for programmatic use
    output = {
        "statistics": stats,
        "evaluation": evaluation,
        "blinkist_score": calculate_blinkist_score(evaluation)
    }

    print("\nJSON OUTPUT:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
