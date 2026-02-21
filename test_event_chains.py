import sys
import os

# Set up paths to import game modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from game.game_manager import GameManager
from game.systems.events import EventSystem

def run_test():
    print("Testing Event Chains...")
    gm = GameManager()
    gm.new_game("Test")
    
    # 1. Test succession_crisis
    gm.events.event_memory['succession_crisis'] = True
    gm.events.event_memory['succession_resolved'] = False
    
    initial_happiness = gm.population.happiness
    initial_loyalty = gm.diplomacy.sultan_loyalty
    
    # Simulate turn
    gm._apply_event_memory_effects()
    
    assert gm.population.happiness == initial_happiness - 1, f"Happiness should drop by 1, got {gm.population.happiness}"
    assert gm.diplomacy.sultan_loyalty == initial_loyalty - 2, f"Loyalty should drop by 2, got {gm.diplomacy.sultan_loyalty}"
    
    # 2. Test succession_resolved loyalty boost
    gm.events.event_memory['succession_resolved'] = True
    gm.events.event_memory['succession_loyalty_boost'] = True
    
    # Simulate turn 5 to trigger boost
    gm.turn_count = 5
    gm.diplomacy.sultan_loyalty = 50
    gm._apply_event_memory_effects()
    
    assert gm.diplomacy.sultan_loyalty == 51, f"Loyalty should increase by 1 on turn 5, got {gm.diplomacy.sultan_loyalty}"
    
    print("Event memory effects test passed!")

if __name__ == "__main__":
    run_test()
