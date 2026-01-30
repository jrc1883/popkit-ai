# Measurement Data Format

Measurements are saved to `.claude/popkit/measurements/` as JSON files.

## File Structure

```json
{
  "routine_id": "p-1",
  "routine_name": "PopKit Full Validation",
  "start_time": 1734567890.123,
  "end_time": 1734567902.456,
  "duration": 12.333,
  "total_tool_calls": 15,
  "total_tokens": 8023,
  "input_tokens": 1234,
  "output_tokens": 6789,
  "total_chars": 32092,
  "tool_breakdown": {
    "Bash": {
      "count": 8,
      "input_tokens": 691,
      "output_tokens": 2765,
      "duration": 2.34,
      "chars": 13824
    },
    "Read": {
      "count": 4,
      "input_tokens": 425,
      "output_tokens": 1698,
      "duration": 1.12,
      "chars": 8492
    }
  },
  "cost_estimate": {
    "input": 0.0037,
    "output": 0.1018,
    "total": 0.1055
  }
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `routine_id` | string | Routine identifier (pk, p-1, rc-1) |
| `routine_name` | string | Human-readable routine name |
| `start_time` | float | Unix timestamp (seconds) when routine started |
| `end_time` | float | Unix timestamp (seconds) when routine ended |
| `duration` | float | Total execution time in seconds |
| `total_tool_calls` | int | Number of tools invoked |
| `total_tokens` | int | Total tokens (input + output) |
| `input_tokens` | int | Estimated input tokens (~20% of total) |
| `output_tokens` | int | Estimated output tokens (~80% of total) |
| `total_chars` | int | Raw character count |
| `tool_breakdown` | object | Per-tool statistics |
| `cost_estimate` | object | Estimated API costs |

## File Naming Convention

```
.claude/popkit/measurements/
├── pk_20251219_080000.json       # Universal routine
├── p-1_20251219_143022.json      # Custom routine
└── rc-1_20251219_180000.json     # Project routine
```

Format: `{routine_id}_{YYYYMMDD}_{HHMMSS}.json`
