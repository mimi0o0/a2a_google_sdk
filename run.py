"""
run_all_agents.py - Start ALL 4 agents + orchestrator in ONE command
"""
import subprocess
import time
import os
import sys
from core.config import settings


def main():
    """Start all 4 agents, then run orchestrator"""
    
    # Get API key
    api_key =settings.gemini_api_key

    print("="*80)
    print("  STARTING ALL 4 AGENTS + ORCHESTRATOR")
    print("="*80)
    print()

    # List of agents to start
    agents = [
        ("Outline Agent", "agents/outline_agent.py", 8001),
        ("Writer Agent", "agents/writer_agent.py", 8002),
        ("Editor Agent", "agents/editor_agent.py", 8003),
        ("SEO Agent", "agents/seo_agent.py", 8004),
    ]

    # Start all agents in background processes
    processes = []
    for name, script, port in agents:
        print(f"  Starting {name} (port {port})...")
        try:
            """Start agent as subprocess (background)"""
            p = subprocess.Popen(
              [sys.executable, script],
)
            processes.append((name, p))
        except Exception as e:
            print(f"  ERROR starting {name}: {e}")
            sys.exit(1)

    print()
    print("  ✓ All 4 agents started in background")
    print("  Waiting 3 seconds for agents to boot...")
    time.sleep(3)

    # Get topic from command line
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = "The future of renewable energy in Nepal"

    print()
    print("="*80)
    print("  STARTING ORCHESTRATOR")
    print(f"  Topic: {topic}")
    print("="*80)
    print()

    try:
        """Run orchestrator (blocks until done)"""
        """Make sure client/orchestrator.py exists with corrections"""
        result = subprocess.run(
            [sys.executable, "orchestrator/orchestrator.py", topic],
            check=False
        )

        if result.returncode == 0:
            print()
            print("="*80)
            print("  ✓ SUCCESS - PIPELINE COMPLETE")
            print("="*80)
        else:
            print()
            print("ERROR: Orchestrator failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")

    finally:
        # Clean up - stop all agent processes
        print("\nCleaning up agents...")
        for name, p in processes:
            try:
                p.terminate()
                p.wait(timeout=2)
                print(f"  Stopped {name}")
            except Exception:
                try:
                    p.kill()
                    print(f"  Force killed {name}")
                except Exception:
                    pass

    print("\n✓ Done!")


if __name__ == "__main__":
    main()