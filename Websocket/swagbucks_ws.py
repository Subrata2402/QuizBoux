import aiohttp, json, discord
from discord import commands
stored_ws = {}
from datetime import datetime
import websockets

class SbWebSocket(object):
	
	def __init__(self, client: commands.Bot, token: str):
		self.client = client
		self.token = token
		self.ws = None
		self.vid = None
		self.game_is_active = False
		self.partner_hash = None
		self.answer = 2
		self.host = "https://api.playswagiq.com/"
		self.icon_url = "https://cdn.discordapp.com/attachments/799861610654728212/991317134930092042/swagbucks_logo.png"
		self.headers = {
			"content-type": "application/x-www-form-urlencoded",
			"Host": "app.swagbucks.com",
			"user-agent": "SwagIQ-Android/34 (okhttp/3.10.0);Realme RMX1911",
			"accept-encoding": "gzip",
			"authorization": self.token
		}
		
	async def game_is_active(self) -> None:
		data = await self.fetch("POST", "trivia/join", headers = headers)
		if data["success"]:
			return self.game_is_active = True

	async def fetch(self, method = "GET", function = "", params = None, headers = None, data = None):
		"""
		Request Swagbucks to perform the action.
		"""
		async with aiohttp.ClientSession() as client_session:
			response = await client_session.request(method = method, url = self.host + function, params = params, headers = headers, data = data)
			if response.status != 200:
				await self.send_hook("Something went wrong!")
				#raise Exception("Something went Wrong!")
			return await response.json()
	
	async def send_answer(self, qid: str, aid: str):
		"""
		Send answer to the game.
		"""
		params = {
			"vid": self.vid, "qid": qid, "aid": aid, "timeDelta": 5000
		}
		#self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/answer", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully sent the answer.")
		else:
			await self.send_hook("Failed to send answer.\n```\n{}\n```".format(data))
	
	async def confirm_rebuy(self):
		"""
		If any question is wrong then we are eliminated.
		For come back and join again to the game we use a rejoin.
		To use this function we can send a rejoin. 
		"""
		params = {
			"vid": self.vid, "useLife": True, "partnerHash": self.partner_hash
		}
		#self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/rebuy_confirm", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully rejoin in the game.")
		else:
			await self.send_hook("Failed to rejoin in the game.\n```\n{}\n```".format(data))
			
	async def complete_game(self):
		"""
		After end of the game check the details won or not
		and how many sb earn from the live game.
		"""
		params = {
			"vid": self.vid
		}
		#self.headers["Authorization"] = "Bearer " + self.token
		data = await self.fetch("POST", "trivia/rebuy_confirm", headers = self.headers, params = params)
		success = data.get("success")
		if success:
			await self.send_hook("Successfully complete the game.")
			winner = data.get("winner")
			sb = data.get("sb")
			await self.send_hook("You {} the game and got {} SB!".format('won' if winner else 'lost', sb))
		else:
			await self.send_hook("Failed to complete the game.\n```\n{}\n```".format(data))
			
	async def show_details(self):
		"""
		Get the details of the current game show.
		"""
		data = await self.fetch("POST", "trivia/home", headers = headers)
		prize = data["episode"]["grandPrizeDollars"]
		time = data["episode"]["start"]
		embed=discord.Embed(title = "__SwagIQ Next Show Details !__", description=f"• Show Name : Swagbucks Live\n• Show Time : <t:{time}>\n• Prize Money : ${prize}", color = discord.Colour.random())
		embed.set_thumbnail(url = self.icon_url)
		embed.set_footer(text = "Swagbucks Live")
		embed.timestamp = datetime.utcnow()
		await self.send_hook(embed = embed)
	
	async def get_ws(self):
		"""
		Get Websocket.
		"""
		self.ws = stored_ws.get(self.token)

	async def close_ws(self):
		"""
		Close Websocket.
		"""
		await self.get_ws()
		if not self.ws:
			await self.send_hook("**Websocket Already Closed!**")
		else:
			if self.ws.closed:
				return await self.send_hook("**Websocket Already Closed!**")
			await self.ws.close()
			await self.send_hook("**Websocket Closed!**")
			
	async def send_hook(self, content = "", embed = None):
		"""
		Send message with Discord channel Webhook.
		"""
		web_url = await self.get_web_url()
		async with aiohttp.ClientSession() as session:
			webhook = discord.Webhook.from_url(web_url, adapter=discord.AsyncWebhookAdapter(session))
			await webhook.send(content = content, embed = embed, username = self.client.user.name, avatar_url = self.client.user.avatar_url)
			
	async def vid(self) -> None:
		"""
		Request viewId for connecting to the websocket.
		"""
		data = await self.fetch("POST", "trivia/join", headers = headers)
		self.vid = data["viewId"]
	
	async def connect_websocket(self):
		"""
		Try to onnect websocket.
		"""
		if not game_is_active:
			return await self.send_hook("Game is not live!")
		socket_url = "wss://api.playswagiq.com/sock/1/game/{}".format(self.vid)
		self.ws = await websockets.connect(socket_url, extra_headers = headers, ping_interval = 15)
		stored_ws[self.token] = self.ws
		rejoin_used = False
		await self.send_hook("Websocket successfully connected!")
		async for message in self.ws:
			message_data = json.loads(message)
			if message_data["code"] == 41:
				question_number = message_data["question"]["number"]
				total_question = message_data["question"]["totalQuestions"]
				question_id = message_data["question"]["idSigned"]
				answer_ids = [answer["idSigned"] for answer in message_data["question"]["answers"]]
				
				embed = discord.Embed(title = f"Question {question_number} out of {total_question}")
				await self.send_hook(embed = embed)
				
				try:
					user_input = await self.client.wait_for("message", timeout = 10.0)
					self.answer = int(user_input.content)
					answer_id = answer_ids[self.answer - 1]
					await self.send_answer(question_id, answer_id)
				except Exception as e:
					await self.send_hook("You failed to send your answer within time or something went wrong.\n```\n{}\n```".format(e))
					
			if message_data["code"] == 42:
				ansid = message_data["correctAnswerId"]
				for index, answer in enumerate(message_data["answerResults"]):
					if answer["answerId"] == ansid:
						ans_num = index + 1
				
				embed = discord.Embed(title = f"Correct Answer : {ans_num}")
				await self.send_hook(embed = embed)
				
				if self.answer != ans_num and not rejoin_used:
					await self.confirm_rebuy()
					
			if message_data["code"] == 49:
				await self.complete_game()
				await self.close_ws()