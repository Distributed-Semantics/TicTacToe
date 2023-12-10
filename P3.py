import socket
import threading
import time
import logging

class GameLogic:
    def __init__(self):
        self.QUIT_COMMAND = "quit"
        self.QUIT_TEXT = "Quitting the game."
        self.board = [[" "] * 6 for _ in range(6)]
        self.turn = "X"
        self.you = "O"
        self.player2 = "X"
        self.player3 = "Y"
        self.winner = None
        self.game_over = False

        self.counter = 0  # to dtermien a tie if all field are full, counter is 36, we have a tie if no winner etc
        logging.basicConfig(filename=f'TicTacLog{self.you}.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def connect_to_game(self, host, host_port,player,player_port):  # 1 player hosst game teh otehr run connect to game
                logging.info(f'{self.you} started the game')
                host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                host_socket.connect((host, host_port))
                print("Connected to host")

                player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                player_socket.connect((player, player_port))
                player_socket.send("Hello P2".encode())
                data = player_socket.recv(1024)
                message = data.decode()
                if message == "Hello P3":
                    print("P2 and P3 are connected.")
                else:
                    print("Failed to connect to P2.")
                try:
                    print("trying to connect to p2")
                    threading.Thread(target=self.handle_connection, args=(player_socket,"P2",[player_socket,host_socket])).start()
                except:
                    print("Failed to connect to P2.")
                threading.Thread(target=self.handle_connection, args=(host_socket,"P1",[host_socket,player_socket])).start()
                


    def handle_connection(self, client_socket,player,other_players):
        while player=="P1":
            data = client_socket.recv(1024)
            if data.decode() == "All players connected.":
                print("All players connected.")
                print("If you want to exit the game type 'quit'")
                client_socket.send("ACK".encode()) 
                break

        while not self.game_over:
            print(player)
            print("after all players con")
            data = client_socket.recv(1024)
            message = data.decode()
            print(f"Received message: {message} from {player}")

            if "disconnect" in message.lower():
                print(message)
                self.game_over = True
            elif message.startswith("WIN"):
                print("YOU LOOSE!")
                self.game_over = True
                exit()
            elif message.startswith("TIE"):
                print("IT IS A TIE!")
                self.game_over = True
                exit()
            elif message.startswith("move:"):
                print("wst move")
                move, player_symbol = data.decode().split(":")[1].split(",")[:2], data.decode().split(":")[1].split(",")[2]
                if player_symbol != self.you:
                    self.apply_move(move, player_symbol,other_players)
            elif message.startswith("next_turn:"):
                print("wst next turn",message.split(":")[1])
                self.turn=message.split(":")[1]
                # If the message from the host indicates it's this player's turn, make a move
                if message.split(":")[1] == self.you:
                    while True:
                        move = input("Enter your move: ")
                        if move.lower() == self.QUIT_COMMAND:
                            print(self.QUIT_TEXT)
                            for other_player in other_players:
                                other_player.send(self.QUIT_TEXT.encode())
                            self.game_over = True
                            break
                        elif self.check_valid_move(move.split(",")):
                            self.apply_move(move.split(","), self.you,other_players)
                            logging.info(f"Movement {self.you} {move}")
                            logging.info(f"Board {self.board}")
                            # Include the player's symbol in the move message
                            for other_player in other_players:
                                other_player.send(("move:" + move + "," + self.you).encode("utf-8"))
                                print("tsayft")
                            break
                        else:
                            print("invalid move. Try Again.")
            else:
                print("messa",message)
                print("No data received from server.")
                time.sleep(1)

                
                 
    def next_turn(self):
        if self.turn == self.you:
            return self.player2
        elif self.turn == self.player2:
            return self.player3
        else:
            return self.you
    # WHAT TO DO IF UR THRONW OUT OF THE LOOP CLOSE TEH CLIENTS?
    def apply_move(self, move, player,other_players):  # idk arguments i guess aybano as we go,
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
            exit()

    def check_valid_move(self, move):
        return self.board[int(move[0])][int(move[1])] == " "

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

    def print_board(self):
        print("\n")
        for row in range(6):
            print(" | ".join(self.board[row]))
            if row != 5:
                print("--------------------------------")
        print("\n")

game = GameLogic()

environment = input("Running locally?")
env_lower = environment.lower()
if env_lower == "yes":
    port = 9999
    host = "localhost"
    player_port=9998
    player="localhost"
else:
    port = 53217
    host = "svm-11.cs.helsinki.fi"
    player_port=53217
    player="svm-11-2.cs.helsinki.fi"
game.connect_to_game(host, port,player,player_port)