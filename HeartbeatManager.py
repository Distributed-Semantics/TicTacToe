# heartbeat_manager.py
import socket
import time
import threading
import logging


class HeartbeatManager:
    def __init__(self, you, other_players,logger):
        self.you = you
        self.other_players = other_players
        self.game_over = False
        self.hb_log={pid: time.time() for pid,player in other_players}
        self.hb_interval=5
        self.timeout=10
        self.logger=logger

    def hb_start(self):
        threading.Thread(target=self.send_heartbeats).start()
        threading.Thread(target=self.receive_heartbeats).start()

    def send_heartbeats(self):
        while not self.game_over:
            for pid,player in self.other_players.items():
                try:
                    message = f"heartbeat from {self.you}"
                    player.send(message.encode())
                except socket.error as e:
                    self.logger.info(f"socket error sending heartbeat to {pid}: {e}")
                except Exception as e:
                    self.logger.info(f"Error sending heartbeat to {pid}: {e}")
            time.sleep(self.hb_interval) 


    def receive_heartbeats(self):
        while not self.game_over:
            for pid,player in self.other_players.items():
                try:
                    message = player.recv(1024).decode()
                    if message:
                        self.logger.info(f"Received heartbeat from {pid}")
                        self.hb_log[pid] = time.time()
                except socket.error as e:
                    self.logger.info(f"socket error receiving heartbeat from {pid}: {e}")
                except Exception as e:
                    self.logger.info(f"Error receiving heartbeat from {pid}: {e}")
            self.check_heartbeats()
            time.sleep(self.hb_interval)

    def check_heartbeats(self):
        for pid,player in self.other_players.items():
            if time.time() - self.hb_log[pid] > self.timeout:
                self.logger.info(f"Player {pid} has timed out")
                self.game_over = True
                