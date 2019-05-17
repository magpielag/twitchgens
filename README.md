# twitchgens
A chat-controlled music generation bot that monitors Twitch.TV channels.

Uses Ryan Kirkbride's "FoxDot" library and SuperCollider.

To install and run, simply follow the FoxDot install instructions available in the relevant github repo on via the FoxDot website, then load start_2.scd into SuperCollider. Run each synthDef individuall before running the "FoxDot.start()" line. 
Once this is done, run the bot.py script using python3. 

The module is set by default to monitor twitch.tv/twitchgens, but this can be altered using the config file. 
