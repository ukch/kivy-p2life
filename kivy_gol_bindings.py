from gol import life_animation

# TODO better name
def evolve(grid):
    anim = life_animation(grid.cells)
    grid.cells = anim.next()
