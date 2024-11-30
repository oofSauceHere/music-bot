# i perhaps may hate python classes

import os
import asyncio
import discord
from collections import deque
from discord.ext import commands
import yt_dlp
from dotenv import load_dotenv
load_dotenv()

YTDL_OPTS = {
    'format': 'bestaudio/best',
}

FFMPEG_OPTS = {
    'options': '-vn', # skip video
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTS)

class MusicBot(commands.Bot):
    # constructor
    def __init__(self, command_prefix, intents):
        super().__init__(command_prefix=command_prefix, intents=intents)
        self.remove_command("help") # uh oh
        self.vid_queue = deque()
        self.vc = None
        self.loop_vid = False
        self.curr_vid = None

    # bot starts
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

        # join user's call and play video from given YouTube link (or whatever's in the queue)
        @self.command(name="play")
        async def play(ctx, link=None):
            # doesn't play if user is not in a voice channel
            voice = ctx.author.voice
            if(voice == None):
                await ctx.send("You need to be in a voice channel.")
                return
            
            # no link specified
            if(link == None):
                # if in vc, resume playback, else try and play from queue
                if(self.vc != None):
                    if(self.vc.is_paused()):
                        await ctx.send("Resuming playback.")
                        self.vc.resume()
                        return
                    else:
                        await ctx.send("Already playing video.")
                        return
                elif(not self.vid_queue):
                    await ctx.send("Queue is empty/not currently playing anything.")
                    return
            else:
                # attempt to access YouTube link
                try:
                    # yt = YouTube(link)
                    yt =  ytdl.extract_info(link, download=False)
                except yt_dlp.utils.DownloadError:
                    return
                
                # if in vc, inform user that video is queued up
                if(self.vc != None):
                    await ctx.send(f"Added **{yt["title"]}** to queue.")
                    self.vid_queue.append(yt)
                    return
                else:
                    self.vid_queue.append(yt)
            
            # connects to voice channel and idles while audio plays
            self.vc = await voice.channel.connect()
            prev_source = None # so looping works efficiently, without the need to re-acquire source
            while((self.vid_queue or self.loop_vid) and self.vc != None):
                source = None

                # if we're looping, make sure to line up same video
                if(self.loop_vid and not prev_source == None):
                    source = prev_source
                else:
                    # remove front video from queue
                    yt = self.vid_queue[0]
                    self.vid_queue.popleft()

                    # make async?
                    source = discord.FFmpegPCMAudio(yt["url"], **FFMPEG_OPTS)
                    prev_source = source

                # play audio in vc
                await ctx.send(f"Currently playing **{yt["title"]}**.")
                self.vc.play(source) # should we define "after" parameter?
                self.curr_vid = yt["title"]

                # busy loop until song finishes
                while(self.vc.is_playing() or self.vc.is_paused()):
                    await asyncio.sleep(0.1)
            
            # leave vc
            await self.vc.disconnect()
            self.vc = None
            self.curr_vid = None
        
        @self.command(name="playing")
        async def playing(ctx):
            if(self.curr_vid == None):
                await ctx.send("Not currently playing anything.")
                return
            await ctx.send(f"Currently playing **{self.curr_vid.title}**.")

        # toggle loop variable
        @self.command(name="loop")
        async def loop(ctx):
            self.loop_vid = not self.loop_vid
            await ctx.send(f"Loop set to **{self.loop_vid}**")
        
        # print queue
        @self.command(name="queue")
        async def queue(ctx):
            output = ""
            for i, yt in enumerate(self.vid_queue):
                output = output + f"**{i+1} - {yt["title"]}**\n"
            
            if(self.vid_queue):
                await ctx.send(output[:-1]) # strip final newline
            else:
                await ctx.send("Queue is empty.")
        
        # add video to queue
        @self.command(name="add")
        async def add(ctx, link=None):
            if(link == None):
                await ctx.send("Please specify link.")
                return

            try:
                yt = ytdl.extract_info(link, download=False)
            except yt_dlp.utils.DownloadError:
                return
            
            await ctx.send(f"Added **{yt["title"]}** to queue.")
            self.vid_queue.append(yt)
        
        # remove video from queue (referenced via index)
        @self.command(name="delete")
        async def delete(ctx, index=1):
            if(not self.vid_queue):
                await ctx.send("Queue is empty.")
                return
            
            # bounds checking
            if(index <= len(self.vid_queue) and index > 0):
                await ctx.send(f"Removed **{self.vid_queue[index-1].title}** from queue.")
                del self.vid_queue[index-1] # delete from deque via index
            else:
                await ctx.send("Invalid index.")
        
        @self.command(name="clear")
        async def clear(ctx):
            if(not self.vid_queue):
                await ctx.send("Queue is empty.")
                return
            
            # bounds checking
            self.vid_queue.clear()
            await ctx.send("Cleared queue.")
        
        # change position of video in queue
        @self.command(name="move")
        async def move(ctx, old=-1, new=-1):
            # bounds checking
            if(old == -1 or new == -1):
                await ctx.send("Please specify where to move from/to.")
            if(old <= len(self.vid_queue) and old > 0 and new <= len(self.vid_queue) and new > 0):
                yt = self.vid_queue[old-1]
                self.vid_queue.insert(new, yt)
                del self.vid_queue[old-1] # inserting before displaces later videos
                await ctx.send(f"Moved **{yt["title"]}** to position {new}.")
            else:
                await ctx.send("Invalid index.")
        
        @self.command(name="skip")
        async def skip(ctx):
            if(self.vc == None):
                await ctx.send("Not currently in a call.")
                return
            
            # can simply stop playback - current play() loop will detect and continue
            self.vc.stop()
        
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
            self.curr_vid = None

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
#   > playlists (differentiate between servers?)
#       > maybe server-wide playlists?
#   > mapping links to sources (inefficient or awesome?)
#   > maybe add function to convert spotify song title to youtube link?
#       > much more involved and possibly flawed...
#   > timestamps
#   > check if user running command is in vc w/ bot
#   > voting for skip
#   > removeall
#   > play via title?
#   > lyrics?
#   > loop all (be sure to add songs only after queue is empty)