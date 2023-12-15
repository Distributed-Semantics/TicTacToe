import threading

class ConsensusManager:
    def __init__(self):
        self.players = []
        self.lock = threading.Lock()

    def add_player(self, player):
        self.players.append(player)

    def start_consensus(self):
        threads = []
        game_states = []

        for player in self.players:
            thread = threading.Thread(target=self.get_game_state, args=(player, game_states))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if self.check_consistency(game_states):
            print("Consistent states")
            return True
        else:
            print("Inconsistent states")
            return False

    def get_game_state(self, player, game_states):
        state = player.get_game_state()
        with self.lock:
            game_states.append(state)

    def check_consistency(self, game_states):
        print("Checking consistency of game states...")
        return all(state == game_states[0] for state in game_states)

    def send(self, message):
        for player in self.players:
            player.send(message.encode("utf-8"))