import math
from typing import List
from treys import Deck, Evaluator, Card
import matplotlib.pyplot as plt
from multiprocessing import Pool, cpu_count
import numpy as np
from scipy.stats import norm
import torch
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_directory, "pokertorch.pt")
pokertorch = torch.jit.load(model_path)
device = torch.device("cpu")  # Set device to CPU explicitly
pokertorch = pokertorch.to(device)

class Hand:
    def __init__(self, cards):
        self.cards = cards

def deal_opponents(n: int, deck: Deck) -> List[Hand]:
    return [Hand(deck.draw(2)) for _ in range(n)]

def fill_board(deck: Deck, board: List[int], stage: int):
    stage = 5
    output = board + deck.draw(stage - len(board))
    return output

def single_trial(player_hand: Hand, num_opponents: int, stage: int, board: List[int], trials: int):
    evaluator = Evaluator()
    wins = 0
    for _ in range(trials):
        deck = Deck()
        deck.cards = [card for card in deck.cards if card not in player_hand.cards + board]
        
        current_board = fill_board(deck, board.copy(), stage)
        opponents = deal_opponents(num_opponents, deck)
        
        player_score = evaluator.evaluate(player_hand.cards, current_board)
        win = True
        for opponent in opponents:
            opponent_score = evaluator.evaluate(opponent.cards, current_board)
            if (opponent_score < 1000):
                break
            if opponent_score < player_score:
                win = False
                break
        if win:
            wins += 1  # Win Condition
    return wins

def simulate(player_hand: Hand, num_opponents: int, stage: int, board: List[int], trials=100, n=1000):
    num_processes = min(cpu_count(), n)
    chunk_size = n // num_processes
    
    args = [(player_hand, num_opponents, stage, board, trials) for _ in range(n)]
    
    with Pool(processes=num_processes) as pool:
        results = pool.starmap(single_trial, args, chunksize=chunk_size)
    
    return results

def sim_stats(player_hand: Hand, num_opponents: int, stage: int, board: List[int], risk: float, trials=100, n=1000):
    results = simulate(player_hand, num_opponents, stage, board, trials, n)
    data = np.array(results) / trials
    mean = np.mean(data)
    sd = np.std(data) * math.sqrt(trials)
    breakeve = breakeven(num_opponents + 1, 1, mean, sd)
    input = torch.tensor(np.array([mean, risk])).float()
    with torch.no_grad():
        optimal_raise = pokertorch(input)
    optim = float(optimal_raise.numpy()[0] * 100)
    optim = optim if optim > 0 else 0
    return mean, sd, breakeve, optim

def get_initial_guess(player_hand: Hand, num_opponents: int, stage: int, board: List[int], trials=100):
    num_processes = cpu_count()
    
    args = [(player_hand, num_opponents, stage, board, trials)]
    
    with Pool(processes=num_processes) as pool:
        results = pool.starmap(single_trial, args)
    
    data = np.array(results) / trials
    mean = np.mean(data)
    return mean


def breakeven(total_pot: int, player_in: int, mean: float, sd: float):
    win_chance = 1.0 * player_in / total_pot
    z_score = (win_chance - mean) / sd
    percent =  1 - norm.cdf(z_score)
    return percent

def main():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_directory, "pokertorch.pt")
    pokertorch = torch.jit.load(model_path)
    player_hand = Hand([Card.new("Ad"), Card.new("Kd")])
    board = []
    num_opponents = 5
    stage = 5
    trials = 100
    n = 2500

    wins = simulate(player_hand, num_opponents, stage, board, trials, n)
    data = np.array(wins) / trials
    mean = np.mean(data)
    sd = np.std(data) * math.sqrt(trials)

    print(mean, sd)

    per_player = 100

    total_pot = (num_opponents + 1) * per_player
    player_in = per_player

    perc = breakeven(total_pot, player_in, mean, sd) * 100

    risk = 0.5

    input = torch.tensor(np.array([mean, risk])).float()

    with torch.no_grad():
        optimal_raise = pokertorch(input)

    optim = float(optimal_raise.numpy()[0] * 100)
    optim = optim if optim > 0 else 0

    print('for a risk tolerance factor of ', risk, ' you should raise ', optim, ' percent of your holdings')

    print('You have a ', mean * 100, ' percent chance to win')

    print('You have a ', perc, ' percent chance to at least break even')

    plt.hist(wins, bins=np.arange(min(wins), max(wins) + 2) - 0.5, edgecolor='black')
    plt.xlabel('# of wins')
    plt.ylabel('Frequency')
    plt.title('Expected number of wins per 100 hands')
    plt.show()

if __name__ == "__main__":
    main()