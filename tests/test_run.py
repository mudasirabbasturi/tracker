
import sys
import os
import time
import json
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tracker import SystemTracker, DATA_DIR, QUEUE_FILE

def test_tracker_functions():
    print(f"Testing tracker in {DATA_DIR}")
    
    # Initialize tracker with dummy ID
    tracker = SystemTracker("TEST_EMP_001")
    
    print("Starting tracker...")
    tracker.start()
    
    try:
        # Run for 5 seconds
        for i in range(5):
            print(f"Tracking... {i+1}/5")
            time.sleep(1)
            
            # Simulate some activity check by reading the queue file size
            if os.path.exists(QUEUE_FILE):
                size = os.path.getsize(QUEUE_FILE)
                print(f"Queue file size: {size} bytes")
                
    except KeyboardInterrupt:
        pass
    finally:
        print("Stopping tracker...")
        tracker.stop()
        
    # Verify results
    print("\n--- Verification ---")
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            data = json.load(f)
            print(f"Events captured: {len(data)}")
            if len(data) > 0:
                print("Latest event:", data[-1])
    else:
        print("ERROR: No queue file created.")

if __name__ == "__main__":
    test_tracker_functions()
