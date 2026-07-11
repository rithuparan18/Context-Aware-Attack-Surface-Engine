import time
import random
from typing import Dict

class EvasionConfig:
    """
    The Ghost Protocol Configuration.
    Implements request jitter and User-Agent rotation to bypass WAFs during active recon.
    """
    
    def __init__(self, jitter_min_ms: int = 1200, jitter_max_ms: int = 4700):
        self.jitter_min_ms = jitter_min_ms
        self.jitter_max_ms = jitter_max_ms
        
        # A pool of realistic user agents to spoof legitimate traffic
        self.user_agent_pool = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15"
        ]

    def get_random_user_agent(self) -> Dict[str, str]:
        """
        Returns a random User-Agent string formatted as a requests header dictionary.
        """
        return {"User-Agent": random.choice(self.user_agent_pool)}

    def apply_jitter(self) -> float:
        """
        Pauses execution for a randomized duration between min and max jitter.
        Returns the duration slept (in seconds) for logging purposes.
        """
        # Convert ms to seconds for time.sleep
        sleep_time = random.uniform(self.jitter_min_ms, self.jitter_max_ms) / 1000.0
        time.sleep(sleep_time)
        return sleep_time

# Quick standalone test for Day 1 isolation verification
if __name__ == "__main__":
    evasion = EvasionConfig()
    headers = evasion.get_random_user_agent()
    print(f"[*] Generated Headers: {headers}")
    print(f"[*] Applying jitter... waiting...")
    slept_for = evasion.apply_jitter()
    print(f"[*] Execution resumed after {slept_for:.2f} seconds.")
