import discord
import os
from discord.ext import commands
from pytubefix import YouTube
from dotenv import load_dotenv
load_dotenv()

class MusicBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)

    async def on_ready(self):
        print("Connected")

    def init_commands(self):
        @self.command()
        async def play(ctx, link):
            # author = context.message.author
            # print(author)

            # currently crashes if link is invalid
            audio = YouTube(link).streams.filter(only_audio=True).first()
            audio.download(filename="temp", mp3=True)
            # stream_to_buffer ?
            await ctx.send(link)

            voice = ctx.author.voice
            print(ctx.author.voice)
            if(voice == None):
                return
            
            await voice.channel.connect()
    
    def start_bot(self, token):
        self.init_commands()
        self.run(token)

# @client.event
# async def on_message(message):
#     # so we dont go on infinitely
#     if message.author == client.user:
#         return
    
#     if message.content == "hi":
#         await message.channel.send("hi")

def main():
    token = os.getenv('DISCORD_TOKEN')
    intents = discord.Intents(messages=True, message_content=True, guilds=True, voice_states=True)
    bot = MusicBot(command_prefix="$", intents=intents)

    bot.start_bot(token)

if __name__ == "__main__":
    main()

# TO-DOs
#   when to leave?
#   handling incorrect youtube links
#   