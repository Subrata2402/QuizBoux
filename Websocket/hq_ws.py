import websockets, aiohttp
import discord, requests, asyncio
from discord.ext import commands
from database import db
import aniso8601, json, threading
from bs4 import BeautifulSoup
from unidecode import unidecode
from datetime import datetime
from config import *
stored_ws = {}
question_number = total_question = 0


class HQWebSocket(object):
	
	def __init__(self, guild_id: int, client: commands.Bot):
		self.guild_id = guild_id
		self.client = client
		self.game_is_live = False
		self.demo_ws = "wss://hqecho.herokuapp.com"
		self.host = "https://api-quiz.hype.space"
		self.icon_url = "https://media.discordapp.net/attachments/799861610654728212/977325044097228870/49112C0D-6021-4333-9E6D-5E385EEE77E1-modified.png"
		self.socket_url = None
		self.answer_ids = None
		self.options = None
		self.pattern = []
	
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
				embed = discord.Embed(color = discord.Colour.random())
				embed.title = "__Next Show Details !__"
				embed.description = f"Date : <t:{int(tm)}>\nPrize Money : ${prize}"
				embed.set_thumbnail(url = self.icon_url)
				embed.set_footer(text = "HQ Trivia")
				self.timestamp = datetime.utcnow()
				await self.send_hook(embed = embed)
			
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
				global question_number, total_question
				question = message_data['question']
				question_number = message_data['questionNumber']
				total_question = message_data['questionCount']
				self.options = [unidecode(ans["text"].strip()) for ans in message_data["answers"]]
				self.answer_ids = [ans["answerId"] for ans in message_data["answers"]]
				raw_question = str(question).replace(" ", "+")
				google_question = "https://google.com/search?q=" + raw_question
				u_options = "+or+".join(self.options)
				raw_options = str(u_options).replace(" ", "+")
				search_with_all = "https://google.com/search?q=" + raw_question + "+" + raw_options
				not_question = await self.get_not_question(question.lower())
				is_not = "(Not Question)" if not_question else ""
		
				embed = discord.Embed(color = discord.Colour.random())
				embed.title = f"Question {question_number} out of {total_question} {is_not}"
				embed.description = f"[{question}]({google_question})\n\n[Search with all options]({search_with_all})"
				for index, option in enumerate(self.options):
					embed.add_field(name = f"Option - {order[index]}", value = f"[{option.strip()}]({google_question + '+' + str(option).strip().replace(' ', '+')})", inline = False)
				embed.set_footer(text = "HQ Trivia")
				embed.set_thumbnail(url = self.icon_url)
				embed.timestamp = datetime.utcnow()
				await self.send_hook(embed = embed)
				
				target_list = [
						self.rating_search_one(google_question, self.options, not_question),
						self.rating_search_two(google_question, self.options, not_question),
						self.direct_search_result(google_question, self.options),
					]
						#self.direct_search_result(search_with_all, choices)
				for target in target_list:
					thread = threading.Thread(target = lambda: asyncio.run(target))
					thread.start()
					
			elif message_data['type'] == 'answered':
				username = message_data["username"]
				ans_id = message_data["answerId"]
				for index, answer_id in enumerate(self.answer_ids):
					if ans_id == answer_id:
						option = self.options[index]
						embed = discord.Embed(color = discord.Colour.random())
						embed.title = f"__{username}__"
						embed.description = f"Option order[index]. {option}"
						await self.send_hook(embed = embed)
			
			elif message_data["type"] == "questionClosed":
				embed = discord.Embed(title = "⏰ | Time's Up!", color = discord.Colour.random())
				await self.send_hook(embed = embed)
				
			elif message_data["type"] == "questionSummary":
				question = message_data["question"]
				for index, answer in enumerate(message_data["answerCounts"]):
					if answer["correct"]:
						option = answer["answer"]
						ans_num = index + 1
				self.pattern.append(str(ans_num))
				advance_players = message_data['advancingPlayersCount']
				eliminate_players = message_data['eliminatedPlayersCount']
				ans = (int(self.prize))/(int(advance_players))
				payout = float("{:.2f}".format(ans))
				total_players = advance_players + eliminate_players
				percentAdvancing = (advance_players*100)/total_players
				pA = float("{:.2f}".format(percentAdvancing))
				percentEliminated = (eliminate_players*100)/total_players
				pE = float("{:.2f}".format(percentEliminated))
			
				embed = discord.Embed(
					title = f"Question {question_number} out of {total_question}",
					description = f"[{question}]({google_question})",
					color = discord.Colour.random(),
					timestamp = datetime.utcnow()
					)
				embed.add_field(name = "Correct Answer :-", value = f"Option {order[ans_num-1]}. {option}", inline = False)
				embed.add_field(name = "Status :-",
					value = f"Advancing Players : {advance_players} ({pA}%)\nEliminated Players : {eliminate_players} ({pE}%)\nCurrent Payout : ${payout}",
					inline = False
				)
				embed.add_field(name = "Ongoing Pattern :-", value = f"{self.pattern}", inline = False)
				embed.set_footer(text = "HQ Trivia")
				embed.set_thumbnail(url = self.icon_url)
				await self.send_hook(embed = embed)