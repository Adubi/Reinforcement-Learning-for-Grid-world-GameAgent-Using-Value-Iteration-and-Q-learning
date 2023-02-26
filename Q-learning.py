from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import pprint
BOARD_ROWS = 3
BOARD_COLS = 4
WIN_STATE = (0, 3)
LOSE_STATE = (1, 3)
START = (2, 0)
DETERMINISTIC = False


class State:
    def __init__(self, state=START):
        self.board = np.zeros([BOARD_ROWS, BOARD_COLS])
        self.board[1, 1] = -1
        self.state = state
        self.isEnd = False
        self.determine = DETERMINISTIC

    def giveReward(self):
        if self.state == WIN_STATE:
            return 1
        elif self.state == LOSE_STATE:
            return -1
        else:
            return 0

    def isEndFunc(self):
        if (self.state == WIN_STATE) or (self.state == LOSE_STATE):
            self.isEnd = True

    def _chooseActionProb(self, action):
        if action == "up":
            return np.random.choice(["up", "left", "right"], p=[0.8, 0.1, 0.1])
        if action == "down":
            return np.random.choice(["down", "left", "right"], p=[0.8, 0.1, 0.1])
        if action == "left":
            return np.random.choice(["left", "up", "down"], p=[0.8, 0.1, 0.1])
        if action == "right":
            return np.random.choice(["right", "up", "down"], p=[0.8, 0.1, 0.1])

    def nxtPosition(self, action):
        """
        action: up, down, left, right
        -------------
        0 | 1 | 2| 3|\n
        1 |\n
        2 |\n
        return next position on board
        """
        if self.determine:
            if action == "up":
                nxtState = (self.state[0] - 1, self.state[1])
            elif action == "down":
                nxtState = (self.state[0] + 1, self.state[1])
            elif action == "left":
                nxtState = (self.state[0], self.state[1] - 1)
            else:
                nxtState = (self.state[0], self.state[1] + 1)
            self.determine = False
        else:
            # non-deterministic
            action = self._chooseActionProb(action)
            self.determine = True
            nxtState = self.nxtPosition(action)

        # if next state is legal
        if (nxtState[0] >= 0) and (nxtState[0] <= 2):
            if (nxtState[1] >= 0) and (nxtState[1] <= 3):
                if nxtState != (1, 1):
                    return nxtState
        return self.state

    def showBoard(self):
        self.board[self.state] = 1
        for i in range(0, BOARD_ROWS):
            print('-----------------')
            out = '| '
            for j in range(0, BOARD_COLS):
                if self.board[i, j] == 1:
                    token = '*'
                if self.board[i, j] == -1:
                    token = 'z'
                if self.board[i, j] == 0:
                    token = '0'
                out += token + ' | '
            print(out)
        print('-----------------')


class Agent:

    def __init__(self):
        self.states = []  # record position and action taken at the position
        self.actions = ["up", "down", "left", "right"]
        self.State = State()
        self.isEnd = self.State.isEnd
        self.lr = 0.2
        self.exp_rate = 0.3
        self.decay_gamma = 0.9
        self.tot_states = {}
        self.rewards = []

        # initial Q values
        self.Q_values = {}
        for i in range(BOARD_ROWS):
            for j in range(BOARD_COLS):
                self.Q_values[(i, j)] = {}
                for a in self.actions:
                    self.Q_values[(i, j)][a] = 0  # Q value is a dict of dict
    def chooseAction(self):
        # choose action with most expected value
        mx_nxt_reward = 0
        action = "right"

        if np.random.uniform(0, 1) <= self.exp_rate:
            action = np.random.choice(self.actions)
        else:
            # greedy action
            for a in self.actions:
                current_position = self.State.state
                nxt_reward = self.Q_values[current_position][a]
                if nxt_reward >= mx_nxt_reward:
                    action = a
                    mx_nxt_reward = nxt_reward
            # print("current pos: {}, greedy aciton: {}".format(self.State.state, action))
        return action

    def takeAction(self, action):
        position = self.State.nxtPosition(action)
        # update State
        return State(state=position)

    def reset(self):
        self.states = []
        self.State = State()
        self.isEnd = self.State.isEnd

    def play(self, rounds=10):
        i = 0
        while i < rounds:
            # to the end of game back propagate reward
            if self.State.isEnd:
                # back propagate
                reward = self.State.giveReward()
                self.rewards.append(reward)
                for a in self.actions:
                    self.Q_values[self.State.state][a] = reward
                print("Game End Reward", reward)
                for s in reversed(self.states):
                    current_q_value = self.Q_values[s[0]][s[1]]
                    reward = current_q_value + self.lr * (self.decay_gamma * reward - current_q_value)
                    self.Q_values[s[0]][s[1]] = round(reward, 3)
                self.tot_states[f"round {i+1}"] = [v[-1] for v in self.states]
                plt.scatter(i, abs(reward))
                plt.xlabel("Rounds", fontsize=22)
                plt.ylabel("Reward", fontsize=22)
                plt.savefig("rewards.png")
                self.reset()
                i += 1
            else:
                action = self.chooseAction()
                # append trace
                self.states.append([(self.State.state), action])
                print("current position {} action {}".format(self.State.state, action))
                # by taking the action, it reaches the next state
                self.State = self.takeAction(action)
                # mark is end
                self.State.isEndFunc()
                print("nxt state", self.State.state)
                print("---------------------")
                self.isEnd = self.State.isEnd
        self.save_rewards_per_round()

    
    def plot_states(self):
        """
        Plots for each round, a bar chart showing how many times each state was activated
        """
        names = []
        temp = []
        rows = 0
        cols = 0
        l = len(self.tot_states)

        for k,v in self.tot_states.items():
            names.append(k)
            temp.append(Counter(v))

        
        if 1 <= l <= 10:
            rows = 2
            cols = l // rows
            first, f_v = names[:l//rows], temp[:l//rows]
            second, s_v = names[l//rows:], temp[l//rows:]
            fig, ax = plt.subplots(rows, cols)
            for i,k in enumerate(first):
                f = f_v[i]
                ax[0, i].bar(x= list(f.keys()), height = list(f.values()))
                ax[0, i].set_title(k)
                ax[0, i].set_xlabel("Moves")
                ax[0, i].set_ylabel("Occurence")

            for i,k in enumerate(second):
                s = s_v[i]
                ax[1, i].bar(x = list(s.keys()), height = list(s.values()))
                ax[1, i].set_title(k)
                ax[1, i].set_xlabel("Moves")
                ax[1, i].set_ylabel("Occurence")
            fig.tight_layout()
            fig.savefig("plot_per_round.png")

        elif 11 <= l <= 20:
            rows = 4
            cols = l // rows
            f_row = 5
            s_row = cols + 5
            t_row = s_row + 5
            first, f_v = names[:l//f_row], temp[:l//f_row]
            second, s_v = names[f_row:s_row], temp[f_row:s_row]
            third, t_v = names[s_row:t_row], temp[s_row:t_row]
            fourth, fv = names[t_row:], temp[t_row:]
            fig, ax = plt.subplots(rows, cols, sharex="all")
            for i,k in enumerate(first):
                ax[0, i].bar(x=list(f_v[i].keys()), height = list(f_v[i].values()))
                ax[0, i].set_title(k)
                ax[0, i].set_xlabel("Moves")
                ax[0, i].set_ylabel("Occurence")

            for i,k in enumerate(second):
                ax[1, i].bar(x=list(s_v[i].keys()), height = list(s_v[i].values()))
                ax[1, i].set_title(k)
                ax[1, i].set_xlabel("Moves")
                ax[1, i].set_ylabel("Occurence")

            for i,k in enumerate(third):
                ax[2, i].bar(x=list(t_v[i].keys()), height = list(t_v[i].values()))
                ax[2, i].set_title(k)
                ax[2, i].set_xlabel("Moves")
                ax[2, i].set_ylabel("Occurence")

            for i,k in enumerate(fourth):
                ax[3, i].bar(x=list(fv[i].keys()), height = list(fv[i].values()))
                ax[3, i].set_title(k)
                ax[3, i].set_xlabel("Moves")
                ax[3, i].set_ylabel("Occurence")
            fig.tight_layout()
            fig.savefig("plot_per_round.png")
    
    def plot_rewards(self):
        """
        convert rewards to won and lost and then plots it
        """
        n = []
        for i in self.rewards:
            if  i == 1:
                n.append("Won")
            else:
                n.append("Lost")
        c = Counter(n)
        fig, ax = plt.subplots(1, 1)
        ax.pie(list(c.values()), labels=list(c.keys()))
        fig.savefig("round_rewards_q.png")
    
    def save_rewards_per_round(self):
        """
        save reward of each game in a file
        """
        n = []
        for i in self.rewards:
            if  i == 1:
                n.append("Won")
            else:
                n.append("Lost")
        
        res = ",".join(n)
        with open("rewards_q.txt", "a") as f:
            f.write(res + "\n")


if __name__ == "__main__":
    ag = Agent()
    print("initial Q-values ... \n")
    pprint.pprint(ag.Q_values)

    ag.play(rounds=20)
    print("latest Q-values ... \n")
    pprint.pprint(ag.Q_values)
    print()
    ag.plot_states()
    ag.plot_rewards()
    plt.show()





