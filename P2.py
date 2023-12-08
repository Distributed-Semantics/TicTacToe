import socket
import threading
import time

class GameLogic:
    def __init__(self):
        self.board = [[" "] * 6 for _ in range(6)]
        self.turn = "X"
        self.you = "Y"
        self.player2 = "O"
        self.player3 = "X"
        self.winner = None
        self.game_over = False

        self.counter = 0  # to determine a tie if all fields are full, counter is 36, we have a tie if no winner etc


    def connect_to_game(self, host, port):  # 1 player hosst game teh otehr run connect to game
                host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                host_socket.connect((host, port))

                threading.Thread(target=self.handle_connection, args=(host_socket,)).start()

    def handle_connection(self, client_socket):
        while True:
            data = client_socket.recv(1024)
            if data.decode() == "All players connected.":
                print("All players connected.")
                break
        while not self.game_over:
            print("after all players con")
            data = client_socket.recv(1024)
            message = data.decode()
            if message.startswith("move:"):
                print("wst move")
                move, player_symbol = data.decode().split(":")[1].split(",")[:2], data.decode().split(":")[1].split(",")[2]
                if player_symbol != self.you:
                    self.apply_move(move, player_symbol)
            elif message.startswith("next_turn:"):
                print("wst next turn",message.split(":")[1])
                self.turn=message.split(":")[1]
                # If the message from the host indicates it's this player's turn, make a move
                if message.split(":")[1] == self.you:
                    move = input("Enter your move: ")
                    if self.check_valid_move(move.split(",")):
                        self.apply_move(move.split(","), self.you)
                        # Include the player's symbol in the move message
                        client_socket.send(("move:" + move + "," + self.you).encode())
                    else:
                        print("invalid move")
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
    def apply_move(self, move, player):  # idk arguments i guess aybano as we go,
        # i think correct hit player hia bach tayl3bp
        if self.game_over:  # HIT GAME OVER?? MAKHASSOCH YWSL HNA LA KAN GAME OVER NO?
            return
        self.counter += 1
        self.board[int(move[0])][int(move[1])] = player
        self.print_board()
        if self.check_for_winner():
            self.game_over = True
            if self.winner == self.you:
                print("YOU WIN!!")  # what happens when someone wins???
            elif self.winner == self.player2 or self.winner == self.player3:
                print("YOU LOOSE! :(")
            else:
                if self.counter == 36:
                    print("IT IS A TIE!")
            exit()  # should you exit if winner found or hwats the next step thatw e have to do

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
port = 9999
host = "localhost"
game.connect_to_game(host, port)