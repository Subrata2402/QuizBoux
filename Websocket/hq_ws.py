import websockets, aiohttp
import discord, datetime
from discord.ext import commands
from database import db
import aniso8601, json
from config import *
stored_ws = {}
total_question = 0
question = None

class HQWebSocket(object):
	
	def __init__(self, guild_id: int, client: commands.Bot):
		self.guild_id = guild_id
		self.client = client
		self.game_is_live = False
		self.demo_ws = "wss://hqecho.herokuapp.com"
		self.host = "https://api-quiz.hype.space"
		self.icon_url = "https://media.discordapp.net/attachments/799861610654728212/977325044097228870/49112C0D-6021-4333-9E6D-5E385EEE77E1-modified.png"
		self.embed = discord.Embed(color = discord.Colour.random())
		self.socket_url = None
		self.answer_ids = None
	
	async def is_expired(self, token):
		"""Check either token is expired or not."""
		headers = {"Authorization": f"Bearer {token}"}
		async with aiohttp.ClientSession() as session:
			response = await session.get(self.host + "/users/me", headers = headers)
			if response.status != 200:
				await self.send_hook("The token has expired!")
				raise commands.CommandError("The token has expired")

	async def get_token(self):
		"""Take Authorization Bearer Token from the database for the different guild."""
		token = db.hq_details.find_one({"guild_id": self.guild_id})
		if not token:
			await self.send_hook("Please add HQ token to continue this process.")
			raise commands.CommandError("Token Not Found") # raise an exception if guild id not found in database
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
				raise commands.CommandError("Show details not found")
			response_data = await response.json()
			time = response_data["nextShowTime"]
			tm = aniso8601.parse_datetime(time).timestamp()
			self.prize = response_data["nextShowPrize"]
			self.game_is_live = response_data['active']
			if self.game_is_live:
				self.socket_url = response_data['broadcast']['socketUrl'].replace('https', 'wss')
			if send_hook:
				self.embed.title = "__Next Show Details !__"
				self.embed.description = f"Date : <t:{int(tm)}>\nPrize Money : ${prize}"
				self.embed.set_thumbnail(url = self.icon_url)
				self.embed.set_footer(text = "HQ Trivia")
				self.timestamp = datetime.datetime.utcnow()
				await self.send_hook(embed = self.embed)
			
	async def get_not_question(self, question) -> bool:
		"""Check either a question negative or not."""
		for negative_word in negative_words:
			if negative_word in question:
				not_question = True
				break
			else:
				not_question = False
		return not_question
			
	async def connect_ws(self, demo = None):
		"""Connect websocket."""
		await self.get_show_details()
		if not self.game_is_live and not demo:
			await self.send_hook("Game is not live!")
			raise commands.CommandError("Game is not live")
		token = await self.get_token()
		await self.is_expired(token)
		headers = {
			"Authorization": f"Bearer {token}",
			"x-hq-client": "iPhone8,2"
		}
		try:
			self.ws = await websockets.connect(self.demo_ws if demo else self.socket_url, extra_headers = None if demo else headers, ping_interval = 15)
		except Exception as e:
			print(e)
			return await self.send_hook("Something went wrong while creating the connection.")
		stored_ws[self.guild_id] = self.ws
		async for message in self.ws:
			message_data = json.loads(message)
			await self.send_hook(f"```\n{message_data}\n```")
			if message_data['type'] == 'gameStatus':
				await self.send_hook("Websocket Successfully Connected!")
				
			elif message_data['type'] == 'interaction':
				pass
			
			elif message_data['type'] == 'question':
				question = message_data['question']
				question_number = message_data['questionNumber']
				total_question = message_data['questionCount']
				options = [unidecode(ans["text"].strip()) for ans in message_data["answers"]]
				self.answer_ids = [ans["answerId"] for ans in message_data["answers"]]
				raw_question = str(question).replace(" ", "+")
				google_question = "https://google.com/search?q=" + raw_question
				u_options = "+or+".join(options)
				raw_options = str(u_options).replace(" ", "+")
				search_with_all = "https://google.com/search?q=" + raw_question + "+" + raw_options
				not_question = await self.get_not_question(question.lower())
				is_not = "(Not Question)" if not_question else ""
		
				self.embed.title = f"Question {question_number} out of {total_question} {is_not}"
				self.embed.description = f"[{question}]({google_question})\n\n[Search with all options]({search_with_all})"
				for index, option in enumerate(options):
					self.embed.add_field(name = f"Option - {order[index]}", value = f"[{option.strip()}]({google_question + '+' + str(option).strip().replace(' ', '+')})", inline = False)
				self.embed.set_footer(text = "HQ Trivia")
				self.embed.set_thumbnail(url = self.icon_url)
				self.embed.timestamp = datetime.datetime.utcnow()
				await self.send_hook(embed = self.embed)
			
			elif message_data["type"] == "questionClosed":
				pass