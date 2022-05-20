import websockets, aiohttp
import discord, datetime
from discord import commands
from database import db

class HQWebSocket(object):
	
	def __init__(self, guild_id: int, client: commands.Bot):
		self.guild_id = guild_id
		self.client = client
		self.game_is_live = False
		self.api_url = "https://api-quiz.hype.space/shows/now"
		self.icon_url = ""
		self.embed = discord.Embed(color = discord.Colour.random())
		self.socket_url = None
	

	async def get_token(self):
		"""Take Authorization Bearer Token from the database for the different guild."""
		token = db.hq_details.find_one({"guild_id": self.guild_id})
		if not token:
			return token # return None if guild id not found in database
		token = token.get("token")
		return token

	async def get_web_url(self):
		"""Get discord channel Webhook url for different guild."""
		web_url = db.hq_details.find_one({"guild_id": self.guild_id})
		if not web_url:
			return web_url
		web_url = web_url.get("web_url")
		async with aiohttp.ClientSession() as session:
			response = await session.get(web_url)
			if response.status != 200:
				return None
		return web_url
		
	async def send_hook(self, content = "", embed = None):
		"""Send message with Discord channel Webhook."""
		web_url = await self.get_web_url()
		async with aiohttp.ClientSession() as session:
			webhook = discord.Webhook.from_url(web_url, adapter=discord.AsyncWebhookAdapter(session))
			await webhook.send(content = content, embed = embed, username = self.client.user.name, avatar_url = self.client.user.avatar_url)
			
	async def get_show_details(self, send_hook = None):
		"""Get show details of HQ Trivia."""
		async with aiohttp.ClientSession() as session:
			response = await session.get(self.api_url)
			if response.status != 200:
				return await self.send_hook("Something went wrong while fetching show details!")
				raise ShowNotFound("Show details not found")
			response_data = await response.json()
			time = response_data["nextShowTime"].timestamp()
			self.prize = response_data["nextShowPrize"]
			self.game_is_live = response_data['active']
			if self.game_is_live:
				self.socket_url = response_data['broadcast']['socketUrl'].replace('https', 'wss')
			if send_hook:
				self.embed.title = "__Next Show Details !__"
				self.embed.description = f"Date : <t:{int(time)}>\nPrize Money : ${prize}"
				self.embed.set_thumbnail(url = self.icon_url)
				self.embed.set_footer(text = "HQ Trivia")
				self.timestamp = datetime.datetime.utcnow()
				await self.send_hook(embed = self.embed)
			
	async def connect_ws(self):
		await self.get_show_details()
		token = await self.get_token()
		headers = {
			"Authorization": f"Bearer {token}",
			"x-hq-client": "iPhone8,2"
		}