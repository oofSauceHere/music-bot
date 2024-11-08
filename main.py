# i perhaps may hate python classes

import os
import io
import asyncio
import discord
from discord.ext import commands
from pytubefix import YouTube
from pytubefix.exceptions import VideoUnavailable
from dotenv import load_dotenv
load_dotenv()

class MusicBot(commands.Bot):
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.remove_command("help")
        self.vc = None

    async def on_ready(self):
        print(f"Logged in as {self.user}.")
        await self.change_presence(activity=discord.Game(name="Bloons TD 6"))
    
    # error handling
    async def on_command_error(self, ctx, error):
        if(type(error).__name__ == "CommandNotFound"):
            await ctx.send("Invalid command. Explode!")
            return
        elif(type(error).__name__ == "CommandInvokeError"):
            error_type = type(error.original).__name__
            if(error_type == "RegexMatchError" or error_type == "VideoUnavailable"):
                await ctx.send("Invalid video. Explode!")

    # defining all discord commands (must be done inside function for use of "self.command")
    def init_commands(self):
        # i am aware of the stupidity of such an act but, because this bot is for my friends, it WILL be funny
        @self.command(name="help")
        async def help(ctx):
            await ctx.send("No")

        # joins user's call and plays song from given youtube link
        @self.command(name="play")
        async def play(ctx, link=None):
            if(link == None):
                await ctx.send("No video specified.")
                return
            
            if(self.vc != None):
                await ctx.send("Currently playing in other voice channel.")
                return

            # uses pytube to gather audio stream from yt link, handles error if invalid link
            try:
                yt = YouTube(link, use_po_token=True)
            except VideoUnavailable:
                return
            
            audio = yt.streams.filter(only_audio=True).first()
            audio_buffer = io.BytesIO()
            audio.stream_to_buffer(audio_buffer)
            audio_buffer.seek(0)
            # audio.download(filename="temp", mp3=True)
            # await ctx.send(link)

            # doesn't play if user is not in a voice channel
            voice = ctx.author.voice
            if(voice == None):
                await ctx.send("You need to be in a voice channel.")
                return
            
            # connects to voice channel and idles while audio plays
            self.vc = await voice.channel.connect()
            await ctx.send(f"Currently playing: **{yt.title}**")
            self.vc.play(discord.FFmpegPCMAudio(source=audio_buffer, pipe=True)) # should we define "after" parameter?
            while self.vc.is_playing():
                await asyncio.sleep(0.1)
            await self.vc.disconnect()
            self.vc = None
        
        # stops playback and leaves call
        @self.command(name="stop")
        async def stop(ctx):
            # should i check if even in voice channel?
            if(self.vc == None):
                await ctx.send("Not currently in a call.")
                return

            await ctx.send("Leaving call.")
            await self.vc.disconnect()

    def start_bot(self, token):
        self.init_commands()
        self.run(token)

def main():
    token = os.getenv('DISCORD_TOKEN')
    intents = discord.Intents(messages=True, message_content=True, guilds=True, voice_states=True)
    bot = MusicBot(command_prefix="$", intents=intents)

    bot.start_bot(token)

if __name__ == "__main__":
    main()

# TO-DOs
#   > playlist/queue (differentiate between servers?)
#       > maybe server-wide playlists?
#   > is it worth mapping links to byte buffers or will that be too space inefficient?
#   > maybe add function to convert spotify song title to youtube link?
#       > much more involved and possibly flawed...
#   > volume control?