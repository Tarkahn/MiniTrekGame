"""
Communications Display - Shows incoming messages from enemy ships and other entities.
Supports LLM integration for dynamic message generation.
"""

import pygame
import time
import random
from collections import deque


class CommunicationsDisplay:
    """
    LCARS-style communications display showing incoming transmissions.
    Messages scroll and fade over time.
    """

    def __init__(self, x, y, width, height, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.small_font = pygame.font.Font(None, 16)
        self.header_font = pygame.font.Font(None, 20)

        # LCARS Colors
        self.bg_color = (15, 15, 35)           # Darker blue background
        self.border_color = (153, 204, 255)    # LCARS light blue for comms
        self.header_color = (153, 204, 255)    # Light blue header
        self.text_color = (200, 200, 200)      # Slightly dimmer text
        self.klingon_color = (255, 100, 100)   # Red for Klingon messages
        self.romulan_color = (100, 255, 100)   # Green for Romulan messages
        self.federation_color = (100, 150, 255) # Blue for Federation messages
        self.timestamp_color = (120, 120, 140)  # Gray for timestamps

        # Message queue (max 10 messages, oldest removed first)
        self.messages = deque(maxlen=10)

        # Message display settings
        self.line_height = 14
        self.max_display_lines = (height - 30) // self.line_height  # Reserve space for header

    def add_message(self, sender_name, message_text, faction='unknown', priority='normal'):
        """
        Add a new message to the communications display.

        Args:
            sender_name: Name of the sender (e.g., "IKS Rotarran")
            message_text: The message content
            faction: 'klingon', 'romulan', 'federation', or 'unknown'
            priority: 'normal', 'urgent', or 'distress'
        """
        message = {
            'sender': sender_name,
            'text': message_text,
            'faction': faction,
            'priority': priority,
            'timestamp': time.time(),
            'displayed_at': pygame.time.get_ticks()
        }
        self.messages.append(message)

    def get_faction_color(self, faction):
        """Get the appropriate color for a faction."""
        if faction == 'klingon':
            return self.klingon_color
        elif faction == 'romulan':
            return self.romulan_color
        elif faction == 'federation':
            return self.federation_color
        else:
            return self.text_color

    def wrap_text(self, text, max_width):
        """Wrap text to fit within max_width pixels."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = self.small_font.size(test_line)[0]

            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def draw(self, screen):
        """Draw the communications display."""
        # Background with slight transparency effect
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)

        # Header
        header_text = "SUBSPACE COMMUNICATIONS"
        header_surface = self.header_font.render(header_text, True, self.header_color)
        header_x = self.rect.x + (self.rect.width - header_surface.get_width()) // 2
        screen.blit(header_surface, (header_x, self.rect.y + 5))

        # Draw decorative line under header
        line_y = self.rect.y + 25
        pygame.draw.line(screen, self.border_color,
                        (self.rect.x + 10, line_y),
                        (self.rect.x + self.rect.width - 10, line_y), 1)

        # Draw messages (newest at bottom)
        current_y = self.rect.y + 32
        max_text_width = self.rect.width - 20
        current_time = pygame.time.get_ticks()

        # Calculate how many lines we can display
        available_height = self.rect.height - 40
        lines_to_draw = []

        # Process messages from oldest to newest
        for message in self.messages:
            # Calculate message age for fade effect
            age_ms = current_time - message['displayed_at']

            # Messages start fading after 30 seconds, fully faded at 60 seconds
            if age_ms > 60000:
                alpha = 0.3  # Very faded but still visible
            elif age_ms > 30000:
                alpha = 1.0 - ((age_ms - 30000) / 30000) * 0.7
            else:
                alpha = 1.0

            faction_color = self.get_faction_color(message['faction'])

            # Sender line
            sender_text = f"[{message['sender']}]:"

            # Wrap message text
            wrapped_lines = self.wrap_text(message['text'], max_text_width - 10)

            # Add sender and message lines
            lines_to_draw.append({
                'text': sender_text,
                'color': faction_color,
                'alpha': alpha,
                'is_sender': True
            })

            for line in wrapped_lines:
                lines_to_draw.append({
                    'text': f"  {line}",
                    'color': self.text_color,
                    'alpha': alpha,
                    'is_sender': False
                })

            # Add small spacing between messages
            lines_to_draw.append({'text': '', 'color': None, 'alpha': 0, 'is_sender': False, 'spacer': True})

        # Only show the most recent lines that fit
        max_lines = available_height // self.line_height
        if len(lines_to_draw) > max_lines:
            lines_to_draw = lines_to_draw[-max_lines:]

        # Draw the lines
        for line_info in lines_to_draw:
            if line_info.get('spacer'):
                current_y += 4  # Small gap between messages
                continue

            if not line_info['text']:
                continue

            # Apply alpha to color
            base_color = line_info['color']
            alpha = line_info['alpha']
            faded_color = (
                int(base_color[0] * alpha),
                int(base_color[1] * alpha),
                int(base_color[2] * alpha)
            )

            text_surface = self.small_font.render(line_info['text'], True, faded_color)
            screen.blit(text_surface, (self.rect.x + 10, current_y))
            current_y += self.line_height

            if current_y > self.rect.y + self.rect.height - 10:
                break

        # If no messages, show "NO INCOMING TRANSMISSIONS"
        if not self.messages:
            no_msg_text = "NO INCOMING TRANSMISSIONS"
            no_msg_surface = self.small_font.render(no_msg_text, True, self.timestamp_color)
            no_msg_x = self.rect.x + (self.rect.width - no_msg_surface.get_width()) // 2
            no_msg_y = self.rect.y + self.rect.height // 2
            screen.blit(no_msg_surface, (no_msg_x, no_msg_y))

    def clear_messages(self):
        """Clear all messages."""
        self.messages.clear()


class EnemyCommunicationsManager:
    """
    Manages enemy ship communications.
    Generates contextual messages based on combat state.
    Can integrate with LLM APIs for dynamic content.
    """

    # Fallback message templates when LLM is not available
    KLINGON_THREATS = [
        "Today is a good day to die, human!",
        "Your ship will make a fine trophy!",
        "Surrender and I may grant you a warrior's death!",
        "The Empire will crush your Federation!",
        "You fight without honor!",
        "Prepare to meet Kahless!",
        "Your shields are weakening, petaQ!",
        "I will drink bloodwine from your skull!",
        "Qapla'! Victory will be ours!",
        "You cannot escape the wrath of the Empire!",
    ]

    KLINGON_TAUNTS = [
        "Is that the best the Federation can do?",
        "My grandmother fights better than you!",
        "Your weapons tickle like a targ's tongue!",
        "Ha! You call that a phaser?",
        "Federation cowards! Stand and fight!",
        "Run, human! Show your true nature!",
        "Your tactics are as predictable as a Ferengi's greed!",
    ]

    KLINGON_DAMAGE_TAKEN = [
        "A lucky shot! It will not happen again!",
        "You have earned my respect, but not my mercy!",
        "Good! A worthy opponent at last!",
        "That one hurt! Now I am angry!",
        "You fight well for a human!",
    ]

    KLINGON_RETREATING = [
        "This battle is not over, human!",
        "We will meet again!",
        "I withdraw to fight another day!",
        "Consider this a tactical withdrawal!",
        "The Empire will have its revenge!",
    ]

    ROMULAN_THREATS = [
        "Your destruction is... inevitable.",
        "The Tal Shiar will be most interested in your ship's debris.",
        "How unfortunate that you ventured into our space.",
        "The Star Empire does not forgive trespassers.",
        "You have made a grave error in judgment.",
        "Surrender your vessel. Resistance is illogical.",
        "We have been watching you. Waiting.",
    ]

    ROMULAN_TAUNTS = [
        "Your Federation is so... predictable.",
        "Did you think your cloak of diplomacy would protect you?",
        "Amusing. You believe you can outmaneuver us.",
        "Your captain is either brave or foolish. Perhaps both.",
        "We knew your course before you did.",
    ]

    ROMULAN_DAMAGE_TAKEN = [
        "An unexpected maneuver. It will not be repeated.",
        "You have... inconvenienced us.",
        "This changes nothing.",
        "A minor setback.",
        "Impressive. For a human.",
    ]

    ROMULAN_RETREATING = [
        "This engagement no longer serves our purposes.",
        "We have gathered sufficient data. For now.",
        "The Senate will hear of this.",
        "Do not mistake withdrawal for defeat.",
        "We shall meet again, Captain. Count on it.",
    ]

    def __init__(self, communications_display):
        self.display = communications_display
        self.last_message_time = {}  # Track last message time per enemy
        self.message_cooldown = 8000  # Minimum ms between messages from same enemy
        self.llm_enabled = False
        self.llm_api_key = None
        self.llm_endpoint = None

    def configure_llm(self, api_key, endpoint="https://api.openai.com/v1/chat/completions", model="gpt-3.5-turbo"):
        """
        Configure LLM integration for dynamic message generation.

        Args:
            api_key: Your OpenAI API key (or compatible API)
            endpoint: API endpoint URL
            model: Model to use (default: gpt-3.5-turbo)

        Example usage:
            comms_manager.configure_llm(
                api_key="sk-your-api-key-here",
                endpoint="https://api.openai.com/v1/chat/completions",
                model="gpt-3.5-turbo"
            )
        """
        self.llm_api_key = api_key
        self.llm_endpoint = endpoint
        self.llm_model = model
        self.llm_enabled = True
        print(f"[COMMS] LLM integration enabled with model: {model}")

    def disable_llm(self):
        """Disable LLM integration and use fallback messages."""
        self.llm_enabled = False
        print("[COMMS] LLM integration disabled, using fallback messages")

    def _generate_llm_message(self, enemy_ship, context, callback=None):
        """
        Generate a message using the configured LLM.
        This runs asynchronously to avoid blocking the game loop.

        Args:
            enemy_ship: The enemy ship object
            context: Combat context ('threat', 'taunt', 'damage_taken', 'retreating')
            callback: Optional callback function to receive the generated message

        Returns:
            str: Generated message or None if async
        """
        if not self.llm_enabled or not self.llm_api_key:
            return None

        # Build the prompt
        faction = getattr(enemy_ship, 'faction', 'klingon')
        ship_name = getattr(enemy_ship, 'name', 'Enemy Ship')

        system_prompt = self._get_system_prompt(faction)
        user_prompt = self._get_context_prompt(context, faction)

        # For synchronous usage (simpler but blocks game loop)
        # In production, you'd want to use threading or asyncio
        try:
            import requests

            headers = {
                "Authorization": f"Bearer {self.llm_api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "max_tokens": 50,
                "temperature": 0.9
            }

            response = requests.post(
                self.llm_endpoint,
                headers=headers,
                json=data,
                timeout=2  # Short timeout to not block game too long
            )

            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']['content'].strip()
                # Remove quotes if the LLM wrapped the message in them
                message = message.strip('"\'')
                return message

        except Exception as e:
            print(f"[COMMS] LLM request failed: {e}")

        return None

    def _get_system_prompt(self, faction):
        """Get the system prompt for the LLM based on faction."""
        if faction == 'klingon':
            return """You are a Klingon warrior captain in Star Trek. You speak with honor, aggression, and pride.
You use Klingon phrases occasionally (like Qapla', petaQ, targ). Your responses are short (1-2 sentences),
dramatic, and warrior-like. You value combat, honor, and glory. Never break character."""
        elif faction == 'romulan':
            return """You are a Romulan commander in Star Trek. You speak with cold intelligence, subtle menace, and superiority.
Your responses are short (1-2 sentences), calculated, and ominous. You are cunning, secretive, and view others as inferior.
You reference the Star Empire and occasionally hint at surveillance. Never break character."""
        else:
            return """You are an alien starship captain. You speak with authority and menace.
Your responses are short (1-2 sentences). Never break character."""

    def _get_context_prompt(self, context, faction):
        """Get the user prompt based on combat context."""
        prompts = {
            'threat': "Generate a threatening message to the Federation ship you're about to attack.",
            'taunt': "Generate a taunting message mocking the Federation ship's combat performance.",
            'damage_taken': "Generate a response after your ship took damage - acknowledge it but remain defiant.",
            'retreating': "Generate a message as you withdraw from battle - hint you'll return.",
            'victory': "Generate a triumphant message as you're about to destroy the enemy.",
            'detecting': "Generate a message upon first detecting the Federation ship.",
        }
        return prompts.get(context, prompts['threat'])

    def _get_fallback_message(self, faction, context):
        """Get a random fallback message when LLM is unavailable."""
        if faction == 'klingon':
            messages = {
                'threat': self.KLINGON_THREATS,
                'taunt': self.KLINGON_TAUNTS,
                'damage_taken': self.KLINGON_DAMAGE_TAKEN,
                'retreating': self.KLINGON_RETREATING,
            }
        elif faction == 'romulan':
            messages = {
                'threat': self.ROMULAN_THREATS,
                'taunt': self.ROMULAN_TAUNTS,
                'damage_taken': self.ROMULAN_DAMAGE_TAKEN,
                'retreating': self.ROMULAN_RETREATING,
            }
        else:
            # Default to Klingon messages for unknown factions
            messages = {
                'threat': self.KLINGON_THREATS,
                'taunt': self.KLINGON_TAUNTS,
                'damage_taken': self.KLINGON_DAMAGE_TAKEN,
                'retreating': self.KLINGON_RETREATING,
            }

        message_list = messages.get(context, messages['threat'])
        return random.choice(message_list)

    def send_enemy_message(self, enemy_ship, context='threat', force=False):
        """
        Send a message from an enemy ship to the player.

        Args:
            enemy_ship: The enemy ship object
            context: 'threat', 'taunt', 'damage_taken', 'retreating', 'victory', 'detecting'
            force: If True, bypass cooldown check

        Returns:
            bool: True if message was sent, False if on cooldown
        """
        current_time = pygame.time.get_ticks()
        enemy_id = id(enemy_ship)

        # Check cooldown
        if not force and enemy_id in self.last_message_time:
            if current_time - self.last_message_time[enemy_id] < self.message_cooldown:
                return False

        # Get ship info
        ship_name = getattr(enemy_ship, 'name', 'Enemy Ship')
        faction = getattr(enemy_ship, 'faction', 'klingon')

        # Try LLM first, fall back to templates
        message = None
        if self.llm_enabled:
            message = self._generate_llm_message(enemy_ship, context)

        if not message:
            message = self._get_fallback_message(faction, context)

        # Send to display
        self.display.add_message(ship_name, message, faction)
        self.last_message_time[enemy_id] = current_time

        return True

    def on_combat_start(self, enemy_ship):
        """Called when combat begins with an enemy."""
        self.send_enemy_message(enemy_ship, 'threat', force=True)

    def on_enemy_damaged(self, enemy_ship):
        """Called when an enemy takes significant damage."""
        # 30% chance to comment on taking damage
        if random.random() < 0.3:
            self.send_enemy_message(enemy_ship, 'damage_taken')

    def on_player_damaged(self, enemy_ship):
        """Called when the player takes damage from this enemy."""
        # 25% chance to taunt
        if random.random() < 0.25:
            self.send_enemy_message(enemy_ship, 'taunt')

    def on_enemy_retreating(self, enemy_ship):
        """Called when an enemy starts retreating."""
        self.send_enemy_message(enemy_ship, 'retreating', force=True)

    def on_enemy_detecting_player(self, enemy_ship):
        """Called when an enemy first detects the player."""
        self.send_enemy_message(enemy_ship, 'detecting', force=True)


def create_communications_display(x, y, width, height, font):
    """Factory function to create a communications display."""
    return CommunicationsDisplay(x, y, width, height, font)
