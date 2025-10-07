## About Snake

Snake is a fully offline snake game that uses a toroidal grid. This application is developed using PyQt. In each version's source folder is a copy of the source code of the version of PyQt which was used to create that specific version of Snake. This game is available in both portable and installable versions; neither version auto-updates. The AI can make mistakes. For your information, the attached MSI installers are made with Advanced Installer. The `.aip` files used to build the installers are not publicly available for privacy reasons. However, you are free to use, modify, and redistribute the installers under the license terms of this software.

### AI Performance (Personal Experience) when Starting Lives is set to 1:

- **Snake 1.0.0:** The AI usually reaches a score of at least 25.

- **Snake 1.1.0:** The AI usually reaches a score of at least 40.

## Notes:

1. Resizing the application window changes the dimensions of the playing grid.
2. Shrinking the application window while a game is active can potentially require the player to start a new game. This is allowed by the game so that the player can resize the application window back to a manegable size if they find the dimensions of the application window too large, but at the cost of possibly having to restart their game.
