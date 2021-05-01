# bot-irongolem
A mini programmable workflow system based on the app Topos, which can help users get daily routines effectively done without missing any points.

## Possible Usage
- Help get routines done
- Build simple expert systems
- Create plot games based on the player's choices

## Get started
The bot has already been deployed on the server of Topos. Therefore, just send the command "ls" to the bot on the app Topos to see what he can do for you. If you have not downloaded the app Topos yet, visit the website [Topos World](http://topos.world/) for installation.
If the bot captures your interest and you feel like creating your own workflow programs, access [IronGolem Workflow Online Manager](http://122.51.74.154:2333/). Since all workflow programs are written in Python, you should have some basic grammatical knowledge of this language. Several API functions are provided for the sake of communication. The following reveals the usage of them:

**Basic Functions**

*start(message: str, time_limit: tuple = None)*
Create the process manifest of the workflow program. The program cannot call any APIs unless this function is called.  
The parameter time_limit should be in this format: (h,m,s). Since the program starts, it must be finished within *3600h+60m+s* seconds.
*do(task_description: str, important_points: list) -> bool*
Require the user to do something according to task description as well as pay attention to some important points of this task.
The user can claim success by sending the message "done" or failure by sending "reject".
If the user choose to reject, the user has to explain what prevented himself/herself from finishing this task.
When the process of the workflow program ends, the bot will render a summary of all rejections in order to help the user improve his/her program.
*say(message: str)*
Send a message to the user. 
