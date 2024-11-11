# i perhaps may hate python classes

import os
import io
import asyncio
import discord
from collections import deque
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
        self.queue = deque()
        self.loop_song = False

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
            # doesn't play if user is not in a voice channel
            voice = ctx.author.voice
            if(voice == None):
                await ctx.send("You need to be in a voice channel.")
                return
            
            if(link != None):
                if(queue):
                    self.enqueue(ctx, link) # possibly idiotic
                    return
                else:
                    try:
                        yt = YouTube(link, use_oauth=True)
                    except VideoUnavailable:
                        return
                    
                    self.queue.append(yt)

            if(self.vc != None):
                if(self.vc.is_paused()):
                    await ctx.send("Resuming playback.")
                    self.vc.resume()
                    return
                else:
                    await ctx.send("Already playing video.")
                    return
            elif(not queue):
                await ctx.send("Queue is empty/nothing currently playing.")
                return

            # if(self.vc != None):
            #     await ctx.send("Currently playing in other voice channel.")
            #     return

            yt = queue[0]
            self.dequeue()
            
            audio = yt.streams.filter(only_audio=True).first()
            audio_buffer = io.BytesIO()
            audio.stream_to_buffer(audio_buffer)
            audio_buffer.seek(0)
            # audio.download(filename="temp", mp3=True)
            # await ctx.send(link)
            
            if(self.queue.empty()):
                self.queue.append()
            
            # connects to voice channel and idles while audio plays
            self.vc = await voice.channel.connect()
            await ctx.send(f"Currently playing: **{yt.title}**")
            while(loop or len(self.queue) != 0):
                self.vc.play(discord.FFmpegPCMAudio(source=audio_buffer, pipe=True)) # should we define "after" parameter?
                while(self.vc.is_playing() or self.vc.is_paused()):
                    await asyncio.sleep(0.1)
            await self.vc.disconnect()
            self.vc = None

        @self.command(name="loop")
        async def loop(ctx):
            self.loop_song = not self.loop_song
        
        @self.command(name="queue")
        async def queue(ctx):
            output = ""
            for yt, i in enumerate(self.queue):
                output += f"{i}: **{yt.title}**\n"
            
            await ctx.send(output[:-1])
        
        @self.command(name="enqueue")
        async def enqueue(ctx, link):
            try:
                yt = YouTube(link, use_oauth=True)
            except VideoUnavailable:
                return
            
            await ctx.send("Added **{yt.title}** to queue.")
            self.queue.append(yt)
        
        @self.command(name="dequeue")
        async def dequeue(ctx):
            if(len(self.queue) > 0):
                self.queue.popleft()
        
        @self.command(name="pause")
        async def pause(ctx):
            if(self.vc == None):
                await ctx.send("Not currently in a call.")
                return
            
            if(not self.vc.is_playing()):
                await ctx.send("Not currently playing anything.")
                return

            await ctx.send("Pausing playback.")
            await self.vc.pause()
        
        # stops playback and leaves call
        @self.command(name="stop")
        async def stop(ctx):
            if(self.vc == None):
                await ctx.send("Not currently in a call.")
                return

            await ctx.send("Stopping playback.")
            await self.vc.disconnect()
            self.vc = None

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
#   > skip/timestamps