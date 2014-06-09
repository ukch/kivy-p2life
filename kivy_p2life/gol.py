#!/usr/bin/env python

# The below taken from
# http://jakevdp.github.io/blog/2013/08/07/conways-game-of-life/

import numpy as np

from .constants import Colours


def life_step_1(X):
    """Game of life step using generator expressions"""
    nbrs_count = sum(np.roll(np.roll(X, i, 0), j, 1)
                     for i in (-1, 0, 1) for j in (-1, 0, 1)
                     if (i != 0 or j != 0))
    return (nbrs_count == 3) | (X & (nbrs_count == 2))


def life_step_2(X):
    """Game of life step using scipy tools"""
    from scipy.signal import convolve2d
    nbrs_count = \
        convolve2d(X, np.ones((3, 3)), mode='same', boundary='wrap') - X
    return (nbrs_count == 3) | (X & (nbrs_count == 2))


def p2life_step(X):
    """P2Life implementation using scipy tools.
    For more on P2Life see
    http://www.dcs.bbk.ac.uk/~gr/software/p2life/p2life.php
    """
    from scipy.signal import convolve2d
    ones = np.ones((3, 3))
    empties = X == Colours.EMPTY
    whites = X == Colours.WHITE
    blacks = X == Colours.BLACK
    white_nbrs = convolve2d(whites, ones, mode='same', boundary='wrap') - whites
    black_nbrs = convolve2d(blacks, ones, mode='same', boundary='wrap') - blacks

    # Birth: The cell has exactly three same colour neighbours and the number
    # of different colour neighbours is different from three.
    white_birth = empties & (white_nbrs == 3)
    black_birth = empties & (black_nbrs == 3)
    birth = (white_birth * Colours.WHITE) + (black_birth * Colours.BLACK)

    # B/W birth: The cell has exactly three white and three black neighbours.
    unknown_birth = (birth == Colours.UNKNOWN) * np.random.randint(Colours.WHITE, Colours.BLACK + 1, X.shape)
    birth = (birth * (birth != Colours.UNKNOWN)) | unknown_birth

    # Survival: If the difference between the number of white and black
    # neighbours is two or three.
    nbr_diff = np.abs(white_nbrs - black_nbrs)
    survival = (nbr_diff == 2) | (nbr_diff == 3)

    # Survival: If the difference between the number of white and black
    # neighbours is one and the number of same colour neighbours is at least
    # two.
    white_survival = (nbr_diff == 1) & (white_nbrs >= 2)
    black_survival = (nbr_diff == 1) & (black_nbrs >= 2)
    survival = (survival | white_survival | black_survival) * X

    return birth | survival

life_step = p2life_step


def life_animation(X):
    """Produce a Game of Life Animation

    Parameters
    ----------
    X : array_like
        a two-dimensional numpy array showing the game board
    """
    X = np.asarray(X)
    assert X.ndim == 2
    X = X.astype(int)

    def _iterate(X):
        while True:
            X = life_step(X)
            yield X

    return _iterate(X)
