import pygame
import os
import logging
import threading
import time

class SoundManager:
    """Manages all game sounds with proper loading, caching, and playback."""
    
    def __init__(self):
        self.sounds = {}
        self.enabled = True
        self.volume = 0.7  # Default volume (0.0 to 1.0)
        
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
                logging.info("[SOUND] Pygame mixer initialized successfully")
            except pygame.error as e:
                logging.error(f"[SOUND] Failed to initialize pygame mixer: {e}")
                self.enabled = False
                return
        
        # Load sound files
        self.load_sounds()
    
    def load_sounds(self):
        """Load all sound files from the assets/Sounds directory."""
        if not self.enabled:
            return
            
        sounds_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'assets', 'Sounds'
        )
        
        if not os.path.exists(sounds_dir):
            logging.warning(f"[SOUND] Sounds directory not found: {sounds_dir}")
            return
        
        # Define sound mappings
        sound_files = {
            'phaser_shot': 'tos_ship_phaser_1.mp3',
            'explosion': 'smallexplosion3.mp3',
            # Add more sounds here as needed
        }
        
        for sound_name, filename in sound_files.items():
            filepath = os.path.join(sounds_dir, filename)
            if os.path.exists(filepath):
                try:
                    sound = pygame.mixer.Sound(filepath)
                    sound.set_volume(self.volume)
                    self.sounds[sound_name] = sound
                    print(f"[SOUND] Loaded sound: {sound_name} from {filename}")
                    logging.info(f"[SOUND] Loaded sound: {sound_name} from {filename}")
                except pygame.error as e:
                    logging.error(f"[SOUND] Failed to load {filename}: {e}")
            else:
                logging.warning(f"[SOUND] Sound file not found: {filepath}")
    
    def play_sound(self, sound_name):
        """Play a sound by name."""
        if not self.enabled or sound_name not in self.sounds:
            if sound_name not in self.sounds:
                print(f"[SOUND] Sound '{sound_name}' not found")
                logging.warning(f"[SOUND] Sound '{sound_name}' not found")
            return
        
        try:
            self.sounds[sound_name].play()
            print(f"[SOUND] Playing sound: {sound_name}")
            logging.debug(f"[SOUND] Playing sound: {sound_name}")
        except pygame.error as e:
            print(f"[SOUND] Failed to play sound {sound_name}: {e}")
            logging.error(f"[SOUND] Failed to play sound {sound_name}: {e}")
    
    def set_volume(self, volume):
        """Set the volume for all sounds (0.0 to 1.0)."""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)
        logging.info(f"[SOUND] Volume set to {self.volume}")
    
    def toggle_enabled(self):
        """Toggle sound on/off."""
        self.enabled = not self.enabled
        logging.info(f"[SOUND] Sound {'enabled' if self.enabled else 'disabled'}")
        return self.enabled
    
    def stop_all(self):
        """Stop all currently playing sounds."""
        if self.enabled:
            pygame.mixer.stop()
            logging.debug("[SOUND] All sounds stopped")
    
    def play_phaser_sequence(self):
        """Play phaser shot followed by explosion sound with proper timing."""
        if not self.enabled:
            return
            
        # Start the sequence in a separate thread to avoid blocking the game
        threading.Thread(target=self._phaser_sequence_thread, daemon=True).start()
    
    def _phaser_sequence_thread(self):
        """Internal method to handle the timed phaser sequence."""
        # Play phaser shot first
        if 'phaser_shot' in self.sounds:
            try:
                phaser_sound = self.sounds['phaser_shot']
                phaser_sound.play()
                print(f"[SOUND] Playing phaser sequence: phaser_shot")
                logging.debug(f"[SOUND] Playing phaser sequence: phaser_shot")
                
                # Use a short, realistic delay for phaser-to-explosion timing
                # Typical Star Trek phaser beam travel time should be very brief
                delay = 0.5  # Half a second - realistic for phaser beam hitting target
                print(f"[SOUND] Using realistic phaser-to-explosion delay: {delay}s")
                time.sleep(delay)
                
            except pygame.error as e:
                print(f"[SOUND] Failed to play phaser_shot: {e}")
                logging.error(f"[SOUND] Failed to play phaser_shot: {e}")
        
        # Play explosion after delay
        if 'explosion' in self.sounds:
            try:
                self.sounds['explosion'].play()
                print(f"[SOUND] Playing phaser sequence: explosion")
                logging.debug(f"[SOUND] Playing phaser sequence: explosion")
            except pygame.error as e:
                print(f"[SOUND] Failed to play explosion: {e}")
                logging.error(f"[SOUND] Failed to play explosion: {e}")

# Global sound manager instance
sound_manager = None

def get_sound_manager():
    """Get the global sound manager instance, creating it if necessary."""
    global sound_manager
    if sound_manager is None:
        sound_manager = SoundManager()
    return sound_manager