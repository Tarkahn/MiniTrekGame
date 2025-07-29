class EventLogManager:
    """Manages the event log display for game messages."""
    
    def __init__(self, max_lines=25):
        self.event_log = []
        self.max_lines = max_lines
    
    def add_message(self, message):
        """Add a message to the event log, handling newlines."""
        # Split on newlines and handle each part
        for line in message.split('\n'):
            if line.strip():  # Only add non-empty lines
                self.event_log.append(line.strip())
        
        # Keep within max lines limit
        while len(self.event_log) > self.max_lines:
            self.event_log.pop(0)
    
    def get_messages(self):
        """Get all messages in the log."""
        return self.event_log
    
    def clear(self):
        """Clear all messages from the log."""
        self.event_log = []
    
    def get_recent_messages(self, count):
        """Get the most recent N messages."""
        return self.event_log[-count:] if count <= len(self.event_log) else self.event_log