import pygame
import os
import logging
import threading
import time

class SoundManager:
    """Manages all game sounds with proper loading, caching, and playback."""
    
    def __init__(self):
        self.sounds = {}
        self.background_music = None
        self.enabled = True
        self.volume = 0.7  # Default volume (0.0 to 1.0)
        self.music_volume = 0.3  # Background music volume (lower than sound effects)
        
        # Movement sound management
        self.movement_sound_channel = None
        self.movement_fade_thread = None
        
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            try:
                # Set up mixer with more channels for multiple simultaneous sounds
                pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
                pygame.mixer.init()
                pygame.mixer.set_num_channels(8)  # Allow up to 8 simultaneous sounds
                logging.info("[SOUND] Pygame mixer initialized successfully with 8 channels")
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
            'scanner': 'tos_scanner.mp3',
            'keypress': 'tos_keypress2.mp3',
            'warp': 'tmp_warp_clean.mp3',
            'impulse': 'tng_warp_out1.mp3',
            'error': 'tos_keypress2.mp3',  # Use keypress sound for error feedback
            # Add more sounds here as needed
        }
        
        # Define background music files (these will use pygame.mixer.music)
        music_files = {
            'bridge_ambient': 'tng_bridge_3.mp3',
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
        
        # Load background music files
        for music_name, filename in music_files.items():
            filepath = os.path.join(sounds_dir, filename)
            if os.path.exists(filepath):
                try:
                    # Store the filepath for later use with pygame.mixer.music
                    if not hasattr(self, 'music_files'):
                        self.music_files = {}
                    self.music_files[music_name] = filepath
                    print(f"[SOUND] Found background music: {music_name} from {filename}")
                    logging.info(f"[SOUND] Found background music: {music_name} from {filename}")
                except Exception as e:
                    logging.error(f"[SOUND] Failed to register music {filename}: {e}")
            else:
                logging.warning(f"[SOUND] Music file not found: {filepath}")
    
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
    
    def play_background_music(self, music_name='bridge_ambient'):
        """Start playing background music in a loop."""
        if not self.enabled:
            return
        
        if hasattr(self, 'music_files') and music_name in self.music_files:
            try:
                pygame.mixer.music.load(self.music_files[music_name])
                pygame.mixer.music.set_volume(self.music_volume)
                pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                print(f"[SOUND] Started background music: {music_name}")
                logging.info(f"[SOUND] Started background music: {music_name}")
            except pygame.error as e:
                print(f"[SOUND] Failed to play background music {music_name}: {e}")
                logging.error(f"[SOUND] Failed to play background music {music_name}: {e}")
        else:
            print(f"[SOUND] Background music '{music_name}' not found")
            logging.warning(f"[SOUND] Background music '{music_name}' not found")
    
    def stop_background_music(self):
        """Stop the background music."""
        if self.enabled:
            pygame.mixer.music.stop()
            print("[SOUND] Stopped background music")
            logging.info("[SOUND] Stopped background music")
    
    def set_music_volume(self, volume):
        """Set the volume for background music (0.0 to 1.0)."""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled:
            pygame.mixer.music.set_volume(self.music_volume)
        logging.info(f"[SOUND] Music volume set to {self.music_volume}")
    
    def is_music_playing(self):
        """Check if background music is currently playing."""
        return pygame.mixer.music.get_busy() if self.enabled else False
    
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
                logging.debug(f"[SOUND] Playing phaser sequence: phaser_shot")
                
                # Use a short, realistic delay for phaser-to-explosion timing
                # Typical Star Trek phaser beam travel time should be very brief
                delay = 0.5  # Half a second - realistic for phaser beam hitting target
                time.sleep(delay)
                
            except pygame.error as e:
                logging.error(f"[SOUND] Failed to play phaser_shot: {e}")
        
        # Play explosion after delay
        if 'explosion' in self.sounds:
            try:
                self.sounds['explosion'].play()
                logging.debug(f"[SOUND] Playing phaser sequence: explosion")
            except pygame.error as e:
                print(f"[SOUND] Failed to play explosion: {e}")
                logging.error(f"[SOUND] Failed to play explosion: {e}")
    
    def play_movement_sound(self, sound_name, duration_ms):
        """
        Play movement sound for specified duration with smooth fade-out.
        
        Args:
            sound_name: Name of the sound to play ('warp' or 'impulse')
            duration_ms: How long the movement will take in milliseconds
        """
        if not self.enabled or sound_name not in self.sounds:
            if sound_name not in self.sounds:
                print(f"[SOUND] Movement sound '{sound_name}' not found")
                logging.warning(f"[SOUND] Movement sound '{sound_name}' not found")
            return
        
        # Stop any existing movement sound
        self.stop_movement_sound()
        
        try:
            sound = self.sounds[sound_name]
            
            # For very short movements (< 1 second), just play once
            if duration_ms < 1000:
                sound.play()
                print(f"[SOUND] Playing short movement sound: {sound_name} (duration: {duration_ms}ms)")
            else:
                # For longer movements, play looped and schedule fade-out
                self.movement_sound_channel = sound.play(-1)  # -1 means loop indefinitely
                print(f"[SOUND] Started looping movement sound: {sound_name} (duration: {duration_ms}ms)")
                
                # Schedule fade-out in a separate thread
                self.movement_fade_thread = threading.Thread(
                    target=self._movement_fade_thread, 
                    args=(duration_ms,), 
                    daemon=True
                )
                self.movement_fade_thread.start()
                
        except pygame.error as e:
            print(f"[SOUND] Failed to play movement sound {sound_name}: {e}")
            logging.error(f"[SOUND] Failed to play movement sound {sound_name}: {e}")
    
    def stop_movement_sound(self, fade_duration_ms=500):
        """
        Stop movement sound with optional fade-out.
        
        Args:
            fade_duration_ms: Duration of fade-out in milliseconds
        """
        if self.movement_sound_channel and self.movement_sound_channel.get_busy():
            if fade_duration_ms > 0:
                # Start fade-out thread
                threading.Thread(
                    target=self._fade_out_channel, 
                    args=(self.movement_sound_channel, fade_duration_ms), 
                    daemon=True
                ).start()
            else:
                # Immediate stop
                self.movement_sound_channel.stop()
            
            print(f"[SOUND] Stopping movement sound with {fade_duration_ms}ms fade")
            logging.debug(f"[SOUND] Stopping movement sound with {fade_duration_ms}ms fade")
    
    def _movement_fade_thread(self, duration_ms):
        """
        Internal thread to handle movement sound fade-out timing.
        
        Args:
            duration_ms: Total movement duration in milliseconds
        """
        # Wait for most of the movement duration
        fade_start_time = max(duration_ms - 500, duration_ms * 0.8)  # Start fade 500ms before end or at 80% completion
        time.sleep(fade_start_time / 1000.0)
        
        # Start fade-out
        if self.movement_sound_channel and self.movement_sound_channel.get_busy():
            fade_duration = min(500, duration_ms - fade_start_time)  # Fade for remaining time or 500ms max
            self._fade_out_channel(self.movement_sound_channel, fade_duration)
    
    def _fade_out_channel(self, channel, fade_duration_ms):
        """
        Fade out a specific sound channel over time.
        
        Args:
            channel: pygame sound channel to fade
            fade_duration_ms: Duration of fade in milliseconds
        """
        if not channel or not channel.get_busy():
            return
        
        try:
            fade_steps = 20  # Number of volume steps for smooth fade
            step_duration = fade_duration_ms / (fade_steps * 1000.0)  # Convert to seconds
            
            for step in range(fade_steps):
                if not channel.get_busy():
                    break
                
                # Calculate fade volume (1.0 to 0.0)
                fade_volume = 1.0 - (step / fade_steps)
                channel.set_volume(fade_volume * self.volume)
                time.sleep(step_duration)
            
            # Ensure complete stop
            if channel.get_busy():
                channel.stop()
            
            print(f"[SOUND] Completed fade-out over {fade_duration_ms}ms")
            logging.debug(f"[SOUND] Completed fade-out over {fade_duration_ms}ms")
            
        except Exception as e:
            print(f"[SOUND] Error during fade-out: {e}")
            logging.error(f"[SOUND] Error during fade-out: {e}")
            # Fallback: immediate stop
            if channel and channel.get_busy():
                channel.stop()

# Global sound manager instance
sound_manager = None

def get_sound_manager():
    """Get the global sound manager instance, creating it if necessary."""
    global sound_manager
    if sound_manager is None:
        sound_manager = SoundManager()
    return sound_manager