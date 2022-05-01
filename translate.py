from deep_translator import GoogleTranslator
from database import db

async def translate(guild_id, text):
	language = db.mimir_details.find_one({"guild_id": guild_id}).get("language")
	if not language: language = "en"
	translated = GoogleTranslator(source='auto', target=language).translate(text)
	return translated