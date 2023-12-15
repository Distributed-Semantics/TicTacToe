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
        self.timeout=6
        self.logger=logger
        self.hb_success = True
        

    def set_geme_over(self,is_game_over):
        self.game_over = is_game_over

    def hb_start(self):
        self.pid_array = [pid for pid in self.other_players] 
        self.pid_array.append(self.you)
        self.player_status = {pid: {other_pid: True for other_pid in self.pid_array} for pid in self.pid_array}
        threading.Thread(target=self.send_heartbeats,daemon=True).start()
        threading.Thread(target=self.receive_heartbeats,daemon=True).start()

    def send_heartbeats(self):
        while not self.game_over and self.hb_success:
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
        try:
            while not self.game_over and self.hb_success:
                for pid,player in self.other_players.items():
                        message = player.recv(1024).decode()
                        if message:
                            if "Player has timed out" in message:
                                self.logger.info(message)
                                server_name = message.split('-')[1]
                                self.update_player_status(pid,server_name,False)
                                self.hb_counsensus(server_name)
                            else:   
                                self.logger.info(f"Received heartbeat from {pid}")
                                self.hb_log[pid] = time.time()
                                self.update_player_status(self.you,pid,True)
                                
                        
                self.check_heartbeats()
                time.sleep(self.hb_interval)
        except socket.error as e:
                self.update_player_status(pid,pid,False)

        except Exception as e:
                self.update_player_status(pid,pid,False)

    def check_heartbeats(self):
            if len(self.hb_log) > 0:
                for pid,player in self.other_players.items():
                    if time.time() - self.hb_log[pid] > self.timeout:
                        self.logger.info(f"Player has timed out {pid}")
                        self.player_status[self.you][pid] = False
                        for pid,player in self.other_players.items():
                                player.send(f" Player has timed out -{pid}- ".encode())

    def hb_counsensus(self, down_player):
        self.logger.info("Enter hb_counsensus")
        down_players_count = sum(1 for outer_key, inner_dict in self.player_status.items() if down_player in inner_dict and not inner_dict[down_player])
        active_players_count = sum(1 for inner_dict in self.player_status.values() if down_player in inner_dict and inner_dict[down_player])
        if(down_players_count > active_players_count):
            self.hb_success = False
            self.inform_disconnect("hb consensus agreed", self.other_players)
        
   
    def inform_disconnect(self,message, other_players):
        try:
            for pid,player in self.other_players.items():
                player.send(message.encode("utf-8"))
                player.close()
                self.logger.info("Disconnect informed, quitting the game")
                exit()
        except Exception as e:
            self.logger.error("Error on informing disconnect, server might be down")
                
    def update_player_status(self,key, item, value):
         if key in self.player_status and item in self.player_status[key]:
            self.player_status[key][item] = value
        

        
                