import bppy as bp

# BEvents functions for x and o moves
x = lambda row, col: bp.BEvent('X' + str(row) + str(col))
o = lambda row, col: bp.BEvent('O' + str(row) + str(col))

# locations of all possible lines
LINES = [[(i, j) for j in range(3)] for i in range(3)] + [[(i, j) for i in range(3)] for j in range(3)] + [
    [(i, i) for i in range(3)]] + [[(i, 3 - i - 1) for i in range(3)]]
x_lines = [[x(i, j) for (i, j) in line] for line in LINES]
o_lines = [[o(i, j) for (i, j) in line] for line in LINES]

# define events sets of x an o moves
any_x = [x(i, j) for i in range(3) for j in range(3)]
any_o = [o(i, j) for i in range(3) for j in range(3)]
move_events = bp.EventSet(lambda e: e.name.startswith('X') or e.name.startswith('O'))

# define static terminal events
static_event = {
    'OWin': bp.BEvent('OWin'),
    'XWin': bp.BEvent('XWin'),
    'draw': bp.BEvent('Draw')
}


@bp.thread
def square_taken(row, col):  # blocks moves to a square that is already taken
    yield bp.sync(waitFor=[x(row, col), o(row, col)])
    yield bp.sync(block=[x(row, col), o(row, col)])


@bp.thread
def enforce_turns():  # blocks moves that are not in turn
    while True:
        yield bp.sync(waitFor=any_x, block=any_o)
        yield bp.sync(waitFor=any_o, block=any_x)


@bp.thread
def end_of_game():  # blocks moves after the game is over
    yield bp.sync(waitFor=list(static_event.values()))
    yield bp.sync(block=bp.All())


@bp.thread
def detect_draw():  # detects a draw
    for r in range(3):
        for c in range(3):
            yield bp.sync(waitFor=move_events)
    yield bp.sync(request=static_event['draw'], priority=90)


@bp.thread
def detect_x_win(line):  # detects a win by player X
    for i in range(3):
        yield bp.sync(waitFor=line)
    yield bp.sync(request=static_event['XWin'], priority=100)


@bp.thread
def detect_o_win(line):  # detects a win by player O
    for i in range(3):
        yield bp.sync(waitFor=line)
    yield bp.sync(request=static_event['OWin'], priority=100)


@bp.thread
def center_preference():
    while True:
        yield bp.sync(request=o(1, 1), priority=35)


@bp.thread
def corner_preference():
    while True:
        yield bp.sync(request=[o(0, 0), o(0, 2), o(2, 0), o(2, 2)], priority=20)


@bp.thread
def side_preference():
    while True:
        yield bp.sync(request=[o(0, 1), o(1, 0), o(1, 2), o(2, 1)], priority=10)


@bp.thread
def add_third_o(line):
    for i in range(2):
        yield bp.sync(waitFor=line)
    yield bp.sync(request=line, priority=50)


@bp.thread
def prevent_third_x(xline, oline):
    for i in range(2):
        yield bp.sync(waitFor=xline)
    yield bp.sync(request=oline, priority=40)


@bp.thread
def block_fork(xfork, ofork):  # blocks a fork strategy
    for i in range(2):
        yield bp.sync(waitFor=xfork)
    yield bp.sync(request=ofork, priority=30)


forks22 = [[x(1, 2), x(2, 0)], [x(2, 1), x(0, 2)], [x(1, 2), x(2, 1)]], [o(2, 2), o(0, 2), o(2, 0)]
forks02 = [[x(1, 2), x(0, 0)], [x(0, 1), x(2, 2)], [x(1, 2), x(0, 1)]], [o(0, 2), o(0, 0), o(2, 2)]
forks20 = [[x(1, 0), x(2, 2)], [x(2, 1), x(0, 0)], [x(2, 1), x(1, 0)]], [o(2, 0), o(0, 0), o(2, 2)]
forks00 = [[x(0, 1), x(2, 0)], [x(1, 0), x(0, 2)], [x(0, 1), x(1, 0)]], [o(0, 0), o(0, 2), o(2, 0)]
forks_diag = [[x(0, 2), x(2, 0)], [x(0, 0), x(2, 2)]], [o(0, 1), o(1, 0), o(1, 2), o(2, 1)]

@bp.thread
def player_x():  # simulate player X
    while True:
        yield bp.sync(request=any_x)


if __name__ == "__main__":
    bprog = bp.BProgram(
        bthreads=[square_taken(i, j) for i in range(3) for j in range(3)] +
                 [enforce_turns(), end_of_game(), detect_draw()] +
                 [detect_x_win(line) for line in x_lines] +
                 [detect_o_win(line) for line in o_lines] +
                 [center_preference(), corner_preference(), side_preference()] +
                 [add_third_o(line) for line in o_lines] +
                 [prevent_third_x(xline, oline) for (xline, oline) in zip(x_lines, o_lines)] +
                 [block_fork(xfork, forks22[1]) for xfork in forks22[0]] +
                 [block_fork(xfork, forks02[1]) for xfork in forks02[0]] +
                 [block_fork(xfork, forks20[1]) for xfork in forks20[0]] +
                 [block_fork(xfork, forks00[1]) for xfork in forks00[0]] +
                 [block_fork(xfork, forks_diag[1]) for xfork in forks_diag[0]] +
                 [player_x()],
        event_selection_strategy=bp.PriorityBasedEventSelectionStrategy(default_priority=0),
        listener=bp.PrintBProgramRunnerListener()
    )
    bprog.run()
