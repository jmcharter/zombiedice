"""
Zombie Dice is by Steve Jackson Games
http://zombiedice.sjgames.com/


Zombie Dice simulator by Al Sweigart (al@inventwithpython.com)
(I'm not affiliated with SJ Games. This is a hobby project.)

Note: A "turn" is a single player's turn. A "round" is every player having one turn.
Note: Since all variables are public in Python, it is trivial to have a bot that hacks the tournament code. Inspect the bot code before running it.
Note: We don't use OOP for bots. A "zombie dice bot" simply implements a turn() method which calls a global roll() function as often as it likes. See documentation for details.
"""

import logging, random, sys, copy
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logging.debug('Start of the program.')

# constants, to keep a typo in a string from making weird errors
COLOR = 'color'
ICON = 'icon'
RED = 'red'
GREEN = 'green'
YELLOW = 'yellow'
SHOTGUN = 'shotgun'
BRAINS = 'brains'
FOOTSTEPS = 'footsteps'
SCORES = 'scores'

VERBOSE = False # if True, program outputs the actions that happen during the game


def runGame(zombies):
    """Runs a single game of zombie dice. zombies is a list of zombie dice bot objects."""
    global CURRENT_ZOMBIE # string of the zombie whose turn it is currently
    global CURRENT_CUP # list of dice strings (i.e. 'red', 'yellow', 'green')
    global CURRENT_HAND # list of dice being rolled (should always be three)
    global NUM_SHOTGUNS_ROLLED # number of shotguns rolled this turn
    global NUM_BRAINS_ROLLED # number of brains rolled this turn
    global ROLLED_BRAINS # list of dice strings for each brain rolled, used in the rare event we run out of brain dice

    # create a new game state object
    playerScores = dict([(zombie.name, 0) for zombie in zombies])
    playerOrder = [zombie.name for zombie in zombies]
    logging.debug('Player order: ' + ', '.join(playerOrder))
    gameState = {'order': playerOrder,
                 'scores': playerScores,
                 'round': 0}

    # validate zombie objects, return None to signify an aborted game
    if len(playerOrder) != len(set(playerOrder)): # set() will get rid of any duplicates
        logging.error('Zombies must have unique names.')
        return
    if len(playerOrder) < 2:
        logging.error('Need at least two zombies to play.')
        return
    for zombie in zombies:
        if 'turn' not in dir(zombie):
            logging.error('All zombies need a turn() method.')
        if 'name' not in dir(zombie):
            logging.error('All zombies need a name member.')

    # call every zombie's newGame() method, if it has one
    for zombie in zombies:
        if 'newGame' in dir(zombie):
            zombie.newGame()

    # set up for a new game
    lastRound = False # True when a player has reached 13 brains
    tieBreakingRound = False # True when the "last round" ended in a tie
    zombiesInPlay = copy.copy(zombies) # all zombies play
    while True: # game loop
        gameState['round'] += 1
        logging.debug('ROUND #%s, scores: %s' % (gameState['round'], gameState[SCORES]))
        if VERBOSE: print('Round #%s' % (gameState['round']))
        for zombie in zombiesInPlay:
            CURRENT_ZOMBIE = zombie.name
            logging.debug('NEW TURN: %s' % (CURRENT_ZOMBIE))
            if VERBOSE: print("%s's turn." % (CURRENT_ZOMBIE))

            # set up for a new turn
            CURRENT_CUP = [RED] * 3 + [YELLOW] * 4 + [GREEN] * 6
            random.shuffle(CURRENT_CUP)
            CURRENT_HAND = []
            NUM_SHOTGUNS_ROLLED = 0
            NUM_BRAINS_ROLLED = 0
            ROLLED_BRAINS = [] # list of dice colors, in case of "ran out of dice"

            # run the turn (don't pass the original gameState)
            zombie.turn(copy.deepcopy(gameState))
            if VERBOSE and NUM_SHOTGUNS_ROLLED < 3: print('%s stops.' % (CURRENT_ZOMBIE))
            if VERBOSE and NUM_SHOTGUNS_ROLLED >= 3: print('%s is shotgunned.' % (CURRENT_ZOMBIE))

            # add brains to the score
            if NUM_SHOTGUNS_ROLLED < 3:
                gameState[SCORES][zombie.name] += NUM_BRAINS_ROLLED

            if gameState[SCORES][zombie.name] >= 13:
                # once a player reaches 13 brains, it becomes the last round
                lastRound = True
                logging.debug('LAST ROUND')
                if VERBOSE: print('%s has reached 13 brains.' % (zombie.name))

        if tieBreakingRound:
            break # there is only one tie-breaking round, so after it end the game

        if lastRound:
            # only zombies tied with the highest score go on to the tie-breaking round (if there is one)
            zombiesInPlay = []
            highestScore = max(gameState[SCORES].values()) # used for tie breaking round
            # zombiesInPlay will now only have the zombies tied with the highest score:
            zombiesInPlay = [zombie for zombie in zombies if gameState[SCORES][zombie.name] == highestScore]

            if len(zombiesInPlay) == 1:
                # only one winner, so end the game
                break
            else:
                # multiple winners, so go on to the tie-breaking round.
                logging.debug('TIE BREAKING ROUND')
                if VERBOSE: print('Tie breaking round with %s' % (', '.join([zombie.name for zombie in zombiesInPlay])))
                tieBreakingRound = True

    # call every zombie's endGame() method, if it has one
    for zombie in zombies:
        if 'endGame' in dir(zombie):
            zombie.endGame(copy.deepcopy(gameState))

    # rank bots by score
    ranking = sorted(gameState[SCORES].items(), key=lambda x: x[1], reverse=True)
    highestScore = ranking[0][1]
    logging.debug('Ranking: %s' % (ranking))
    if VERBOSE: print('Final Scores: %s' % (', '.join(['%s %s' % (x[0], x[1]) for x in ranking])))     #(', '.join(['%s %s' % (name, score) for name, score in ranking.items()])))

    # winners are the bot(s) with the highest score
    winners = [x[0] for x in ranking if x[1] == highestScore]
    logging.debug('Winner(s): %s' % (winners))
    if VERBOSE: print('Winner%s: %s' % ((len(winners) != 1 and 's' or ''), ', '.join(winners)))

    return gameState


def runTournament(zombies, numGames):
    """A tournament is one or more games of Zombie Dice. The bots are re-used between games, so they can remember previous games.
    zombies is a list of zombie bot objects. numGames is an int of how many games to run."""
    tournamentState = {'wins': dict([(zombie.name, 0) for zombie in zombies]),
                       'ties': dict([(zombie.name, 0) for zombie in zombies])}

    for i in range(numGames):
        random.shuffle(zombies) # randomize the order
        endState = runGame(zombies) # use the same zombie objects so they can remember previous games.

        if endState is None:
            sys.exit('Error when running game.')

        ranking = sorted(endState[SCORES].items(), key=lambda x: x[1], reverse=True)
        highestScore = ranking[0][1]
        winners = [x[0] for x in ranking if x[1] == highestScore]
        if len(winners) == 1:
            tournamentState['wins'][ranking[0][0]] += 1
        elif len(winners) > 1:
            for score in endState[SCORES].items():
                if score[1] == highestScore:
                    tournamentState['ties'][score[0]] += 1

    # print out the tournament results in neatly-formatted columns.
    print('Tournament results:')
    maxNameLength = max([len(zombie.name) for zombie in zombies])

    winsRanking = sorted(tournamentState['wins'].items(), key=lambda x: x[1], reverse=True)
    print('Wins:')
    for winnerName, winnerScore in winsRanking:
        print('    %s %s' % (winnerName.rjust(maxNameLength), str(winnerScore).rjust(len(str(numGames)))))

    tiesRanking = sorted(tournamentState['ties'].items(), key=lambda x: x[1], reverse=True)
    print('Ties:')
    for tiedName, tiedScore in tiesRanking:
        print('    %s %s' % (tiedName.rjust(maxNameLength), str(tiedScore).rjust(len(str(numGames)))))


def roll():
    """This global function is called by a zombie bot object to indicate that they wish to roll the dice.
    The state of the game and previous rolls are held in global variables."""
    global CURRENT_ZOMBIE, CURRENT_CUP, CURRENT_HAND, NUM_SHOTGUNS_ROLLED, NUM_BRAINS_ROLLED, ROLLED_BRAINS

    # make sure zombie can actually roll
    if NUM_SHOTGUNS_ROLLED >= 3:
        return []

    logging.debug(CURRENT_ZOMBIE + ' rolls. (brains: %s, shotguns: %s)' % (NUM_BRAINS_ROLLED, NUM_SHOTGUNS_ROLLED))
    if VERBOSE: print('%s rolls. (brains: %s, shotguns: %s)' % (CURRENT_ZOMBIE, NUM_BRAINS_ROLLED, NUM_SHOTGUNS_ROLLED))

    # "ran out of dice", so put the rolled brains back into the cup
    if 3 - len(CURRENT_HAND) > len(CURRENT_CUP):
        logging.debug('Out of dice! Putting rolled brains back into cup.')
        CURRENT_CUP.extend(ROLLED_BRAINS)
        ROLLED_BRAINS = []


def rollDie(die):
    """Returns the result of a single die roll as a dictionary with keys 'color' and 'icon'.
    The die parameter is a string of the color of the die (i.e. 'green', 'yellow', 'red').
    The 'color' values in the return dict are one of 'green', 'yellow', 'red'.
    The 'icon' values are one of 'shotgun', 'footsteps', 'brains'."""
    roll = random.randint(1, 6)
    if die == RED:
        if roll in (1, 2, 3):
            return {COLOR: RED, ICON: SHOTGUN}
        elif roll in (4, 5):
            return {COLOR: RED, ICON: FOOTSTEPS}
        elif roll in (6,):
            return {COLOR: RED, ICON: BRAINS}
    elif die == YELLOW:
        if roll in (1, 2):
            return {COLOR: YELLOW, ICON: SHOTGUN}
        elif roll in (3, 4):
            return {COLOR: YELLOW, ICON: FOOTSTEPS}
        elif roll in (5, 6):
            return {COLOR: YELLOW, ICON: BRAINS}
    elif die == GREEN:
        if roll in (1,):
            return {COLOR: GREEN, ICON: SHOTGUN}
        elif roll in (2, 3):
            return {COLOR: GREEN, ICON: FOOTSTEPS}
        elif roll in (4, 5, 6):
            return {COLOR: GREEN, ICON: BRAINS}



class ZombieBot_RandomCoinFlip(object):
    """After the first roll, this bot always has a fifty-fifty chance of deciding to roll again or stopping."""
    def __init__(self, name):
        self.name = name

    def turn(self, gameState):
        results = roll() # first roll

        while results and random.randint(0, 1) == 0:
            results = roll()



def main():
    # fill up the zombies list with different bot objects, and then pass to runTournament()
    zombies = []
    zombies.append(ZombieBot_RandomCoinFlip('Alice'))
    zombies.append(ZombieBot_RandomCoinFlip('Bob'))
    runTournament(zombies, 1)


if __name__ == '__main__':
    main()