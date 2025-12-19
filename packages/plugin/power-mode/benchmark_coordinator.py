#!/usr/bin/env python3
"""
Benchmark-Driven Power Mode Coordinator

CLI wrapper for Power Mode coordinator that accepts benchmark task configuration
and orchestrates multi-agent coordination with proper context distribution.

Usage:
    python benchmark_coordinator.py --task-config puzzle-coordination.json --results-dir ./results/test-123/

This script:
1. Reads task configuration from JSON
2. Extracts powerModeConfig with agent roles
3. Spawns agents via Claude CLI with their specific secret contexts
4. Coordinates via Upstash Redis Streams
5. Writes coordination data to results directory
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add power-mode to path
sys.path.insert(0, str(Path(__file__).parent))

from upstash_adapter import get_redis_client, is_upstash_available
from protocol import MessageFactory, MessageType


def spawn_agent(
    agent_id: str,
    agent_name: str,
    secret_context: str,
    puzzle_prompt: str,
    stream_key: str,
    work_dir: str,
    timeout: int = 300
) -> subprocess.Popen:
    """
    Spawn a Claude CLI agent with specific context.

    Returns:
        subprocess.Popen: The running agent process
    """

    # Use absolute path to power-mode directory so agents can import upstash_adapter
    power_mode_dir = str(Path(__file__).parent.absolute())

    # Build the full prompt with secret context and puzzle
    full_prompt = f"""You are {agent_name} (ID: {agent_id}).

Your secret context (DO NOT share the raw data, only your findings):
{secret_context}

{puzzle_prompt}

Coordination Protocol:
1. IMMEDIATELY check in using the Bash tool to run Python code
2. Analyze your secret context
3. Ask questions and share insights with other agents
4. The puzzle is solved when you collectively identify the attack vector

CRITICAL: You MUST use the Bash tool to publish messages to Redis Stream: {stream_key}

To check in and coordinate, use the Bash tool with this Python code:
```bash
python -c "import sys; import time; sys.path.insert(0, r'{power_mode_dir}'); from upstash_adapter import get_redis_client; redis = get_redis_client(); redis.xadd('{stream_key}', {{'agent_id': '{agent_id}', 'type': 'check_in', 'message': 'Your message here', 'timestamp': str(int(time.time() * 1000))}}, maxlen=1000); print('Message published')"
```

START by running the check-in code above, then analyze your data and coordinate.
"""

    # Spawn Claude CLI with the prompt
    # On Windows, use claude.cmd instead of claude
    claude_cmd = 'claude.cmd' if platform.system() == 'Windows' else 'claude'

    print(f"  Spawning Claude CLI for {agent_name}...")
    try:
        # Ensure environment variables are passed to subprocess (especially Upstash creds)
        env = os.environ.copy()

        proc = subprocess.Popen(
            [
                claude_cmd,
                '--no-session-persistence',  # Don't save session to disk
                '--dangerously-skip-permissions'  # Skip tool permission prompts
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=work_dir,
            env=env,
            text=True
        )

        # Send the prompt
        if proc.stdin:
            proc.stdin.write(full_prompt)
            proc.stdin.close()
            print(f"  [OK] Prompt sent to {agent_name}")

        # Quick check if process started
        time.sleep(0.1)
        if proc.poll() is not None:
            # Process already exited
            stdout, stderr = proc.communicate()
            print(f"  [FAIL] {agent_name} exited immediately!")
            print(f"    Exit code: {proc.returncode}")
            if stderr:
                print(f"    Error: {stderr[:500]}")
            return None

        print(f"  [OK] {agent_name} process running (PID: {proc.pid})")
        return proc

    except Exception as e:
        print(f"  [FAIL] Failed to spawn {agent_name}: {e}")
        return None


def run_power_mode_benchmark(
    task_config: Dict[str, Any],
    results_dir: Path,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Run Power Mode coordination benchmark.

    Args:
        task_config: Task configuration with powerModeConfig
        results_dir: Directory to write results
        timeout: Maximum time in seconds

    Returns:
        dict: Results including success, stream data, agent info
    """

    # Validate Upstash availability
    if not is_upstash_available():
        return {
            'success': False,
            'error': 'Upstash Redis not configured',
            'message': 'Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN'
        }

    # Get Redis client
    try:
        redis = get_redis_client()
    except Exception as e:
        return {
            'success': False,
            'error': 'Failed to connect to Upstash',
            'message': str(e)
        }

    # Extract configuration
    power_config = task_config.get('powerModeConfig', {})
    agent_roles = power_config.get('agentRoles', [])
    puzzle_prompt = task_config.get('prompt', '')

    if not agent_roles:
        return {
            'success': False,
            'error': 'No agent roles defined in powerModeConfig'
        }

    # Create stream key
    timestamp = int(time.time() * 1000)
    task_id = task_config.get('id', 'unknown')
    stream_key = f"popkit:stream:test-{task_id}-{timestamp}"

    print(f"\n[POWER MODE COORDINATOR]")
    print(f"Task: {task_id}")
    print(f"Agents: {len(agent_roles)}")
    print(f"Stream: {stream_key}")
    print(f"Results: {results_dir}\n")

    # Create work directory
    work_dir = results_dir / 'workspace'
    work_dir.mkdir(parents=True, exist_ok=True)

    # Write initial files
    initial_files = task_config.get('initialFiles', {})
    for filename, content in initial_files.items():
        file_path = work_dir / filename
        file_path.write_text(content)
        print(f"Created: {filename}")

    # Spawn agents
    agents = []
    for role in agent_roles:
        agent_id = role['id']
        agent_name = role['name']
        secret_context = role['secretContext']

        print(f"\nSpawning {agent_name} ({agent_id})...")

        proc = spawn_agent(
            agent_id=agent_id,
            agent_name=agent_name,
            secret_context=secret_context,
            puzzle_prompt=puzzle_prompt,
            stream_key=stream_key,
            work_dir=str(work_dir),
            timeout=timeout
        )

        if proc is None:
            print(f"[FAIL] Failed to spawn {agent_name}")
            continue

        agents.append({
            'id': agent_id,
            'name': agent_name,
            'process': proc
        })

    if not agents:
        return {
            'success': False,
            'error': 'No agents spawned successfully',
            'streamKey': stream_key,
            'messageCount': 0,
            'duration': 0
        }

    # Monitor coordination
    print(f"\nAgents active ({len(agents)} running). Monitoring coordination for up to {timeout}s...")
    print(f"Stream key: {stream_key}\n")

    start_time = time.time()
    last_message_count = 0

    while time.time() - start_time < timeout:
        # Check if agents are still running
        running_agents = []
        for agent in agents:
            if agent['process'].poll() is None:
                running_agents.append(agent)
            else:
                print(f"[{int(time.time() - start_time)}s] [WARN] {agent['name']} exited (code: {agent['process'].returncode})")
                # Try to read stderr
                try:
                    stderr = agent['process'].stderr.read() if agent['process'].stderr else ''
                    if stderr:
                        print(f"    Error: {stderr[:500]}")
                except:
                    pass

        if not running_agents:
            print(f"\n[FAIL] All agents have exited!")
            break

        # Check Redis stream for new messages
        try:
            messages = redis.xrange(stream_key, '-', '+')
            message_count = len(messages)

            if message_count > last_message_count:
                new_count = message_count - last_message_count
                print(f"[{int(time.time() - start_time)}s] +{new_count} messages (total: {message_count})")
                last_message_count = message_count

                # Check for solution
                for msg_id, fields in messages:
                    content = fields.get('message', '') + fields.get('content', '')
                    if any(keyword in content.lower() for keyword in [
                        'user-agent', 'header manipulation', 'bypass rate limiter'
                    ]):
                        print(f"\n[SUCCESS] SOLUTION DETECTED in message {msg_id}")
                        print(f"Content: {content[:200]}...")

                        # Wait a bit for agents to finish
                        time.sleep(5)

                        # Kill all agents
                        for agent in agents:
                            agent['process'].terminate()

                        # Collect stream data
                        stream_data = {
                            'streamKey': stream_key,
                            'messages': [
                                {
                                    'id': msg_id,
                                    'agent_id': fields.get('agent_id'),
                                    'type': fields.get('type'),
                                    'content': fields.get('message') or fields.get('content'),
                                    'timestamp': fields.get('timestamp')
                                }
                                for msg_id, fields in messages
                            ],
                            'summary': {
                                'totalMessages': len(messages),
                                'puzzleSolved': True,
                                'duration': int(time.time() - start_time)
                            }
                        }

                        # Write to results
                        (results_dir / 'redis-stream.json').write_text(
                            json.dumps(stream_data, indent=2)
                        )

                        return {
                            'success': True,
                            'streamKey': stream_key,
                            'messageCount': len(messages),
                            'duration': int(time.time() - start_time),
                            'puzzleSolved': True
                        }

        except Exception as e:
            print(f"Error checking stream: {e}")

        time.sleep(2)

    # Timeout - kill agents
    print(f"\n[TIMEOUT] Reached {timeout}s limit")
    for agent in agents:
        agent['process'].terminate()

    # Collect final stream data
    try:
        messages = redis.xrange(stream_key, '-', '+')
        stream_data = {
            'streamKey': stream_key,
            'messages': [
                {
                    'id': msg_id,
                    'agent_id': fields.get('agent_id'),
                    'type': fields.get('type'),
                    'content': fields.get('message') or fields.get('content'),
                    'timestamp': fields.get('timestamp')
                }
                for msg_id, fields in messages
            ],
            'summary': {
                'totalMessages': len(messages),
                'puzzleSolved': False,
                'duration': timeout
            }
        }

        (results_dir / 'redis-stream.json').write_text(
            json.dumps(stream_data, indent=2)
        )
    except Exception as e:
        print(f"Error saving stream data: {e}")

    return {
        'success': False,
        'streamKey': stream_key,
        'messageCount': len(messages) if messages else 0,
        'duration': timeout,
        'error': 'Timeout - puzzle not solved'
    }


def main():
    parser = argparse.ArgumentParser(description='Power Mode Benchmark Coordinator')
    parser.add_argument('--task-config', required=True, help='Path to task config JSON')
    parser.add_argument('--results-dir', required=True, help='Results directory')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')

    args = parser.parse_args()

    # Load task config
    with open(args.task_config) as f:
        task_config = json.load(f)

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)

    # Run coordination
    result = run_power_mode_benchmark(
        task_config=task_config,
        results_dir=results_dir,
        timeout=args.timeout
    )

    # Write result
    (results_dir / 'coordinator-result.json').write_text(
        json.dumps(result, indent=2)
    )

    # Print summary
    print("\n" + "="*70)
    print("COORDINATION COMPLETE")
    print("="*70)
    print(f"Success: {result.get('success')}")
    print(f"Stream: {result.get('streamKey')}")
    print(f"Messages: {result.get('messageCount')}")
    print(f"Duration: {result.get('duration')}s")

    if result.get('error'):
        print(f"Error: {result['error']}")

    # Exit with appropriate code
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
