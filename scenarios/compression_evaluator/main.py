#!/usr/bin/env python3
"""
Compression Quality Evaluator

Evaluates the quality of text compression using Claude AI to assess:
- Factual preservation (key information retained)
- Semantic coherence (logical flow maintained)
- Information density (efficiency of compression)
- Readability (ease of understanding)
- Listenability (suitability for audio)

Usage:
    python main.py evaluate <original_text_file> <compressed_text_file>
    python main.py score <original_text> <compressed_text>
"""

import sys
import json
from pathlib import Path
from anthropic import Anthropic


def evaluate_compression(original: str, compressed: str) -> dict:
    """Evaluate compression quality using Claude AI."""
    client = Anthropic()

    prompt = f"""You are an expert evaluator of text compression quality. Analyze how well the compressed text preserves the essential information from the original.

ORIGINAL TEXT:
{original}

COMPRESSED TEXT:
{compressed}

Evaluate the compression on these dimensions (scale 0-10):

1. **Factual Preservation**: Are key facts, names, numbers, and important details retained?
2. **Semantic Coherence**: Does the compressed text maintain logical flow and make sense?
3. **Information Density**: Is the compression efficient? Does each word carry weight?
4. **Readability**: Is it easy to read and understand?
5. **Listenability**: Would this work well as audio content? Natural phrasing?

For each dimension:
- Score (0-10)
- Brief justification (1-2 sentences)
- Specific examples from the text

Also provide:
- **Overall Quality Score** (0-10)
- **Compression Efficiency**: Is the compression ratio appropriate for the quality?
- **Key Losses**: What important information was lost?
- **Improvements**: How could the compression be better?

Respond in JSON format:
{{
  "factual_preservation": {{"score": X, "justification": "...", "examples": ["..."]}},
  "semantic_coherence": {{"score": X, "justification": "...", "examples": ["..."]}},
  "information_density": {{"score": X, "justification": "...", "examples": ["..."]}},
  "readability": {{"score": X, "justification": "...", "examples": ["..."]}},
  "listenability": {{"score": X, "justification": "...", "examples": ["..."]}},
  "overall_score": X,
  "compression_efficiency": "...",
  "key_losses": ["...", "..."],
  "improvements": ["...", "..."]
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


def calculate_summary_score(evaluation: dict) -> float:
    """Calculate weighted summary score (0-100)."""
    weights = {
        "factual_preservation": 0.30,
        "semantic_coherence": 0.25,
        "information_density": 0.20,
        "readability": 0.15,
        "listenability": 0.10
    }

    weighted_sum = sum(
        evaluation[key]["score"] * weight
        for key, weight in weights.items()
    )

    # Scale to 0-100
    return (weighted_sum / 10) * 100


def format_evaluation_report(evaluation: dict, stats: dict) -> str:
    """Format evaluation results as a readable report."""
    report = []
    report.append("=" * 80)
    report.append("COMPRESSION QUALITY EVALUATION REPORT")
    report.append("=" * 80)
    report.append("")

    # Statistics
    report.append("COMPRESSION STATISTICS:")
    report.append(f"  Original:   {stats['original_words']} words, {stats['original_chars']} characters")
    report.append(f"  Compressed: {stats['compressed_words']} words, {stats['compressed_chars']} characters")
    report.append(f"  Ratio:      {stats['compression_ratio']:.1%} (saved {stats['words_saved']} words)")
    report.append("")

    # Overall score
    summary_score = calculate_summary_score(evaluation)
    report.append(f"OVERALL QUALITY SCORE: {evaluation['overall_score']:.1f}/10")
    report.append(f"WEIGHTED SUMMARY:      {summary_score:.1f}/100")
    report.append("")

    # Dimension scores
    report.append("DIMENSION SCORES:")
    dimensions = [
        ("Factual Preservation", "factual_preservation"),
        ("Semantic Coherence", "semantic_coherence"),
        ("Information Density", "information_density"),
        ("Readability", "readability"),
        ("Listenability", "listenability")
    ]

    for name, key in dimensions:
        dim = evaluation[key]
        report.append(f"  {name:.<25} {dim['score']:.1f}/10")
        report.append(f"    {dim['justification']}")
        if dim.get('examples'):
            report.append(f"    Examples: {', '.join(dim['examples'][:2])}")
        report.append("")

    # Efficiency
    report.append("COMPRESSION EFFICIENCY:")
    report.append(f"  {evaluation['compression_efficiency']}")
    report.append("")

    # Key losses
    if evaluation.get('key_losses'):
        report.append("KEY INFORMATION LOSSES:")
        for loss in evaluation['key_losses']:
            report.append(f"  - {loss}")
        report.append("")

    # Improvements
    if evaluation.get('improvements'):
        report.append("SUGGESTED IMPROVEMENTS:")
        for improvement in evaluation['improvements']:
            report.append(f"  - {improvement}")
        report.append("")

    report.append("=" * 80)

    return "\n".join(report)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "evaluate":
        if len(sys.argv) != 4:
            print("Usage: python main.py evaluate <original_file> <compressed_file>")
            sys.exit(1)

        original_file = Path(sys.argv[2])
        compressed_file = Path(sys.argv[3])

        if not original_file.exists():
            print(f"Error: Original file not found: {original_file}")
            sys.exit(1)
        if not compressed_file.exists():
            print(f"Error: Compressed file not found: {compressed_file}")
            sys.exit(1)

        original = original_file.read_text()
        compressed = compressed_file.read_text()

    elif command == "score":
        if len(sys.argv) != 4:
            print("Usage: python main.py score '<original_text>' '<compressed_text>'")
            sys.exit(1)

        original = sys.argv[2]
        compressed = sys.argv[3]

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

    # Calculate statistics
    stats = {
        "original_words": len(original.split()),
        "original_chars": len(original),
        "compressed_words": len(compressed.split()),
        "compressed_chars": len(compressed),
    }
    stats["words_saved"] = stats["original_words"] - stats["compressed_words"]
    stats["compression_ratio"] = stats["compressed_words"] / stats["original_words"] if stats["original_words"] > 0 else 0

    print("Evaluating compression quality...")
    print(f"Original: {stats['original_words']} words")
    print(f"Compressed: {stats['compressed_words']} words ({stats['compression_ratio']:.1%})")
    print()

    # Evaluate
    evaluation = evaluate_compression(original, compressed)

    # Add overall score to evaluation if not present
    if "overall_score" not in evaluation:
        evaluation["overall_score"] = calculate_summary_score(evaluation) / 10

    # Print report
    report = format_evaluation_report(evaluation, stats)
    print(report)

    # Output JSON for programmatic use
    output = {
        "statistics": stats,
        "evaluation": evaluation,
        "summary_score": calculate_summary_score(evaluation)
    }

    print("\nJSON OUTPUT:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
