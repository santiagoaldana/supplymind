"""
Phase 3 Integration Test — runs the Buyer Agent directly.
Start the seller server first, then run this file.

  Terminal 1: .venv/bin/python src/seller_agent/server.py
  Terminal 2: .venv/bin/python tests/test_phase3.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.buyer_agent.buyer import run

if __name__ == "__main__":
    run()
