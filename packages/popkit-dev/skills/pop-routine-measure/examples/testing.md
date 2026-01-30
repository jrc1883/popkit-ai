# Testing

## Manual Testing

Test measurement functionality manually:

```bash
# Enable measurement manually
export POPKIT_ROUTINE_MEASURE=true

# Run a routine
/popkit:routine morning

# Verify measurement file created
ls -la .claude/popkit/measurements/

# Inspect JSON
cat .claude/popkit/measurements/*.json | jq '.'
```

## Verify Tracking

Check that tool calls are being tracked:

```bash
# Enable measurement and run a simple routine
export POPKIT_ROUTINE_MEASURE=true
/popkit:routine morning run pk

# Check that measurement includes tool breakdown
cat .claude/popkit/measurements/pk_*.json | jq '.tool_breakdown'
```

## Dashboard Testing

Test the dashboard display:

```bash
# Create a measurement
/popkit:routine morning --measure

# View the dashboard
python examples/dashboard-implementation.py

# View all measurements
python examples/dashboard-implementation.py --all

# Filter by routine
python examples/dashboard-implementation.py --routine morning
```

## Integration Testing

Test the full workflow:

```bash
# Run routine with measurement
/popkit:routine morning run p-1 --measure

# Verify file created with correct naming
ls .claude/popkit/measurements/p-1_*.json

# Verify data structure
cat .claude/popkit/measurements/p-1_*.json | jq 'keys'

# Verify cost calculation
cat .claude/popkit/measurements/p-1_*.json | jq '.cost_estimate'
```
