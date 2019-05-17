"""
This is the actual game
it is an squared board 
	* with a fixed amount of ships and cells
	* the rounds(shoots) are defined by the user
		* this implements easier or harder games
	* it is initialized with 0 as an empty cell
	* every ship 
		* is conformed with two contiguous cells
		* the cells have the same integer
		* every ship is represented by diferent integer
	* when a ship is hit is considered destroyed
		* a destroyed ship is represented by cells with -1 

"""

from random import randint

EMPTY_CELL = "_"  	# water
DESTR_SHIP = "*"  	# destroyed ship
MISS_SHOT = "X" 	# miss shot

class Board:
	

	"""docstring for Board"""
	def __init__(self,board_id,auto=False):
		#
		self.board_id = board_id
		self.auto = auto
		self.size = 6
		self.gameboard = [[EMPTY_CELL for x in range(self.size)] for y in range(self.size)]
		self.shots = []
		self.ships = 5
		self.fillboard()
		self.hit = False 


	# fills the board with ships
	def fillboard(self):
		ship = self.ships 					# keep the value of the ships
		while ship:
			self.place_ship(ship)			# every ship will be in represented by its number
			ship -= 1


	# places one ship (two contiguous cells)
	def place_ship(self,ship):
		self.hit = False
		not_placed = True
		while not_placed:
			x = randint(0,self.size-1)
			y = randint(0,self.size-1)
			if(not self.empty_cell(x,y)):
				continue					# non empty cell

			direc = randint(0,2)			
			x_next,y_next,inside = self.next_cell(x,y,direc)
			if(not inside or not self.empty_cell(x_next,y_next)):
				continue					# not inside or non empty cell

			# empty slot found
			self.gameboard[y][x] = str(ship)
			self.gameboard[y_next][x_next] = str(ship)
			not_placed = False



	# return if it is an empty cell
	def empty_cell(self,x,y):
		return self.gameboard[y][x] == EMPTY_CELL


	# return if the cell was hit previously
	def hit_cell(self,x,y):
		return 	self.gameboard[y][x] == DESTR_SHIP or \
				self.gameboard[y][x] == MISS_SHOT


	# used to insert a new ship
	# returns the next cell based on the direc variable
	# direc: 0=horizontal; 1=vertical
	# inside: indicates the the cell is inside the board
	def next_cell(self,x,y,direc):
		if (direc == 0):
			x += 1
		else:
			y += 1
		inside = self.valid(x,y)
		return x,y,inside

	
	# validate the given coordinate
	def valid(self,x,y):
		return 	x >= 0 and			\
				x < self.size and	\
				y >= 0 and 			\
				y < self.size





	# shoot a cell located at x,y
	# if a ship is hit => destroys the whole ship
	# returns True if won the game
	def shoot(self,x,y):
		self.hit = False
		if (self.empty_cell(x,y)):		
			self.gameboard[y][x] = MISS_SHOT
			return False						# hit an empty cell, return false
		if (self.hit_cell(x,y)):
			return False 						# already shot this cell, return false

		ship = self.gameboard[y][x]
		self.gameboard[y][x] = DESTR_SHIP
		self.destroy_ship(x,y,ship)
		self.ships -= 1
		self.hit = True
		return self.won() 						# return if the player won the game


	# used when shooting to the board
	# destroys the other cell of the ship being hit
	def destroy_ship(self,x,y,ship):
		if 	 ( x > 0 and self.gameboard[y][x-1] == ship):
			coor = x-1,y
		elif ( x < self.size-1 and self.gameboard[y][x+1] == ship):
			coor = x+1,y
		elif ( y > 0  and self.gameboard[y-1][x] == ship):
			coor = x,y-1
		else :
			coor = x,y+1
		res_x,res_y = coor
		self.gameboard[res_y][res_x] = DESTR_SHIP
		self.shots.append(coor)

			

	# game won?
	def won(self):
		return self.ships == 0 


	# serialized board 
	# friendly : determines the information to be shown 
	# 	true -> team mates
	# 	false -> enemies
	def serialize(self,friendly=False):
		result = ""
		for row in self.gameboard:
			for cell in row:
				temp_cell = cell
				if (not friendly and self.ship_cell(cell)):
					temp_cell = EMPTY_CELL
				result += temp_cell
			result += "\n"
		return result + "\n"


	# a ship cell is formed by numbers
	def ship_cell(self,cell):
		try:
			int(cell)
			return True
		except:
			return False

	# to generate intelligent coordinates
	def generate_coordinates(self):
		while True:
			x = randint(0,self.size-1)
			y = randint(0,self.size-1)
			contained = (x,y) in self.shots
			if(not contained):
				self.shots.append((x,y))
				return x,y
		