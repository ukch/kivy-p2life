""" Doctests for kivy-p2life

>>> p2life_step(np.array([[1, 2, 1], [1, 2, 1], [1, 2, 1]]))
array([[1, 0, 1],
       [1, 0, 1],
       [1, 0, 1]])
"""

import numpy as np

from kivy_p2life.gol import p2life_step

if __name__ == "__main__":
    import doctest
    import logging

    logging.getLogger().setLevel(logging.INFO)

    result = doctest.testmod()
    if not result.failed:
        logging.info("All doctests passed")
