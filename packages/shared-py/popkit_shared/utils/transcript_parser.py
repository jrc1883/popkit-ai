"""
Transcript Parser for PopKit Session Recording

Parses Claude Code JSONL transcript files to extract:
- Assistant reasoning (text and extended thinking)
- Token usage per message
- Tool use correlation

Used by html_report_generator to enhance forensic reports with
Claude's decision-making process and cost analysis.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class AssistantMessage:
    """Represents an assistant message from the transcript"""
    text_blocks: List[str]
    thinking_blocks: List[str]
    tool_uses: List[Dict[str, Any]]
    usage: Dict[str, int]
    message_id: str
    timestamp: Optional[str] = None


@dataclass
class TokenUsage:
    """Token usage statistics"""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens +
            self.output_tokens +
            self.cache_creation_input_tokens +
            self.cache_read_input_tokens
        )

    def to_dict(self) -> Dict[str, int]:
        return {
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'cache_creation_input_tokens': self.cache_creation_input_tokens,
            'cache_read_input_tokens': self.cache_read_input_tokens,
            'total_tokens': self.total_tokens
        }


class TranscriptParser:
    """
    Parse Claude Code JSONL transcript files

    Example usage:
        parser = TranscriptParser('/path/to/transcript.jsonl')
        reasoning = parser.get_reasoning_before_tool('toolu_abc123')
        tokens = parser.get_token_usage_for_tool('toolu_abc123')
        total = parser.get_total_token_usage()

    With timestamp filtering (for recording sessions):
        parser = TranscriptParser('/path/to/transcript.jsonl',
                                   start_time='2025-12-26T21:29:00',
                                   end_time='2025-12-26T21:46:00')
    """

    def __init__(self, transcript_path: str,
                 start_time: Optional[str] = None,
                 end_time: Optional[str] = None):
        self.transcript_path = Path(transcript_path)
        self.start_time = start_time
        self.end_time = end_time
        self.entries: List[Dict[str, Any]] = []
        self._parse()

    def _parse(self):
        """Parse JSONL transcript file with optional timestamp filtering"""
        if not self.transcript_path.exists():
            raise FileNotFoundError(f"Transcript not found: {self.transcript_path}")

        with open(self.transcript_path, encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line.strip())

                    # Apply timestamp filtering if start_time/end_time provided
                    if self.start_time or self.end_time:
                        entry_timestamp = entry.get('timestamp')
                        if not entry_timestamp:
                            # Skip entries without timestamps when filtering
                            continue

                        # Check if entry is within time range
                        if self.start_time and entry_timestamp < self.start_time:
                            continue
                        if self.end_time and entry_timestamp > self.end_time:
                            continue

                    self.entries.append(entry)
                except json.JSONDecodeError as e:
                    # Skip malformed lines
                    print(f"Warning: Skipping malformed line {line_num}: {e}")
                    continue

    def get_reasoning_before_tool(self, tool_use_id: str) -> Dict[str, Any]:
        """
        Get Claude's reasoning before a specific tool use

        Returns:
            {
                'text': [list of text blocks],
                'thinking': [list of extended thinking blocks],
                'combined': 'formatted combined reasoning'
            }
        """
        text_blocks = []
        thinking_blocks = []

        # Search for the tool_use in the transcript
        for entry in self.entries:
            if entry.get('type') != 'assistant':
                continue

            message = entry.get('message', {})
            content = message.get('content', [])

            for block in content:
                # Found the tool use
                if block.get('type') == 'tool_use' and block.get('id') == tool_use_id:
                    # Return collected reasoning up to this point
                    return self._format_reasoning(text_blocks, thinking_blocks)

                # Collect text blocks
                elif block.get('type') == 'text':
                    text = block.get('text', '').strip()
                    if text:
                        text_blocks.append(text)

                # Collect thinking blocks
                elif block.get('type') == 'thinking':
                    thinking = block.get('thinking', '').strip()
                    if thinking:
                        thinking_blocks.append(thinking)

        # Tool use not found
        return self._format_reasoning([], [])

    def _format_reasoning(self, text_blocks: List[str], thinking_blocks: List[str]) -> Dict[str, Any]:
        """Format reasoning blocks into a structured response"""
        combined_parts = []

        if text_blocks:
            combined_parts.extend(text_blocks)

        if thinking_blocks:
            for thinking in thinking_blocks:
                combined_parts.append(f"[Extended Thinking]\n{thinking}")

        return {
            'text': text_blocks,
            'thinking': thinking_blocks,
            'combined': '\n\n'.join(combined_parts) if combined_parts else ''
        }

    def get_token_usage_for_tool(self, tool_use_id: str) -> Optional[TokenUsage]:
        """
        Get token usage for the message containing this tool use

        Returns TokenUsage object or None if not found
        """
        for entry in self.entries:
            if entry.get('type') != 'assistant':
                continue

            message = entry.get('message', {})
            content = message.get('content', [])

            # Check if this message contains the tool use
            for block in content:
                if block.get('type') == 'tool_use' and block.get('id') == tool_use_id:
                    # Extract usage from this message
                    usage = message.get('usage', {})
                    return TokenUsage(
                        input_tokens=usage.get('input_tokens', 0),
                        output_tokens=usage.get('output_tokens', 0),
                        cache_creation_input_tokens=usage.get('cache_creation_input_tokens', 0),
                        cache_read_input_tokens=usage.get('cache_read_input_tokens', 0)
                    )

        return None

    def get_total_token_usage(self) -> TokenUsage:
        """Calculate total token usage across entire session"""
        total = TokenUsage()

        for entry in self.entries:
            if entry.get('type') != 'assistant':
                continue

            message = entry.get('message', {})
            usage = message.get('usage', {})

            if usage:
                total.input_tokens += usage.get('input_tokens', 0)
                total.output_tokens += usage.get('output_tokens', 0)
                total.cache_creation_input_tokens += usage.get('cache_creation_input_tokens', 0)
                total.cache_read_input_tokens += usage.get('cache_read_input_tokens', 0)

        return total

    def get_all_tool_uses(self) -> List[Dict[str, Any]]:
        """
        Extract all tool uses from the transcript

        Returns:
            List of dicts with tool_use_id, tool_name, timestamp
        """
        tool_uses = []

        for entry in self.entries:
            if entry.get('type') != 'assistant':
                continue

            message = entry.get('message', {})
            content = message.get('content', [])

            for block in content:
                if block.get('type') == 'tool_use':
                    tool_uses.append({
                        'tool_use_id': block.get('id'),
                        'tool_name': block.get('name'),
                        'input': block.get('input', {}),
                        'message_id': message.get('id')
                    })

        return tool_uses

    def get_assistant_messages(self) -> List[AssistantMessage]:
        """
        Get all assistant messages with their content

        Useful for generating session narratives
        """
        messages = []

        for entry in self.entries:
            if entry.get('type') != 'assistant':
                continue

            message = entry.get('message', {})
            content = message.get('content', [])

            text_blocks = []
            thinking_blocks = []
            tool_uses = []

            for block in content:
                if block.get('type') == 'text':
                    text_blocks.append(block.get('text', ''))
                elif block.get('type') == 'thinking':
                    thinking_blocks.append(block.get('thinking', ''))
                elif block.get('type') == 'tool_use':
                    tool_uses.append({
                        'id': block.get('id'),
                        'name': block.get('name'),
                        'input': block.get('input', {})
                    })

            messages.append(AssistantMessage(
                text_blocks=text_blocks,
                thinking_blocks=thinking_blocks,
                tool_uses=tool_uses,
                usage=message.get('usage', {}),
                message_id=message.get('id', '')
            ))

        return messages

    def calculate_cost(self, usage: TokenUsage) -> float:
        """
        Calculate cost in USD based on Claude Sonnet 4.5 pricing

        Pricing as of December 2025:
        - Input: $3.00 per million tokens
        - Output: $15.00 per million tokens
        - Cache write: $3.75 per million tokens
        - Cache read: $0.30 per million tokens
        """
        PRICING = {
            'input': 3.00 / 1_000_000,
            'output': 15.00 / 1_000_000,
            'cache_write': 3.75 / 1_000_000,
            'cache_read': 0.30 / 1_000_000
        }

        cost = 0.0
        cost += usage.input_tokens * PRICING['input']
        cost += usage.output_tokens * PRICING['output']
        cost += usage.cache_creation_input_tokens * PRICING['cache_write']
        cost += usage.cache_read_input_tokens * PRICING['cache_read']

        return cost


# Convenience function for quick usage
def parse_transcript(transcript_path: str) -> TranscriptParser:
    """Convenience function to create a parser instance"""
    return TranscriptParser(transcript_path)
