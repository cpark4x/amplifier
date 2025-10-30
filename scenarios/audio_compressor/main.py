"""Audio content compressor using Claude AI.

This tool compresses text content for audiobook generation, reducing length
while preserving key information and narrative flow.
"""

import argparse
import sys
from pathlib import Path
from anthropic import Anthropic


def compress_text(text: str, ratio: float) -> str:
    """Compress text using Claude AI.

    Args:
        text: Input text to compress
        ratio: Target compression ratio (0.0-1.0) - percentage of original words to keep

    Returns:
        Compressed text
    """
    client = Anthropic()

    # Convert ratio to percentage (0.75 → 75%)
    target_percent = int(ratio * 100)

    # Calculate target word count
    original_word_count = len(text.split())
    target_word_count = int(original_word_count * ratio)

    prompt = f"""You are an expert editor compressing text content for audio listening while preserving ALL important information.

CRITICAL: This is COMPRESSION, not summarization. Keep ALL the content, just make it tighter and more concise.

TARGET LENGTH: Exactly {target_word_count} words ({target_percent}% of original {original_word_count} words)

COMPRESSION RULES:

1. **Preserve ALL Content**
   - Keep EVERY major point, argument, and key example
   - Maintain the original structure and chapter flow
   - Don't skip any sections or significant topics
   - The compressed version should cover everything the original covers, just more efficiently

2. **What to Remove/Tighten**
   - Redundant phrasing and unnecessary repetition
   - Filler words and verbose explanations
   - Excessive examples (keep 1-2 best ones per concept, remove the rest)
   - Tangential stories or digressions
   - Over-explanation of simple concepts

3. **What Must Stay**
   - Every major argument and supporting point
   - Key examples and concrete evidence
   - Important details, data, and specifics
   - The logical flow and narrative structure
   - Technical terms and precise language when needed

4. **Compression Techniques**
   - Combine related ideas into single sentences
   - Remove hedging language ("sort of", "kind of", "perhaps")
   - Use active voice and direct phrasing
   - Eliminate redundant adjectives and adverbs
   - Tighten wordy constructions ("in order to" → "to", "due to the fact that" → "because")

5. **Audio Optimization**
   - Natural, conversational phrasing
   - Clear transitions between sections
   - Short, punchy sentences
   - Easy to follow when listening aloud
   - No bullet points or lists (convert to prose)

6. **Word Count Target**
   - Original: {original_word_count} words
   - Target: {target_word_count} words ({target_percent}%)
   - Hit this target as closely as possible (within 5%)

DO NOT:
- Skip entire sections or chapters
- Remove important supporting details
- Dramatically restructure into "key insights" format
- Create an executive summary of highlights only
- Change technical content or core arguments

REMEMBER: The user should get ALL the same information and insights, just delivered more efficiently. This is editorial tightening, not content reduction.

Original text:
{text}

Compress this text to approximately {target_word_count} words while preserving all important content. Return only the compressed text with no meta-commentary."""

    # Calculate max_tokens needed (target word count * 1.5 for safety, min 8000)
    max_tokens = max(8000, int(target_word_count * 1.5))

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=max_tokens,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text


def main() -> int:
    """Main entry point for the audio compressor CLI."""
    parser = argparse.ArgumentParser(
        description="Compress text content for audiobook generation"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to input text file"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output text file"
    )
    parser.add_argument(
        "--ratio",
        type=float,
        default=0.50,
        help="Target compression ratio (0.0-1.0) - percentage of original words to keep (e.g., 0.75 = keep 75%%)"
    )

    args = parser.parse_args()

    try:
        # Read input file
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            return 1

        input_text = input_path.read_text(encoding='utf-8')

        if not input_text.strip():
            print("Error: Input file is empty", file=sys.stderr)
            return 1

        # Compress text
        print(f"Compressing text (target: {int(args.ratio * 100)}% of original)...", file=sys.stderr)
        compressed_text = compress_text(input_text, args.ratio)

        # Write output file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(compressed_text, encoding='utf-8')

        # Calculate stats
        original_words = len(input_text.split())
        compressed_words = len(compressed_text.split())
        actual_ratio = (compressed_words / original_words * 100) if original_words > 0 else 0

        print(f"Compression complete!", file=sys.stderr)
        print(f"Original: {original_words} words", file=sys.stderr)
        print(f"Compressed: {compressed_words} words ({actual_ratio:.1f}%)", file=sys.stderr)
        print(f"Output saved to: {args.output}", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
