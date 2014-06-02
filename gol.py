#!/usr/bin/env python

# The below taken from
# http://jakevdp.github.io/blog/2013/08/07/conways-game-of-life/

import numpy as np


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

life_step = life_step_1


def life_animation(X):
    """Produce a Game of Life Animation

    Parameters
    ----------
    X : array_like
        a two-dimensional numpy array showing the game board
    """
    X = np.asarray(X)
    assert X.ndim == 2
    X = X.astype(bool)

    def _iterate(X):
        while True:
            X = life_step(X)
            yield X

    return _iterate(X)
