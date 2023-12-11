# heartbeat_manager.py
import socket
import time
import logging
from Constants import HEART_BEAT_TIME, HEART_BEAT_TEXT

class HeartbeatManager:
    def __init__(self, you, other_players):
        self.you = you
        self.other_players = other_players
        self.game_over = False

    def send_heartbeat(self):
        while not self.game_over:
            time.sleep(HEART_BEAT_TIME)  # Send heartbeat every given seconds
            for player in self.other_players:
                try:
                    message = f"{HEART_BEAT_TEXT} from {self.you}"
                    logging.info(message)
                    player.send(message.encode())
                except socket.error as e:
                    logging.error(f"Error sending heartbeat to {player}: {e}")
                except Exception as e:
                    logging.error(f"Error sending heartbeat to {player}: {e}")
