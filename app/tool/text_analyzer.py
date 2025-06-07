"""
Text Analyzer Tool for analyzing and processing text content.
"""

import re
import string
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Tuple
import math

from app.tool.base import BaseTool, ToolResult


class TextAnalyzer(BaseTool):
    """Tool for analyzing and processing text content."""

    name: str = "text_analyzer"
    description: str = """Analyze and process text content.

    Available commands:
    - analyze: Basic text analysis (word count, readability, etc.)
    - sentiment: Simple sentiment analysis
    - keywords: Extract keywords and phrases
    - summarize: Create a simple summary
    - compare: Compare two texts
    - clean: Clean and normalize text
    - translate_case: Convert text case
    - word_frequency: Analyze word frequency
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["analyze", "sentiment", "keywords", "summarize", "compare", "clean", "translate_case", "word_frequency"],
                "type": "string",
            },
            "text": {
                "description": "Text to analyze.",
                "type": "string",
            },
            "text2": {
                "description": "Second text for comparison.",
                "type": "string",
            },
            "file_path": {
                "description": "Path to text file to analyze.",
                "type": "string",
            },
            "case_type": {
                "description": "Case type for conversion (upper, lower, title, sentence).",
                "type": "string",
            },
            "top_n": {
                "description": "Number of top items to show (default: 10).",
                "type": "integer",
            },
            "min_word_length": {
                "description": "Minimum word length for analysis (default: 3).",
                "type": "integer",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        text: Optional[str] = None,
        text2: Optional[str] = None,
        file_path: Optional[str] = None,
        case_type: str = "lower",
        top_n: int = 10,
        min_word_length: int = 3,
        **kwargs
    ) -> ToolResult:
        """Execute text analyzer command."""
        try:
            # Load text from file if provided
            if file_path and not text:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                except FileNotFoundError:
                    return ToolResult(error=f"File not found: {file_path}")
                except Exception as e:
                    return ToolResult(error=f"Error reading file: {str(e)}")

            if command == "analyze":
                return self._analyze_text(text)
            elif command == "sentiment":
                return self._analyze_sentiment(text)
            elif command == "keywords":
                return self._extract_keywords(text, top_n, min_word_length)
            elif command == "summarize":
                return self._summarize_text(text)
            elif command == "compare":
                return self._compare_texts(text, text2)
            elif command == "clean":
                return self._clean_text(text)
            elif command == "translate_case":
                return self._translate_case(text, case_type)
            elif command == "word_frequency":
                return self._word_frequency(text, top_n, min_word_length)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing text analyzer command '{command}': {str(e)}")

    def _analyze_text(self, text: Optional[str]) -> ToolResult:
        """Basic text analysis."""
        try:
            if not text:
                return ToolResult(error="Text is required for analysis")

            # Basic counts
            char_count = len(text)
            char_count_no_spaces = len(text.replace(' ', ''))
            word_count = len(text.split())
            sentence_count = len(re.findall(r'[.!?]+', text))
            paragraph_count = len([p for p in text.split('\n\n') if p.strip()])

            # Average calculations
            avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
            avg_chars_per_word = char_count_no_spaces / word_count if word_count > 0 else 0

            # Readability metrics
            flesch_score = self._calculate_flesch_score(text)

            # Language characteristics
            uppercase_count = sum(1 for c in text if c.isupper())
            lowercase_count = sum(1 for c in text if c.islower())
            digit_count = sum(1 for c in text if c.isdigit())
            punctuation_count = sum(1 for c in text if c in string.punctuation)

            # Most common words
            words = re.findall(r'\b\w+\b', text.lower())
            word_freq = Counter(words)
            common_words = word_freq.most_common(5)

            output = f"Text Analysis Results:\n"
            output += "=" * 40 + "\n"
            output += f"Characters (total): {char_count:,}\n"
            output += f"Characters (no spaces): {char_count_no_spaces:,}\n"
            output += f"Words: {word_count:,}\n"
            output += f"Sentences: {sentence_count:,}\n"
            output += f"Paragraphs: {paragraph_count:,}\n"
            output += f"\nAverages:\n"
            output += f"Words per sentence: {avg_words_per_sentence:.1f}\n"
            output += f"Characters per word: {avg_chars_per_word:.1f}\n"
            output += f"\nReadability:\n"
            output += f"Flesch Reading Ease: {flesch_score:.1f} ({self._flesch_interpretation(flesch_score)})\n"
            output += f"\nCharacter Types:\n"
            output += f"Uppercase: {uppercase_count:,}\n"
            output += f"Lowercase: {lowercase_count:,}\n"
            output += f"Digits: {digit_count:,}\n"
            output += f"Punctuation: {punctuation_count:,}\n"
            output += f"\nMost Common Words:\n"
            for word, count in common_words:
                output += f"  {word}: {count}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error analyzing text: {str(e)}")

    def _analyze_sentiment(self, text: Optional[str]) -> ToolResult:
        """Simple sentiment analysis."""
        try:
            if not text:
                return ToolResult(error="Text is required for sentiment analysis")

            # Simple sentiment word lists
            positive_words = {
                'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
                'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied', 'delighted',
                'perfect', 'brilliant', 'outstanding', 'superb', 'magnificent', 'beautiful',
                'best', 'better', 'positive', 'success', 'win', 'victory', 'triumph'
            }

            negative_words = {
                'bad', 'terrible', 'awful', 'horrible', 'disgusting', 'hate', 'dislike',
                'sad', 'angry', 'frustrated', 'disappointed', 'upset', 'annoyed',
                'worst', 'worse', 'negative', 'fail', 'failure', 'lose', 'loss',
                'problem', 'issue', 'trouble', 'difficult', 'hard', 'impossible'
            }

            # Tokenize and analyze
            words = re.findall(r'\b\w+\b', text.lower())

            positive_count = sum(1 for word in words if word in positive_words)
            negative_count = sum(1 for word in words if word in negative_words)
            neutral_count = len(words) - positive_count - negative_count

            # Calculate sentiment score
            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words == 0:
                sentiment_score = 0
                sentiment_label = "Neutral"
            else:
                sentiment_score = (positive_count - negative_count) / total_sentiment_words
                if sentiment_score > 0.1:
                    sentiment_label = "Positive"
                elif sentiment_score < -0.1:
                    sentiment_label = "Negative"
                else:
                    sentiment_label = "Neutral"

            # Find sentiment words in text
            found_positive = [word for word in words if word in positive_words]
            found_negative = [word for word in words if word in negative_words]

            output = f"Sentiment Analysis Results:\n"
            output += "=" * 40 + "\n"
            output += f"Overall Sentiment: {sentiment_label}\n"
            output += f"Sentiment Score: {sentiment_score:.3f} (-1 to 1)\n"
            output += f"\nWord Counts:\n"
            output += f"Positive words: {positive_count}\n"
            output += f"Negative words: {negative_count}\n"
            output += f"Neutral words: {neutral_count}\n"
            output += f"Total words: {len(words)}\n"

            if found_positive:
                output += f"\nPositive words found:\n"
                pos_freq = Counter(found_positive)
                for word, count in pos_freq.most_common(10):
                    output += f"  {word}: {count}\n"

            if found_negative:
                output += f"\nNegative words found:\n"
                neg_freq = Counter(found_negative)
                for word, count in neg_freq.most_common(10):
                    output += f"  {word}: {count}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error analyzing sentiment: {str(e)}")

    def _extract_keywords(self, text: Optional[str], top_n: int, min_word_length: int) -> ToolResult:
        """Extract keywords and phrases."""
        try:
            if not text:
                return ToolResult(error="Text is required for keyword extraction")

            # Common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
                'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
                'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
                'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
                'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }

            # Extract words
            words = re.findall(r'\b\w+\b', text.lower())

            # Filter words
            filtered_words = [
                word for word in words
                if len(word) >= min_word_length and word not in stop_words
            ]

            # Calculate word frequency
            word_freq = Counter(filtered_words)

            # Extract bigrams (two-word phrases)
            bigrams = []
            for i in range(len(filtered_words) - 1):
                bigram = f"{filtered_words[i]} {filtered_words[i+1]}"
                bigrams.append(bigram)

            bigram_freq = Counter(bigrams)

            # Extract trigrams (three-word phrases)
            trigrams = []
            for i in range(len(filtered_words) - 2):
                trigram = f"{filtered_words[i]} {filtered_words[i+1]} {filtered_words[i+2]}"
                trigrams.append(trigram)

            trigram_freq = Counter(trigrams)

            output = f"Keyword Extraction Results:\n"
            output += "=" * 40 + "\n"
            output += f"Total words analyzed: {len(words)}\n"
            output += f"Unique keywords: {len(word_freq)}\n"

            output += f"\nTop {top_n} Keywords:\n"
            for word, count in word_freq.most_common(top_n):
                percentage = (count / len(filtered_words)) * 100
                output += f"  {word}: {count} ({percentage:.1f}%)\n"

            if bigram_freq:
                output += f"\nTop {min(top_n, 5)} Two-word Phrases:\n"
                for phrase, count in bigram_freq.most_common(min(top_n, 5)):
                    output += f"  {phrase}: {count}\n"

            if trigram_freq:
                output += f"\nTop {min(top_n, 5)} Three-word Phrases:\n"
                for phrase, count in trigram_freq.most_common(min(top_n, 5)):
                    output += f"  {phrase}: {count}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error extracting keywords: {str(e)}")

    def _summarize_text(self, text: Optional[str]) -> ToolResult:
        """Create a simple summary."""
        try:
            if not text:
                return ToolResult(error="Text is required for summarization")

            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            sentences = [s.strip() for s in sentences if s.strip()]

            if len(sentences) <= 3:
                return ToolResult(output=f"Text is already short ({len(sentences)} sentences):\n\n{text}")

            # Simple scoring based on word frequency
            words = re.findall(r'\b\w+\b', text.lower())
            word_freq = Counter(words)

            # Score sentences
            sentence_scores = {}
            for i, sentence in enumerate(sentences):
                sentence_words = re.findall(r'\b\w+\b', sentence.lower())
                score = sum(word_freq[word] for word in sentence_words)
                sentence_scores[i] = score / len(sentence_words) if sentence_words else 0

            # Select top sentences (about 1/3 of original)
            num_summary_sentences = max(1, len(sentences) // 3)
            top_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
            selected_indices = sorted([idx for idx, score in top_sentences[:num_summary_sentences]])

            summary_sentences = [sentences[i] for i in selected_indices]
            summary = '. '.join(summary_sentences) + '.'

            # Calculate compression ratio
            compression_ratio = len(summary) / len(text) * 100

            output = f"Text Summary:\n"
            output += "=" * 40 + "\n"
            output += f"Original: {len(sentences)} sentences, {len(text)} characters\n"
            output += f"Summary: {len(summary_sentences)} sentences, {len(summary)} characters\n"
            output += f"Compression: {compression_ratio:.1f}%\n"
            output += f"\nSummary:\n{summary}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error summarizing text: {str(e)}")

    def _compare_texts(self, text1: Optional[str], text2: Optional[str]) -> ToolResult:
        """Compare two texts."""
        try:
            if not text1 or not text2:
                return ToolResult(error="Both text1 and text2 are required for comparison")

            # Basic metrics
            len1, len2 = len(text1), len(text2)
            words1 = text1.split()
            words2 = text2.split()
            word_count1, word_count2 = len(words1), len(words2)

            # Word frequency analysis
            words1_clean = re.findall(r'\b\w+\b', text1.lower())
            words2_clean = re.findall(r'\b\w+\b', text2.lower())

            freq1 = Counter(words1_clean)
            freq2 = Counter(words2_clean)

            # Common and unique words
            common_words = set(words1_clean) & set(words2_clean)
            unique_to_text1 = set(words1_clean) - set(words2_clean)
            unique_to_text2 = set(words2_clean) - set(words1_clean)

            # Similarity calculation (Jaccard similarity)
            all_words = set(words1_clean) | set(words2_clean)
            jaccard_similarity = len(common_words) / len(all_words) if all_words else 0

            # Most common words in each text
            top_words1 = freq1.most_common(5)
            top_words2 = freq2.most_common(5)

            output = f"Text Comparison Results:\n"
            output += "=" * 40 + "\n"
            output += f"Text 1: {len1} chars, {word_count1} words\n"
            output += f"Text 2: {len2} chars, {word_count2} words\n"
            output += f"\nSimilarity:\n"
            output += f"Jaccard Similarity: {jaccard_similarity:.3f}\n"
            output += f"Common words: {len(common_words)}\n"
            output += f"Unique to Text 1: {len(unique_to_text1)}\n"
            output += f"Unique to Text 2: {len(unique_to_text2)}\n"

            output += f"\nTop words in Text 1:\n"
            for word, count in top_words1:
                output += f"  {word}: {count}\n"

            output += f"\nTop words in Text 2:\n"
            for word, count in top_words2:
                output += f"  {word}: {count}\n"

            if common_words:
                output += f"\nSample common words: {', '.join(list(common_words)[:10])}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error comparing texts: {str(e)}")

    def _clean_text(self, text: Optional[str]) -> ToolResult:
        """Clean and normalize text."""
        try:
            if not text:
                return ToolResult(error="Text is required for cleaning")

            original_length = len(text)

            # Cleaning steps
            cleaned = text

            # Remove extra whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned)

            # Remove leading/trailing whitespace
            cleaned = cleaned.strip()

            # Remove special characters (optional - keeping basic punctuation)
            # cleaned = re.sub(r'[^\w\s.,!?;:-]', '', cleaned)

            # Normalize quotes
            cleaned = re.sub(r'["""]', '"', cleaned)
            cleaned = re.sub(r"['']", "'", cleaned)

            # Remove multiple punctuation
            cleaned = re.sub(r'([.!?]){2,}', r'\1', cleaned)

            # Fix spacing around punctuation
            cleaned = re.sub(r'\s+([,.!?;:])', r'\1', cleaned)
            cleaned = re.sub(r'([,.!?;:])\s*', r'\1 ', cleaned)

            # Remove extra line breaks
            cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)

            new_length = len(cleaned)
            reduction = ((original_length - new_length) / original_length * 100) if original_length > 0 else 0

            output = f"Text Cleaning Results:\n"
            output += "=" * 40 + "\n"
            output += f"Original length: {original_length} characters\n"
            output += f"Cleaned length: {new_length} characters\n"
            output += f"Reduction: {reduction:.1f}%\n"
            output += f"\nCleaned text:\n{cleaned}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error cleaning text: {str(e)}")

    def _translate_case(self, text: Optional[str], case_type: str) -> ToolResult:
        """Convert text case."""
        try:
            if not text:
                return ToolResult(error="Text is required for case conversion")

            if case_type.lower() == "upper":
                converted = text.upper()
            elif case_type.lower() == "lower":
                converted = text.lower()
            elif case_type.lower() == "title":
                converted = text.title()
            elif case_type.lower() == "sentence":
                # Sentence case: first letter of each sentence capitalized
                sentences = re.split(r'([.!?]+)', text)
                converted_sentences = []
                for sentence in sentences:
                    if sentence and not re.match(r'[.!?]+', sentence):
                        sentence = sentence.strip()
                        if sentence:
                            sentence = sentence[0].upper() + sentence[1:].lower()
                    converted_sentences.append(sentence)
                converted = ''.join(converted_sentences)
            else:
                return ToolResult(error=f"Unknown case type: {case_type}")

            output = f"Case Conversion Results:\n"
            output += "=" * 40 + "\n"
            output += f"Conversion type: {case_type.title()}\n"
            output += f"Original length: {len(text)} characters\n"
            output += f"\nConverted text:\n{converted}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error converting case: {str(e)}")

    def _word_frequency(self, text: Optional[str], top_n: int, min_word_length: int) -> ToolResult:
        """Analyze word frequency."""
        try:
            if not text:
                return ToolResult(error="Text is required for word frequency analysis")

            # Extract words
            words = re.findall(r'\b\w+\b', text.lower())

            # Filter by length
            filtered_words = [word for word in words if len(word) >= min_word_length]

            # Calculate frequency
            word_freq = Counter(filtered_words)
            total_words = len(filtered_words)
            unique_words = len(word_freq)

            output = f"Word Frequency Analysis:\n"
            output += "=" * 40 + "\n"
            output += f"Total words: {total_words}\n"
            output += f"Unique words: {unique_words}\n"
            output += f"Vocabulary richness: {unique_words/total_words:.3f}\n"
            output += f"Min word length: {min_word_length}\n"

            output += f"\nTop {top_n} Most Frequent Words:\n"
            for i, (word, count) in enumerate(word_freq.most_common(top_n), 1):
                percentage = (count / total_words) * 100
                output += f"{i:2d}. {word:<15} {count:>5} ({percentage:>5.1f}%)\n"

            # Word length distribution
            length_dist = Counter(len(word) for word in filtered_words)
            output += f"\nWord Length Distribution:\n"
            for length in sorted(length_dist.keys()):
                count = length_dist[length]
                percentage = (count / total_words) * 100
                output += f"{length:2d} chars: {count:>5} words ({percentage:>5.1f}%)\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error analyzing word frequency: {str(e)}")

    def _calculate_flesch_score(self, text: str) -> float:
        """Calculate Flesch Reading Ease score."""
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        syllables = self._count_syllables(text)

        if sentences == 0 or words == 0:
            return 0

        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0, min(100, score))

    def _count_syllables(self, text: str) -> int:
        """Estimate syllable count in text."""
        words = re.findall(r'\b\w+\b', text.lower())
        total_syllables = 0

        for word in words:
            syllables = len(re.findall(r'[aeiouy]+', word))
            if word.endswith('e'):
                syllables -= 1
            if syllables == 0:
                syllables = 1
            total_syllables += syllables

        return total_syllables

    def _flesch_interpretation(self, score: float) -> str:
        """Interpret Flesch Reading Ease score."""
        if score >= 90:
            return "Very Easy"
        elif score >= 80:
            return "Easy"
        elif score >= 70:
            return "Fairly Easy"
        elif score >= 60:
            return "Standard"
        elif score >= 50:
            return "Fairly Difficult"
        elif score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
