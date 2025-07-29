import time


class Stardate:
    """Manages the stardate system for the game."""
    
    def __init__(self, start_stardate=2387.0):
        """Initialize stardate system. Standard stardate format: YYYY.DDD where DDD is day of year."""
        self.start_time = time.time()
        self.start_stardate = start_stardate
        self.time_factor = 100.0  # How fast stardate advances (1 real second = 100 stardate units)
    
    def get_current_stardate(self):
        """Get current stardate based on elapsed time."""
        elapsed_time = time.time() - self.start_time
        stardate_advance = elapsed_time * self.time_factor / 86400  # Convert to days
        return self.start_stardate + stardate_advance
    
    def format_stardate(self):
        """Format stardate for display."""
        current = self.get_current_stardate()
        return f"Stardate: {current:.1f}"