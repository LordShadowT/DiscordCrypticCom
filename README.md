# DiscordCrypticCom
A Communicator, that creates a local website and exchanges encrypted messages with other clients via Discord (now supports multiple clients)

Actually, you shouldn't use this., it's more or less a proof of concept.

If you still want to use it, check the dependencies and run the run.py file.

## Dependencies:

You need to have redis installed
```
pip install -r requirements.txt
```
Create a Discord Bot and add it to your server. Then create a channel and get the channel id.

Add a file called '.env' to the root directory with the following content:
```env
#  .env
DISCORD_TOKEN = <your discord bot token>
IP = <your local ip> (optional)
PORT = <your preferred port> (optional)
CHANNEL_ID = <the id of the discord channel you want to use> (needs to be the same for every client)
```