import websockets, aiohttp
import discord, datetime
from discord import commands
from database import db
stored_ws = []

class HQWebSocket(object):
	
	def __init__(self, guild_id: int, client: commands.Bot):
		self.guild_id = guild_id
		self.client = client
		self.game_is_live = False
		self.host = "https://api-quiz.hype.space"
		self.icon_url = ""
		self.embed = discord.Embed(color = discord.Colour.random())
		self.socket_url = None
	
	async def is_expired(self, token):
		"""Check either token is expired or not."""
		headers = {"Authorization": "Bearer " + token}
		async with aiohttp.ClientSession() as session:
			response = await session.get(self.host + "/users/me", headers = headers)
			if response.status != 200:
				await self.send_hook("The token has expired!")
				raise TokenExpired("The token has expired")

	async def get_token(self):
		"""Take Authorization Bearer Token from the database for the different guild."""
		token = db.hq_details.find_one({"guild_id": self.guild_id})
		if not token:
			await self.send_hook("Please add HQ token to continue this process.")
			raise TokenNotFound("Token Not Found") # raise an exception if guild id not found in database
		token = token.get("token")
		await self.is_expired(token)
		return token

	async def get_ws(self):
		"""Get Websocket."""
		self.ws = stored_ws.get(self.guild_id)

	async def close_ws(self):
		"""Close Websocket."""
		await self.get_ws()
		if not self.ws:
			await self.send_hook("**Websocket Already Closed!**")
		else:
			if self.ws.closed:
				return await self.send_hook("**Websocket Already Closed!**")
			await self.ws.close()
			await self.send_hook("**Websocket Closed!**")

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
			response = await session.get(self.host + "/shows/now")
			if response.status != 200:
				await self.send_hook("Something went wrong while fetching show details!")
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
			
	async def connect_ws(self, demo = None):
		"""Connect websocket."""
		await self.get_show_details()
		if not self.game_is_live and not demo:
			await self.send_hook("Game is not live!")
			raise NotLive("Game is not live")
		token = await self.get_token()
		headers = {
			"Authorization": f"Bearer {token}",
			"x-hq-client": "iPhone8,2"
		}
		self.ws = await websockets.connect(url = self.socket_url, extra_headers = headers, ping_interval = 15)
		stored_ws[self.guild_id] = self.ws
		async for message in self.ws:
			message_data = json.loads(message)
			await self.send_hook(f"```\n{message_data}\n```")
			if message_data['type'] == 'interaction':
				pass
			
			elif message_data['type'] == 'question':
				pass
				
			elif message_data["type"] == "questionClosed":
				pass