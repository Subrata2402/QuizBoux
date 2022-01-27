import discord
from discord.ext import commands
from Websocket.ws import Websocket
from database import db
import aiohttp

class MimirQuiz(commands.Cog, Websocket):
    
    def __init__(self, client):
        super().__init__()
        self.client = client
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Ready!")
        
    @commands.command()
    async def addtoken(self, ctx, token):
        """Update Token."""
        await ctx.message.delete()
        url = "https://api.mimir-prod.com//games/list?type=play_free"
        headers = {
            "host": "api.mimir-prod.com",
            "authorization": f"Bearer {token}",
            "user-agent": "Mozilla/5.0 (Linux; Android 10; RMX1827) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36",
            "content-type": "application/json",
            "accept": "*/*",
            "origin": "https://app.mimirquiz.com",
            "referer": "https://app.mimirquiz.com/",
            "accept-encoding": "gzip, deflate",
            "accept-language": "en-US,en;q=0.9"
            }
        async with aiohttp.ClientSession() as session:
            async with session.get(url = url, headers = headers) as response:
                if response.status != 200:
                    return await self.send_hook("The token is invalid or expired!")
                update = {"token": token}
                db.token.update_one({"id": "3250"}, {"$set": update})
                await self.send_hook("Successfully Updated!")
        
    @commands.command()
    async def tq(self, ctx):
        """Get how many questions has stored in database."""
        questions = list(db.question_base.find())
        await self.send_hook(f"Total Questions : {len(questions)}")
        
    @commands.command(aliases = ["quiz", "mimir"])
    async def nextquiz(self, ctx):
        """Get next quiz details."""
        await self.get_quiz_details("send")
    
    @commands.command(aliases = ["open"])
    async def start(self, ctx):
        """Start Websocket."""
        if not self.ws_is_opened:
            await self.start_hook()
        else:
            await self.send_hook("Websocket Already Opened!")
         
    @commands.command()
    async def close (self, ctx):
        """Close Websocket."""
        if self.ws_is_opened:
            await self.close_hook()
        else:
            await self.send_hook("Websocket Already Closed!")


client = commands.Bot(command_prefix = "m!", strip_after_prefix = True, case_insensitive = True)
client.add_cog(MimirQuiz(client))
            
client.run("Nzk5NDY4ODE4Mzc1NjM5MDUw.YAEBWw.OFUuud6gDHl5TYbcie3guwxPMI8")
