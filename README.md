# python-online-multiplayer-battleship
Copyright © 2018 Gautam Balamurali

Battleship is a guessing game for multiple players. It is played on ruled grids
(paper or board) on which each player's fleet of ships (including battleships) are
marked. The locations of the fleets are concealed from the other player. Players
alternate turns calling "shots" at the other player's ships, and the objective of the
game is to destroy the opposing player's fleet.
The game is played on twice the number of players grids, two for each player.
The grids are typically square – usually 10×10 – and the individual squares in
the grid are identified by letter and number. On one grid the player arranges
ships and records the shots by the opponent. On the other grid the player
records their own shots. It is a multiplayer client-server game over socket
connections using Python programming language.

This was my Computer Network Lab project. Run server.py first then client.py. Python3 is implemented. While giving the coordinates first digit represents the number of enemy grid number, second digit represents the position of ship and third digit represents row number. There is no UI. The game works on terminal.
