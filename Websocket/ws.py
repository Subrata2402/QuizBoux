import requests
import json
import discord
from discord.ext import commands
import datetime
from sseclient import SSEClient
import aiohttp
import asyncio
from bs4 import BeautifulSoup
google_question = "https://google.com/search?q="
question_number = total_question = 0
from database import db


class Websocket:
	
	def __init__(self):
		self.prize = 50
		self.pattern = []
		self.web_url = "https://discord.com/api/webhooks/935981741833871430/y8HWuzK074QDQhBzRlxnR5P5OQn3etGsLUuqP-JDJMk8NzjpMnu7NW2PHjc2f87aylSB"
		self.token = None
		self.ws_is_opened = False
		self.icon_url = "https://cdn.discordapp.com/emojis/924632014617972736.png"
		self.game_is_active = False
		self.game_id = None
		self.partner_id = None
		self.user_id = None
		self.bearer_token = None

	async def close_hook(self):
		self.ws_is_opened == False
		print("Websocket Closed!")
		await self.send_hook("**Websocket Closed!**")

	async def get_token(self):
		token = db.token.find_one({"id": "3250"})["token"]
		self.token = token

	async def send_hook(self, content = "", embed = None):
		async with aiohttp.ClientSession() as session:
			webhook = discord.Webhook.from_url(self.web_url, adapter=discord.AsyncWebhookAdapter(session))
			await webhook.send(
				content = content,
				embed = embed,
				username = "Mimir Quiz",
				avatar_url = self.icon_url
				)
				
	async def get_answer(self, question):
		question = db.question_base.find_one({"question": question})
		if not question:
			return None
		answer = question.get("answer")
		return answer

	async def add_question(self, question, answer):
		check = db.question_base.find_one({"question": question})
		if not check:
			db.question_base.insert_one({"question": question, "answer": answer})
				
	async def get_quiz_details(self, get_type = None):
		await self.get_token()
		url = "https://api.mimir-prod.com//games/list?type=play_free"
		headers = {
			"host": "api.mimir-prod.com",
			"authorization": f"Bearer {self.token}",
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
					await self.send_hook("**The Auth token has expired!**")
					raise commands.CommandError("Token has expired!")
				r = await response.json()
				data = r["data"]["data"][0]
				self.game_is_active = data["active"]
				image = data["backgroundImageLandscapeUrl"]
				topic = data["label"]
				description = data["description"]
				self.prize = data["reward"]
				time = f'<t:{int(data["scheduled"]/1000)}>'
				gameType = data["winCondition"]
				self.game_id = data["id"]
				self.partner_id = data["partnerId"]
				embed = discord.Embed(
					title = "**__Mimir Upcoming Quiz Details !__**",
					description = description,
					color = discord.Colour.random(),
					timestamp = datetime.datetime.utcnow()
					)
				embed.add_field(name = "Quiz Topic :", value = topic, inline = False)
				embed.add_field(name = "Prize Money :", value = f"ᛗ{self.prize}", inline = False)
				embed.add_field(name = "Date & Time :", value = time, inline = False)
				embed.set_footer(text = "Mimir Quiz")
				embed.set_thumbnail(url = image)
				if get_type == "send":
					await self.send_hook(embed = embed)

	async def get_access_token(self):
		await self.get_quiz_details()
		url = f"https://apic.us.theq.live/v2/oauth/token?partnerCode={self.partner_id}"
		headers = {
			"host": "apic.us.theq.live",
			"user-Agent": "Mozilla/5.0 (Linux; Android 10; RMX1827) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36",
			"accept": "application/json, text/plain, */*",
			"content-type":"application/json",
			"origin": "https://play.us.theq.live",
			"referer": "https://play.us.theq.live/",
			"accept-encoding": "gzip, deflate",
			"accept-language": "en-US,en;q=0.9"
		}
		post_data = json.dumps({"mimir":{"accessToken": self.token}})
		async with aiohttp.ClientSession() as session:
			async with session.post(url = url, headers = headers, data = post_data) as response:
				if response.status != 200:
					await self.send_hook("**Access Token Error...**")
					raise commands.CommandError("Get access token error...")
				r = await response.json()
				new_token = r["oauth"]["accessToken"]
				token_type = r["oauth"]["tokenType"]
				self.user_id = r["user"]["id"]
				self.bearer_token = token_type + " " + new_token
				
	async def get_host(self):
		await self.get_access_token()
		url = f"https://apic.us.theq.live/v2/games/active/{self.game_id}?userId={self.user_id}"
		headers = {
			"Host": "apic.us.theq.live",
			"accept": "application/json, text/plain, */*",
			"authorization": f"{self.bearer_token}",
			"sec-ch-ua-mobile": "?1",
			"user-agent": "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.98 Mobile Safari/537.36",
			"origin": "https://play.us.theq.live",
			"referer": "https://play.us.theq.live/",
			"accept-encoding": "gzip, deflate, br",
			"accept-language": "en-US,en;q=0.9,bn;q=0.8,hi;q=0.7"
		}
		async with aiohttp.ClientSession() as session:
			async with session.get(url = url, headers = headers) as response:
				if response.status != 200:
					await self.send_hook("**Host Error...(Game is not live)**")
					raise commands.CommandError("Host Error")
				r = await response.json()
				data = r["game"]
				self.game_is_active = data["active"]
				host = data["host"]
				return host

	async def start_hook(self):
		host = await self.get_host()
		url = f"https://{host}/v2/event-feed/games/{self.game_id}"
		headers = {
			"Host": host,
			"Connection": "keep-alive",
			"Authorization": self.bearer_token,
			"Accept": "text/event-stream",
			"Cache-Control": "no-cache",
			"User-Agent": "Mozilla/5.0 (Linux; Android 10; RMX1827) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.99 Mobile Safari/537.36",
			"Origin": "https://play.us.theq.live",
			"Sec-Fetch-Site": "same-site",
			"Sec-Fetch-Mode": "cors",
			"Referer": "https://play.us.theq.live/",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": "en-US,en;q=0.9"
		}
		try:
			messages = SSEClient(url, headers = headers)
			await self.send_hook("**Websocket Connecting...**")
		except:
			return await self.send_hook("**Failed to Connect Websocket!**")
		self.ws_is_opened = True
		for msg in messages:
			event = msg.event
			print(event)
			if self.ws_is_opened == False:
				return
			
			if event == "GameStatus":
				await self.send_hook("**Websocket is Connected Successfully!**")

			elif event == "ViewCountUpdate":
				pass

			elif event == "GameReset":
				await self.send_hook(embed = discord.Embed(title = "The Game has Reset!", color = discord.Colour.random()))

			elif event == "QuestionStart":
				global google_question, question_number, total_question
				data = json.loads(msg.data)
				question = str(data["question"]).strip()
				question_number = data["number"]
				total_question = data["total"]
				response_time = data["secondsToRespond"]
				choices = data["choices"]
				option_1 = str(choices[0]["choice"]).strip()
				option_2 = str(choices[1]["choice"]).strip()
				if len(choices) >= 3: option_3 = str(choices[2]["choice"]).strip()
				if len(choices) == 4: option_4 = str(choices[3]["choice"]).strip()
				raw_question = str(question).replace(" ", "+")
				raw_options = str(f"{option_1} + {option_2} + {option_3 if len(choices) >= 3 else ''} + {option_4 if len(choices) == 4 else ''}").replace(" ", "+")
				google_question = "https://google.com/search?q=" + raw_question
				search_with_all = "https://google.com/search?q=" + raw_question + raw_options
				
				embed = discord.Embed(
					title = f"**Question {question_number} out of {total_question}**",
					description = f"**[{question}]({google_question})\n\n[Search with all options]({search_with_all})**",
					color = discord.Colour.random()
					)
				embed.add_field(name = "**Option - １**", value = f"**[{option_1}]({search_with_all})**", inline = False)
				embed.add_field(name = "**Option - ２**", value = f"**[{option_2}]({search_with_all})**", inline = False)
				if len(choices) >= 3: embed.add_field(name = "**Option - ３**", value = f"**[{option_3}]({search_with_all})**", inline = False)
				if len(choices) == 4: embed.add_field(name = "**Option - ４**", value = f"**[{option_4}]({search_with_all})**", inline = False)
				embed.set_thumbnail(url = self.icon_url)
				embed.set_footer(text = f"Response Time : {response_time} seconds")
				await self.send_hook(embed = embed)
				
				answer = await self.get_answer(question)
				if answer: await self.send_hook(embed = discord.Embed(title = answer, color = discord.Colour.random()))
				
				r = requests.get(google_question)
				soup = BeautifulSoup(r.text, 'html.parser')
				response = soup.find_all("span", class_="st")
				res = str(r.text)
				cnop1 = res.count(option_1)
				cnop2 = res.count(option_2)
				cnop3 = cnop4 = 0
				if len(choices) >= 3: cnop3 = res.count(option_3)
				if len(choices) == 4: cnop4 = res.count(option_4)
				maxcount = max(cnop1, cnop2, cnop3 if len(choices) >= 3 else 0, cnop4 if len(choices) == 4 else 0)
				mincount = min(cnop1, cnop2, cnop3 if len(choices) >= 3 else 0, cnop4 if len(choices) == 4 else 0)
				embed = discord.Embed(title="**__Google Results !__**", color = discord.Colour.random())
				if len(choices) == 4:
					if cnop1 == maxcount:
						embed.description=f"**１. {option_1} : {cnop1}**  ✅\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}**\n４. **{option_4} : {cnop4}**"
					elif cnop2 == maxcount:
						embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**  ✅\n**３. {option_3} : {cnop3}**\n４. **{option_4} : {cnop4}**"
					elif cnop3 == maxcount:
						embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}** ✅\n４. **{option_4} : {cnop4}**"
					else:
						embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}**\n４. **{option_4} : {cnop4}** ✅"
					await self.send_hook(embed = embed)
				elif len(choices) == 3:
					if cnop1 == maxcount:
						embed.description=f"**１. {option_1} : {cnop1}**  ✅\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}**"
					elif cnop2 == maxcount:
						embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**  ✅\n**３. {option_3} : {cnop3}**"
					else:
						embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}**  ✅"
					await self.send_hook(embed = embed)
				else:
					if cnop1 == maxcount:
						embed.description=f"**１. {option_1} : {cnop1}**  ✅\n**２. {option_2} : {cnop2}**"
					else:
						embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}** ✅"
					await self.send_hook(embed = embed)
				
				r = requests.get(google_question)
				soup = BeautifulSoup(r.text , "html.parser")
				response = soup.find("div" , class_='BNeawe')
				result = str(response.text)
				embed = discord.Embed(
					description=result,
					color = discord.Colour.random(),
					timestamp = datetime.datetime.utcnow()
					)
				embed.set_footer(text="Search with Google")
				if len(choices) == 4:
					if option_1.lower() in result.lower():
						embed.title=f"**__Option １. {option_1}__**"
					elif option_2.lower() in result.lower():
						embed.title=f"**__Option ２. {option_2}__**"
					elif option_3.lower() in result.lower():
						embed.title=f"**__Option ３. {option_3}__**"
					elif option_4.lower() in result.lower():
						embed.title=f"**__Option ４. {option_4}__**"
					else:
						embed.title=f"**__Direct Search Result !__**"
					await self.send_hook(embed = embed)
				elif len(choices) == 3:
					if option_1.lower() in result.lower():
						embed.title=f"**__Option １. {option_1}__**"
					elif option_2.lower() in result.lower():
						embed.title=f"**__Option ２. {option_2}__**"
					elif option_3.lower() in result.lower():
						embed.title=f"**__Option ３. {option_3}__**"
					else:
						embed.title=f"**__Direct Search Result !__**"
					await self.send_hook(embed = embed)
				else:
					if option_1.lower() in result.lower():
						embed.title=f"**__Option １. {option_1}__**"
					elif option_2.lower() in result.lower():
						embed.title=f"**__Option ２. {option_2}__**"
					else:
						embed.title=f"**__Direct Search Result !__**"
					await self.send_hook(embed = embed)

				try:
					r = requests.get("https://duckduckgo.com/search?q=" + raw_question)
					soup = BeautifulSoup(r.text, 'html.parser')
					response = soup.find_all("span", class_="st")
					res = str(r.text)
					cnop1 = res.count(option_1)
					cnop2 = res.count(option_2)
					cnop3 = cnop4 = 0
					if len(choices) >= 3: cnop3 = res.count(option_3)
					if len(choices) == 4: cnop4 = res.count(option_4)
					maxcount = max(cnop1, cnop2, cnop3 if len(choices) >= 3 else 0, cnop4 if len(choices) == 4 else 0)
					mincount = min(cnop1, cnop2, cnop3 if len(choices) >= 3 else 0, cnop4 if len(choices) == 4 else 0)
					embed = discord.Embed(title="**__DuckDuckGo Results !__**", color = discord.Colour.random())
					if len(choices) == 4:
						if cnop1 == maxcount:
							embed.description=f"**１. {option_1} : {cnop1}**  ✅\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}**\n４. **{option_4} : {cnop4}**"
						elif cnop2 == maxcount:
							embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**  ✅\n**３. {option_3} : {cnop3}**\n４. **{option_4} : {cnop4}**"
						elif cnop3 == maxcount:
							embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}** ✅\n４. **{option_4} : {cnop4}**"
						else:
							embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}**\n４. **{option_4} : {cnop4}** ✅"
						await self.send_hook(embed = embed)
					elif len(choices) == 3:
						if cnop1 == maxcount:
							embed.description=f"**１. {option_1} : {cnop1}**  ✅\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}**"
						elif cnop2 == maxcount:
							embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**  ✅\n**３. {option_3} : {cnop3}**"
						else:
							embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}**\n**３. {option_3} : {cnop3}**  ✅"
						await self.send_hook(embed = embed)
					else:
						if cnop1 == maxcount:
							embed.description=f"**１. {option_1} : {cnop1}**  ✅\n**２. {option_2} : {cnop2}**"
						else:
							embed.description=f"**１. {option_1} : {cnop1}**\n**２. {option_2} : {cnop2}** ✅"
						await self.send_hook(embed = embed)
				except:
					pass

			elif event == "QuestionEnd":
				embed = discord.Embed(title = "Question has Ended!", color = discord.Colour.random())
				await self.send_hook(embed = embed)

			elif event == "QuestionResult":
				data = json.loads(msg.data)
				question = str(data["question"]).strip()
				total_players = 0
				for index, choice in enumerate(data["choices"]):
					if choice["correct"] == True:
						ans_num = index + 1
						answer = str(choice["choice"]).strip()
						advance_players = choice["responses"]
					total_players += choice["responses"]
				self.pattern.append(str(ans_num))
				await self.add_question(question, answer)
				eliminate_players = total_players - advance_players
				percentAdvancing = (int(advance_players)*(100))/total_players
				pA = float("{:.2f}".format(percentAdvancing))
				percentEliminated = (int(eliminate_players)*(100))/total_players
				pE = float("{:.2f}".format(percentEliminated))
				ans = (self.prize)/(advance_players)
				payout = float("{:.2f}".format(ans))
				embed = discord.Embed(
					title = f"**Question {question_number} out of {total_question}**",
					description = f"**[{question}]({google_question})**",
					color = discord.Colour.random(),
					timestamp = datetime.datetime.utcnow()
					)
				embed.add_field(name = "**Correct Answer :-**", value = f"**Option {ans_num}. {answer}**", inline = False)
				embed.add_field(name = "**Status :-**",
					value = f"**Advancing Players : {advance_players} ({pA}%)\nEliminated Players : {eliminate_players} ({pE}%)\nCurrent Payout : ᛗ{payout}**",
					inline = False
				)
				embed.add_field(name = "**Ongoing Pattern :-**", value = f"**{self.pattern}**", inline = False)
				embed.set_footer(text = "Mimir Quiz")
				embed.set_thumbnail(url = self.icon_url)
				await self.send_hook(embed = embed)

			elif event == "GameWinners":
				data = json.loads(msg.data)
				winners = int(data["winnerCount"])
				ans = (self.prize)/(winners)
				payout = float("{:.2f}".format(ans))
				embed = discord.Embed(title = "**__Game Summary !__**",
					description = f"**● Payout : ᛗ{payout}\n● Total Winners : {winners}\n● Prize Money : ᛗ{self.prize}**",
					color = discord.Colour.random(),
					timestamp = datetime.datetime.utcnow()
					)
				embed.set_thumbnail(url = self.icon_url)
				embed.set_footer(text = "Mimir Quiz")
				await self.send_hook(embed = embed)
				
			elif event == "GameEnded":
				embed = discord.Embed(title = "**__Game has Ended !__**",
					description = "**Thanks for playing!**", color = discord.Colour.random()
					)
				await self.send_hook(embed = embed)
				self.pattern.clear()
				await self.close_hook()
				return
