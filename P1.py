import socket
import threading
import time
import logging
import json
from HeartbeatManager import HeartbeatManager
from ConsensusManager import ConsensusManager

class GameLogic:
    def __init__(self):
        self.QUIT_COMMAND = "quit"
        self.QUIT_TEXT = "Quitting the game."
        self.grid_size = 6
        self.board = [[" "] * self.grid_size for _ in range(self.grid_size)]
        self.turn = "X"
        self.you = "X"
        self.player2 = "Y"
        self.player3 = "O"
        self.winner = None
        self.game_over = False
        self.counter = 0  # to dtermien a tie if all field are full, counter is 36, we have a tie if no winner etc
        self.other_players = []
        self.hb_players={}
        self.hb1_port=1548
        # Configure logging to write to a file
        logging.basicConfig(filename=f'TicTacLog{self.you}.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
        self.host = "localhost"
        self.port = 9999
        environment = input("Running locally?")
        env_lower = environment.lower()
        if env_lower != "yes":
            player_number = input("What is your player number?")
            self.load_config("config.json", player_number)
        #sm modified it
        # Create a ConsensusManager instance with all players
        self.consensus_manager = ConsensusManager()


        
    def load_config(self, config_file, player):
        try:
            with open(config_file, "r") as f:
                config_data = json.load(f)

            self.host = config_data[player]["host"]
            self.port = config_data[player]["port"]

        except FileNotFoundError:
            print(f"Config file {config_file} not found.")
            logging.info(f"Config file {config_file} not found.")
            exit()
        except json.JSONDecodeError:
            print(f"Error decoding JSON in {config_file}.")
            logging.info(f"Error decoding JSON in {config_file}.")
            exit()
        except KeyError:
            print(f"Invalid configuration for node {self.you}.")
            logging.info(f"Invalid configuration for node {self.you}.")
            exit()
    
    def host_game(self):  # basically does job fo tournament manager?
        try:
            logging.info(f'Started the game')
            host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # we are using tcp
            host_socket.bind((self.host, self.port))
            host_socket.listen(2)  # server needs to listen for 2 connections so that the game can start
            
            print("Waiting for players to connect...")
            player2_socket, player2_address = host_socket.accept()
            self.other_players.append(player2_socket)

            

            print("Player 2 connected!",player2_address)
            logging.info(f"Player 2 connected! {player2_address}")
            player3_socket, player3_address = host_socket.accept()
            self.other_players.append(player3_socket)
            print("Player 3 connected!", player3_address)
            print("If you want to exit the game type 'quit'")
            logging.info(f"Player 3 connected! {player3_address}")

            player2_socket.send("All players connected.".encode())
            player3_socket.send("All players connected.".encode())
            
             # sm modified it from here
            print("All players connected. Starting consensus...")
            if not self.consensus_manager.start_consensus():
                self.inform_disconnect(None, self.other_players)
                return

            print("Consensus reached. Starting the game.")
            # to here

            hb1_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # we are using tcp
            hb1_socket.bind((self.host, self.hb1_port))
            hb1_socket.listen(2)
            hb21_socket, hb21_address = hb1_socket.accept()
            hb31_socket, hb31_address = hb1_socket.accept()
            self.hb_players["P2"]=hb21_socket
            self.hb_players["P3"]=hb31_socket

            threading.Thread(target=self.handle_connection, args=(player2_socket, [player2_socket,player3_socket],self.player2,1)).start()
            threading.Thread(target=self.handle_connection, args=(player3_socket, [player3_socket,player2_socket],self.player3,0)).start()
        
        except socket.error as e:
            print(f"Socket error: {e}")
            self.inform_disconnect(None, self.other_players)
        except Exception as e:
             print(f"An unexpected error occurred: {e}")
             self.inform_disconnect(None, self.other_players)

        # sm modified it
    def get_game_state(self):
        # Return the current game state (in this case, the board)
        return self.board

    def handle_connection(self,player,other_players,symbol,flag):
            try:
                data = player.recv(1024)  # wait for ACK
                if data.decode() == "ACK":
                    print("ACK received.")
                heartbeat_manager = HeartbeatManager("P1", self.hb_players,logging.getLogger())
                heartbeat_manager.hb_start()
                while not self.game_over:
                    if self.turn == self.you and flag==1:  # do we do this for turns
                        
                        # sm modified it
                        self.reach_consensus_before_move(other_players)
                        # to here
                    
                        move = input("Enter a move (row,column): ")
                        if move.lower() == self.QUIT_COMMAND:
                            print("Quitting the game.")
                            self.game_over = True
                            self.inform_disconnect(self.you,other_players)
                            break
                        else:
                            print("move")
                            if self.check_valid_move(move.split(",")):
                                self.apply_move(
                                    move.split(","), self.you,other_players
                                )  
                                logging.info(f"Movement {self.you} {move}")
                                logging.info(f"Board {self.board}")
                                # hadi wstah should have smtg fo share game state w keep track of games state
                                #is this ok to handle turns
                                    # idk maybe look into mroe of how ur gonna ensure consistency w synchro han
                            # invalid move
                                self.turn = self.next_turn()
                                for other_player in other_players:
                                    other_player.send(("move:" + move + "," + self.you).encode("utf-8"))
                                    other_player.send(("next_turn:" + self.turn).encode("utf-8"))
                                print("Valid move, to the next!")                     
                            else:
                                print("Invalid move!")  # what to do in this case? i guess you can enter a new mve hit rak wst loop
                    elif self.turn==symbol:
                        # take in the data received from other players, check why bdbt this nbr
                        data = player.recv(1024)
                        message=data.decode()
                        if not data:
                            # why close clients HNA I GUESS FAULT TOLERANCE
                            # IF SMTG GOES DOWN WHAT TP DO? do we just lose teh con
                            print("no data from ", player)
                            break
                        elif "quitting" in message.lower():
                            self.game_over = True
                            print(f"Player {symbol} has disconnected. Game will quit")
                            self.inform_disconnect(symbol,other_players)
                            break
                        elif message.startswith("WIN"):
                            print("YOU LOOSE!")
                            self.game_over = True
                            exit()
                        elif message.startswith("TIE"):
                            print("IT IS A TIE!")
                            self.game_over = True
                            exit()
                        elif message.startswith("move:"):
                            move, player_symbol = data.decode().split(":")[1].split(",")[:2], data.decode().split(":")[1].split(",")[2]
                            self.apply_move(move, player_symbol,other_players)
                            self.turn = self.next_turn()
                            for other_player in other_players:
                                other_player.send(("next_turn:" + self.turn).encode("utf-8"))
                                print("ha next turn lmn",self.turn)
            except socket.error as e:
                print(f"Socket error: {e}")
                self.inform_disconnect(None, self.other_players)
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                self.inform_disconnect(None, self.other_players)
                
        # sm modified it
    def reach_consensus_before_move(self, other_players):
        print("Requesting consensus before making a move...")
        if not self.consensus_manager.start_consensus():
            self.inform_disconnect(None, other_players)
            return
        print("Consensus reached. Proceeding with the move.")

            
    def next_turn(self):
        if self.turn == self.you:
            return self.player2
        elif self.turn == self.player2:
            return self.player3
        else:
            return self.you
    # WHAT TO DO IF UR THRONW OUT OF THE LOOP CLOSE TEH CLIENTS?
    def apply_move(self, move, player,other_players):  # idk arguments i guess aybano as we go,
        try:
            # i think correct hit player hia bach tayl3bp
            if self.game_over:  # HIT GAME OVER?? MAKHASSOCH YWSL HNA LA KAN GAME OVER NO?
                return
            self.counter += 1
            self.board[int(move[0])][int(move[1])] = player
            self.print_board()
            
            if self.check_for_winner():
                self.game_over = True
                if self.winner == self.you:
                    print("YOU WIN!!")  
                    #broadcast a win, have other players print they lost then quit
                    for other_player in other_players:
                            other_player.send(("WIN" + self.you).encode("utf-8"))
                    self.game_over = True

                else:
                    if self.counter == 36:
                        print("IT IS A TIE!")
                        for other_player in other_players:
                            other_player.send("TIE" + self.you.encode("utf-8"))
                        self.game_over = True
                        #broadcast a tie then quit
                exit()  # should you exit if winner found or hwats the next step thatw e have to do
        except IndexError:
            logging.error("Invalid row or column index. Please choose valid row and column indexes.")
        except ValueError as e:
            logging.error(f"Error: {e}")

    def check_valid_move(self, move):
        try:
            row, col = int(move[0]), int(move[1])
            # Check if the given indices are within the valid range (0 to 5 for a 6x6 board)
            if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                return move != self.QUIT_COMMAND and self.board[row][col] == " "
            else:
                logging.error("Invalid row or column index. Please choose valid row and column indexes.")
                return False
        except ValueError:
            logging.error("Invalid row or column index. Please enter integer values.")
        return False
    
    
    def check_for_winner(self):
        for row in range(6):
            count = 0
            for col in range(5):
                if (
                    self.board[row][col] == self.board[row][col + 1]
                    and self.board[row][col] != " "
                ):
                    count += 1
            if count == 5:
                self.winner = self.board[row][0]
                self.game_over = True
                return True  # NYTHING ELSE TO DO IF TEHRE IS A WINNER???
        for col in range(6):
            count = 0
            for row in range(5):
                if (
                    self.board[row][col] == self.board[row+1][col]
                    and self.board[row][col] != " "
                ):
                    count += 1
            if count == 5:
                self.winner = self.board[0][col]
                self.game_over = True
                return True
        # DIIAG CHECKS
        count_diag1 = 0
        count_diag2 = 0
        for i in range(5):
            if self.board[i][i] == self.board[i + 1][i + 1] and self.board[i][i] != " ":
                count_diag1 += 1
            if (
                self.board[i][5 - i] == self.board[i + 1][4 - i]
                and self.board[i][5 - i] != " "
            ):
                count_diag2 += 1

        if count_diag1 == 5 and self.board[0][0] != " ":
            self.winner = self.board[0][0]
            self.game_over = True
            return True
        elif count_diag2 == 5 and self.board[0][5] != " ":
            self.winner = self.board[0][5]
            self.game_over = True
            return True
        return False
    
    def inform_disconnect(self,disconnected_player, other_players):
        message = "An error occurred. Game will quit" 
        if  disconnected_player:
            message = f"Player {disconnected_player} has disconnected. Game will quit"
    
        for player in other_players:
            player.send(message.encode("utf-8"))
            player.close()

   
    def print_board(self):
        print("\n")
        for row in range(6):
            print(" | ".join(self.board[row]))
            if row != 5:
                print("-----------------------------")
        print("\n")

def main():
    game = GameLogic()
    game.host_game()

if __name__ == "__main__":
    main()
