import pyautogui
import skimage as ski
import numpy as np
import click
import glob
import sys
from board import Board
from time import sleep

tile_width = 66
tile_height = 57

last_mouse = None
def mousemove(x, y):
    global last_mouse
    if last_mouse is not None:
        assert pyautogui.mouseinfo.position() == last_mouse, "Mouse moved while executing clicks"
    pyautogui.moveTo(x, y)
    last_mouse = (x, y)
 


tile_offset_x, tile_offset_y = 276, 85
shot_offset_x, shot_offset_y = -38, -733
shot_width, shot_height = 850, 750

def normalize_offset(pxl):
    pxl = pxl.astype(np.float64)
    for i in range(3):
        pxl[:,:,i] -= np.average(pxl[:,:,i])
    return pxl

new_game = ski.io.imread("new-game.png")



def screenshot(region=None):
    if region is None:
        size = pyautogui.size()
        region = (0, 0, size.width, size.height)

    s = pyautogui.screenshot(region=region)
    pxl_data = np.array(s.getdata(), dtype="uint8")
    pxl_data.resize((region[3], region[2], 3))
    ski.io.imsave("game.png", pxl_data)
    return pxl_data


def tiles():
    high = -5
    for i in range(11):
        for j in range(max(0, high), min(11, high + 11)):
            yield i, j
        high += 1


def get_block(pxl, i, j):
    x = tile_offset_x + tile_width * j - tile_width//2 * i
    y = tile_offset_y + tile_height * i
    
    block = pxl[y:y+32, x:x+32, :]

    return block

block_read_index = 0
def simplify_block(block):
    global block_read_index
    block_read_index += 1
    # ski.io.imsave(f"blocks/b_{block_read_index}_orig.png", block)
    gray = ski.color.rgb2gray(block)
    d = ski.feature.canny(gray, sigma=0.2, mode="reflect")
    # ski.io.imsave(f"blocks/b_{block_read_index}_feat.png", d)
    return d

def block_distance(a, b):
    return np.sum(a ^ b)

def is_empty(pxl):
    a = np.copy(pxl[16,:,:])
    l = np.max(a, axis=0) - np.min(a, axis=0)
    s = np.sum(l)
    return s < 30

class SigmarsGarden:
    def __init__(self):
        self.offset = (0, 0)
        self.tile_mapping = []

    def register(self, offset=None):
        if offset is None:
            shot = screenshot()
            match = ski.feature.match_template(
                shot, new_game
            )
            y, x, _ = np.unravel_index(np.argmax(match), match.shape)
            offset = (x, y)
        self.offset = offset

    def learn_mapping(self):
        for path in glob.glob("learn_mapping/game*.txt"):
            try:
                with open(path) as f:
                    correct = [l.strip().upper().split() for l in f]
                shot = ski.io.imread(path[:-3]+"png")
                for i, j in tiles():
                    if correct[i][j] != "__":
                        pxl = simplify_block(get_block(shot, i, j))
                        self.tile_mapping.append((correct[i][j], pxl))

            except Exception as e:
                print(f"Error while reading {path}: {e}", file=sys.stderr)

    def find_tile(self, needle_pxl):
        def distance_key(map_entry):
            return block_distance(needle_pxl, map_entry[1])

        return min(self.tile_mapping, key=distance_key)[0]

    def current_board(self):
        ox, oy = self.offset

        mousemove(ox, oy)
        sleep(0.5)

        shot = screenshot(region=(
            ox + shot_offset_x, oy + shot_offset_y,
            shot_width, shot_height
        ))
        board = Board()
        for i, j in tiles():
            blk = get_block(shot, i, j)
            if is_empty(blk):
                continue
            tile = self.find_tile(simplify_block(blk))
            if tile != "__":
                board.add_tile((i, j), tile)
        return board

    def execute_clicks(self, clicks):
        ox, oy = self.offset
        ox += shot_offset_x
        oy += shot_offset_y
        x, y = ox + 100, oy + 100
        mousemove(x, y)
        sleep(1)
        for i, j in clicks:
            x = ox + tile_offset_x + tile_width * j - tile_width//2 * i
            y = oy + tile_offset_y + tile_height * i
            mousemove(x=x, y=y)
            pyautogui.mouseDown()
            pyautogui.mouseUp()
    
    def new_game(self):
        ox, oy = self.offset
        mousemove(x=ox+100, y=oy+40)
        pyautogui.mouseDown()
        pyautogui.mouseUp()



@click.command()
@click.option('--offset', default=None)
def main(offset):
    garden = SigmarsGarden()
    if offset is None:
        print("Calculating offset...")
        garden.register()
        x, y = garden.offset
        print(f"To skip offset calculation next time, use: --offset {x},{y}")
    else:
        try:
            o = tuple(map(int, offset.split(",")))
            assert len(o) == 2
        except:
            assert False, "The offset parameter should look like '--offset <x>,<y>'. For example '--offset 123,987'."
        garden.register(o)

    garden.learn_mapping()

    while 1:
        board = garden.current_board()
        print(board.counts())
        print(sum(board.counts().values()))
        if board.is_full() or board.is_full(True):
            if board.is_full():
                print("Solving Sigmar's Garden")
            else:
                print("Solving Sigmar's Garden 2")

            try:
                solution = next(board.solve())
                print(solution)

                garden.execute_clicks([c for r in solution for c in r])
            except StopIteration:
                print("No solution found. Skipping to the next puzzle.")
        else:
            print("Probably the board has not been parsed correctly. Skipping to the next puzzle.")
        garden.new_game()
        sleep(6)


if __name__ == '__main__':
    main()
