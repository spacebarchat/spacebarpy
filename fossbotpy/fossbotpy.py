#to speed up importing fossbotpy & only import modules when they are needed
from .importmanager import Imports
imports = Imports(
	{
		'Wrapper': 'fossbotpy.requestsender',
		'Auth': 'fossbotpy.start.auth',
		'SuperProperties': 'fossbotpy.start.superproperties',
		'Other': 'fossbotpy.start.other',
		'Guild': 'fossbotpy.guild.guild',
		'Channels': 'fossbotpy.channels.channels',
		'User': 'fossbotpy.user.user',
		'Stickers': 'fossbotpy.stickers.stickers',
		'Science': 'fossbotpy.science.science',
	}
)

#logging to console/file
from .logger import LogLevel, Logger

#other imports
import time
import base64
import json
import re
import requests
import random

#client initialization
class Client:
	"""A fosscord client.
	can be used with or without a token

    Basic Usage:

      >>> import fossbotpy
      >>> bot = fossbotpy.Client()
      >>> bot.get_gateway_url()
      <Response [200]>

    Or as a context manager:

	  >>> import fossbotpy
      >>> with fossbotpy.Client() as bot:
      ...     bot.get_gateway_url()
      <Response [200]>
	"""
	__slots__ = [
		"log",
		"locale",
		"__user_token",
		"__user_email",
		"__user_password",
		"user_data",
		"__proxy_host",
		"__proxy_port",
		"api_version",
		"fosscord",
		"main_url",
		"websocketurl",
		"__user_agent",
		"s",
		"__super_properties",
		"gateway",
		"Science"
	]
	def __init__(
		self,
		token="",
		email="",
		password="",
		proxy_host=None,
		proxy_port=None,
		user_agent="random",
		locale="en-US",
		build_num="request",
		base_url="https://dev.fosscord.com/api/v9/",
		log={"console": True, "file": False}
	):
		#step 1: vars
		self.log = log
		self.locale = locale
		self.__user_token = token
		self.__user_email = email
		self.__user_password = password
		self.user_data = {} #used if science requests are used
		self.__proxy_host = None if proxy_host in (None,False) else proxy_host
		self.__proxy_port = None if proxy_port in (None,False) else proxy_port
		url_params = re.search(r'(https?):\/\/(.*api)?(\/v\d)?', base_url).groups()
		self.api_version = int(url_params[2][2:]) if len(url_params)>2 else 9
		self.fosscord = base_url+'/' if not base_url.endswith('/') else base_url
		self.main_url = main_url = url_params[0]+'//'+url_params[1][:-4]

		#step 2: user agent
		if user_agent != 'random':
			self.__user_agent = user_agent
		else:
			import random_user_agent.user_agent #only really want to import this if needed
			self.__user_agent = random_user_agent.user_agent.UserAgent(limit=100).get_random_user_agent()
			Logger.log('Randomly generated user agent: '+self.__user_agent, None, log)

		#step 3: http request headers (modified from dolfies's d.py-self)
		headers = {
			'Accept': '*/*',
			'Accept-Encoding': 'gzip, deflate',
			'Accept-Language': self.locale,
			'Cache-Control': 'no-cache',
			'Connection': 'keep-alive',
			'Origin': main_url,
			'Pragma': 'no-cache',
			'Referer': '{}/channels/@me'.format(main_url),
			'Sec-CH-UA-Mobile': '?0',
			'Sec-CH-UA-Platform': '"Windows"',
			'Sec-Fetch-Dest': 'empty',
			'Sec-Fetch-Mode': 'cors',
			'Sec-Fetch-Site': 'same-origin',
			'User-Agent': self.__user_agent,
			'X-Debug-Options': 'logGatewayEvents,logOverlayEvents,logAnalyticsEvents,bugReporterEnabled'
		}
		self.s = requests.Session()
		self.s.headers.update(headers)
		if self.__proxy_host != None: #self.s.proxies defaults to {}
			proxies = {
			'http': 'http://{}:{}'.format(self.__proxy_host, self.__proxy_port),
			'https': 'https://{}:{}'.format(self.__proxy_host, self.__proxy_port)
			}
			self.s.proxies.update(proxies)

		#step 4: cookies
		self.s.cookies.update({'locale': self.locale})

		#step 5: super-properties + Sec-CH-UA headers
		self.__super_properties = imports.SuperProperties(self.s, build_num, log).get_super_properties(self.__user_agent, self.locale)
		jsonsp = json.dumps(self.__super_properties).encode()
		self.s.headers.update({'X-Super-Properties': base64.b64encode(jsonsp).decode('utf-8')})
		browser_version = self.__super_properties['browser_version']
		self.s.headers.update({'Sec-CH-UA': '"Google Chrome";v="{0}", "Chromium";v="{0}", ";Not A Brand";v="99"'.format(browser_version.split('.')[0])})

		#step 6: token/authorization
		login_needed = token in ('', None, False) and {email, password}.isdisjoint({'', None, False})
		if login_needed:
			login_response = self.login(email, password)
			self.__user_token = login_response.json().get('token') #update token from '' to actual value
		self.s.headers.update({'Authorization': self.__user_token}) #update headers

		#step 7: gateway (object initialization)
		from .gateway.gateway import GatewayServer
		try:
			self.websocketurl = self.get_gateway_url().json()['url']
		except:
			self.websocketurl = url_params[1]
			if url_params[1].endswith('/api'):
				self.websocketurl = self.websocketurl[:-4]
		self.websocketurl += '/?encoding=json&v={}'.format(self.api_version) #&compress=zlib-stream #fosscord's zlib-stream is kinda broken rn
		self.gateway = GatewayServer(self.websocketurl, self.__user_token, self.__super_properties, self.s, self.fosscord, log)

		#step 8: somewhat prepare for science events
		self.Science = ''

##########################################################

	"""
	context manager stuff
	"""
	def __enter__(self):
		return self
	def __exit__(self, type, value, traceback):
		pass

	"""
	test token
	"""
	def check_token(self, token):
		"""checks if a token is valid, locked, or invalid

		Parameters
		----------
		token : str
		password : str

		Returns
		-------
		tuple of booleans
			(is_valid, is_locked)
		"""
		edited_s = imports.Wrapper().edited_req_session(self.s, {'update':{'Authorization':token}})
		user = imports.User(self.fosscord, edited_s, self.log)
		settings_test = user.enable_dev_mode(True)
		info_test = user.info()
		if settings_test.status_code == 200:
			Logger.log('Valid, non-locked token.', None, self.log)
		elif info_test.status_code == 204:
			Logger.log('Valid, but locked token.', None, self.log)
		else:
			Logger.log('Invalid token.', None, self.log)
		return settings_test, info_test

	"""
	start
	"""
	def register(self, email=None, username=None, password=None, invite=None, dob='1970-01-01', gift_code_sku_id=None, captcha=None):
		"""registers an account
		options:
			email, username, and password
			email and username
			only username (unclaimed account)
			no inputs (randomly generated username, unclaimed account)

		Parameters
		----------
		email : str (optional)
		username : str (optional)
			required if email is used
		password : str (optional)
		invite : str (optional)
			the invite code, not the full invite url
		dob : str (optional)
			date of birth; yyyy-mm-dd format; defaults to '1970-01-01'
		gift_code_sku_id : str (optional)
			unknown
		captcha : str (optional)
			captcha solution

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{"token": str}
			```
		"""
		return imports.Auth(self.s, self.fosscord, self.log).register(email, username, password, invite, dob, gift_code_sku_id, captcha)

	def login(self, emailphone, password, undelete=False, source=None, gift_code_sku_id=None, captcha=None):
		"""login to an account with email/phone and password

		Parameters
		----------
		emailphone : str
			email or phone number (ex: '+10000000000')
		password : str
		undelete : bool (optional)
			recover a deleted account
		source : str (optional)
			unknown
		gift_code_sku_id : str (optional)
			unknown
		captcha : str (optional)
			captcha solution

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{
				"token": str,
				"settings": {
					"afk_timeout": int,
					"allow_accessibility_detection": bool,
					"animate_emoji": bool,
					"animate_stickers": int,
					"contact_sync_enabled": bool,
					"convert_emoticons": bool,
					"custom_status": dict,
					"default_guilds_restricted": bool,
					"detect_platform_accounts": bool,
					"developer_mode": bool,
					"disable_games_tab": bool,
					"enable_tts_command": bool,
					"explicit_content_filter": int,
					"friend_source_flags": dict,
					"gateway_connected": bool,
					"gif_auto_play": bool,
					"guild_folders": list,
					"guild_positions": list,
					"inline_attachment_media": bool,
					"inline_embed_media": bool,
					"locale": str,
					"message_display_compact": bool,
					"native_phone_integration_enabled": bool,
					"render_embeds": bool,
					"render_reactions": bool,
					"restricted_guilds": list,
					"show_current_game": bool,
					"status": str,
					"stream_notifications_enabled": bool,
					"theme": "str",
					"timezone_offset": int,
				},
			}
			```
		"""
		return imports.Auth(self.s, self.fosscord, self.log).login(emailphone, password, undelete, captcha, source, gift_code_sku_id)

	def get_build_number(self):
		"""get build number of fosscord instance

		Returns
		-------
		int or None
		"""
		return imports.SuperProperties(self.s, 'request', self.log).request_build_number()

	def get_super_properties(self, user_agent, build_num='request', locale=None):
		"""get super properties dict

		Parameters
		----------
		user_agent : str
		build_num : int (optional)
			requests the build number from fosscord by default
		locale : str (optional)
			ex: 'en-US'

		Returns
		-------
		[super properties dictionary](https://luna.gitlab.io/discord-unofficial-docs/science.html#super-properties-object)
		"""
		return imports.SuperProperties(self.s, build_num, self.log).get_super_properties(user_agent, locale) #self.locale

	def get_gateway_url(self):
		"""get gateway url

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{"url": str}
			```
		"""
		return imports.Other(self.s, self.fosscord, self.log).get_gateway_url()

	def get_detectables(self):
		"""get detectable applications (doesn't do anything)

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			[]
			```
		"""
		return imports.Other(self.s, self.fosscord, self.log).get_detectables()

	def get_oauth2_tokens(self):
		"""get oauth2 tokens (doesn't do anything)

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			[]
			```
		"""
		return imports.Other(self.s, self.fosscord, self.log).get_oauth2_tokens()

	"""
	Messages
	"""
	def create_dm(self, recipients):
		"""create a dm / dm group

		Parameters
		----------
		recipients : list
			list of user id strings. str input also accepted if only creating a dm with 1 user
		
		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{
				"icon": str or None,
				"id": str,
				"last_message_id": str or None,
				"name": str or None,
				"origin_channel_id": str or None,
				"owner_id": str or None,
				"type": 1,
				"recipients": [
					{
						"avatar": str or None,
						"discriminator": str,
						"id": str,
						"public_flags": int,
						"username": str,
					}
				],
			}
			```
		"""
		return imports.Channels(self.fosscord, self.s, self.log).create_dm(recipients)

	def delete_channel(self, channel_id):
		"""delete a channel, thread, or dm

		Parameters
		----------
		channel_id : str
			channel id string

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).delete_channel(channel_id)

	def remove_from_dm_group(self, channel_id, user_id):
		"""remove a user from a dm group

		Parameters
		----------
		channel_id : str
		user_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).remove_from_dm_group(channel_id, user_id)

	def add_to_dm_group(self, channel_id, user_id):
		"""add user to dm group

		Parameters
		----------
		channel_id : str
		user_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).add_to_dm_group(channel_id, user_id)

	def create_dm_group_invite(self, channel_id, max_age_seconds=86400):
		"""add user to dm group

		Parameters
		----------
		channel_id : str
		max_age_seconds : int (optional)
			number of seconds for invite to last. Defaults to 86400 (24 hrs)

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).create_dm_group_invite(channel_id, max_age_seconds)

	def set_dm_group_name(self, channel_id, name):
		"""set the name of a dm group

		Parameters
		----------
		channel_id : str
		name : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).set_dm_group_name(channel_id, name)

	def set_dm_group_icon(self, channel_id, image_path):
		"""set the icon of a dm group

		Parameters
		----------
		channel_id : str
		image_path : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).set_dm_group_icon(channel_id, image_path)

	def get_messages(self, channel_id, num=1, before_date=None, around_message=None):
		"""get past messages in a channel

		Parameters
		----------
		channel_id : str
		num : str (optional)
			number of messages to fetch, between 0 and 100 inclusive. Defaults to 1
		before_date : str (optional)
			fosscord snowflake
		around_message : str (optional)
			message id string. Doesn't work yet in fosscord...

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).get_messages(channel_id, num, before_date, around_message)

	def send_message(self, channel_id, message='', nonce='calculate', tts=False, embed=None, reply_to=None, allowed_mentions=None, sticker_ids=None, file=None, is_url=False):
		"""send message to channel/DM/thread

		Parameters
		----------
		channel_id : str
		message : str (optional)
		nonce : str (optional)
			by default, the current discord snowflake is used
		tts : bool (optional)
			text to speech
		embed : dict (optional)
			can be constructed using fossbotpy.utils.embed.Embedder
		reply_to : list (optional)
			message (in a guild) that is being replied to. Format is ['guild id', 'channel id', 'message id'].
		allowed_mentions : dict (optional)
			who to ping when replying or mentioning others. Format is {'parse':['users','roles','everyone'],'replied_user':False}
		sticker_ids : list (optional)
			list of sticker id strings
		file : str (optional)
			local file path or file url
		is_url : bool (optional)
			If you set file to an file url, set is_url to True. Defaults to False

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See Message under Schemas at https://docs.fosscord.com/api/routes
		"""
		if reply_to != None:
			reply_to = {'guild_id':reply_to[0], 'channel_id':reply_to[1], 'message_id':reply_to[2]}
		if file == None:
			return imports.Channels(self.fosscord, self.s, self.log).send_message(channel_id, message, nonce, tts, embed, reply_to, allowed_mentions, sticker_ids)
		else:
			return imports.Channels(self.fosscord, self.s, self.log).send_file(channel_id, file, is_url, message, tts, embed, reply_to, sticker_ids)

	def typing_action(self, channel_id):
		"""send typing indicator for 10 seconds

		Parameters
		----------
		channel_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).typing_action(channel_id)

	def delete_message(self, channel_id, message_id):
		"""delete a message

		Parameters
		----------
		channel_id : str
		message_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).delete_message(channel_id, message_id)

	def edit_message(self, channel_id, message_id, new_message):
		"""delete a message

		Parameters
		----------
		channel_id : str
		message_id : str
		new_message : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See Message under Schemas at https://docs.fosscord.com/api/routes
		"""
		return imports.Channels(self.fosscord, self.s, self.log).edit_message(channel_id, message_id, new_message)

	def pin_message(self, channel_id, message_id):
		"""pin a message

		Parameters
		----------
		channel_id : str
		message_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).pin_message(channel_id, message_id)

	def unpin_message(self, channel_id, message_id):
		"""unpin a pinned message

		Parameters
		----------
		channel_id : str
		message_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).unpin_message(channel_id, message_id)

	def get_pins(self, channel_id):
		"""get a channel's pinned messages

		Parameters
		----------
		channel_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).get_pins(channel_id)

	def add_reaction(self, channel_id, message_id, emoji):
		"""add a reaction to a message

		Parameters
		----------
		channel_id : str
		message_id : str
		emoji : str
			if using a custom emoji, format is 'name:id'. For example: 'test:897982116313210027'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).add_reaction(channel_id, message_id, emoji)

	def remove_my_reaction(self, channel_id, message_id, emoji):
		"""remove my reaction from a message

		Parameters
		----------
		channel_id : str
		message_id : str
		emoji : str
			if using a custom emoji, format is 'name:id'. For example: 'test:897982116313210027'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).remove_my_reaction(channel_id, message_id, emoji)

	def remove_reaction(self, channel_id, message_id, emoji):
		"""remove a certain reaction from a message (ex: remove all thumbs up reactions from a message)

		Parameters
		----------
		channel_id : str
		message_id : str
		emoji : str
			if using a custom emoji, format is 'name:id'. For example: 'test:897982116313210027'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).remove_reaction(channel_id, message_id, emoji)

	def clear_reactions(self, channel_id, message_id):
		"""clear all reactions from message

		Parameters
		----------
		channel_id : str
		message_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).clear_reactions(channel_id, message_id)

	def get_reactions(self, channel_id, message_id, emoji, limit=100):
		"""get a message's reactions

		Parameters
		----------
		channel_id : str
		message_id : str
		emoji : str
			if using a custom emoji, format is 'name:id'. For example: 'test:897982116313210027'
		limit : int (optional)
			defaults to 100

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			[
				{
					"id": str,
					"username": str,
					"discriminator": str,
					"avatar": str or None,
					"accent_color": str or None,
					"banner": str or None,
					"bot": bool,
					"bio": str,
					"public_flags": int,
				},
			]
			```
		"""
		return imports.Channels(self.fosscord, self.s, self.log).get_reactions(channel_id, message_id, emoji, limit)

	def ack_message(self, channel_id, message_id, ack_token=None):
		"""mark a message as read (acknowledge message)

		Parameters
		----------
		channel_id : str
		message_id : str
		ack_token : str (optional)
			this is useless in fosscord

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).ack_message(channel_id,message_id,ack_token)

	def unack_message(self, channel_id, message_id, num_mentions=0):
		"""mark a message as unread (unacknowledge message)

		Parameters
		----------
		channel_id : str
		message_id : str
		num_mentions : int (optional)
			number of mentions to show up in your client

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Channels(self.fosscord, self.s, self.log).unack_message(channel_id, message_id, num_mentions)

	def get_trending_gifs(self, provider='tenor', locale='default', media_format='mp4'):
		"""fetch trending gifs

		Parameters
		----------
		provider : str (optional)
			turns out it doesn't matter what you set this to, fosscord will just use tenor
		locale : str (optional)
			defaults to whatever you set locale to when you initialized the client (which is, by default, 'en-US')
		media_format : str (optional)
			defaults to 'mp4'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{
				"categories": [
					{
						"name": str,
						"src": str
					},
				],
				"gifs": [
					{
						"id": str,
						"title": str,
						"url": str,
						"src": str,
						"gif_src": str,
						"width": int,
						"height": int,
						"preview": str
					},
				],
			}
			```
		"""
		if locale == 'default':
			locale = self.locale
		return imports.Channels(self.fosscord, self.s, self.log).get_trending_gifs(provider, locale, media_format)

	"""
	Stickers
	"""
	def get_stickers(self, country_code='default', locale='default'):
		"""fetch stickers

		Parameters
		----------
		country_code : str (optional)
			example: US
		locale : str (optional)
			defaults to whatever you set locale to when you initialized the client (which is, by default, 'en-US')

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{"sticker_packs": list}
			```
		"""
		if locale == 'default':
			locale = self.locale
		if country_code == 'default':
			country_code = locale.split('-')[-1]
		return imports.Stickers(self.fosscord, self.s, self.main_url, self.log).get_stickers(country_code, locale)

	def get_sticker_file(self, sticker_id):
		"""fetch sticker apng data
		size is always 460x460

		Parameters
		----------
		sticker_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Stickers(self.fosscord, self.s, self.main_url, self.log).get_sticker_file(sticker_id, sticker_asset)

	def get_sticker_pack(self, sticker_pack_id):
		"""fetch sticker pack
		doesn't work yet but is documented on docs.fosscord.com/api/routes ...

		Parameters
		----------
		sticker_pack_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.Stickers(self.fosscord, self.s, self.main_url, self.log).get_sticker_pack(sticker_pack_id)

	"""
	User relationships
	"""
	def get_relationships(self):
		"""get relationships
		returns status code 500...idk

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).get_relationships()

	def request_friend(self, user):
		"""create outgoing friend request

		Parameters
		----------
		user : str
			'user id' or 'user#discriminator'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).request_friend(user)

	def accept_friend(self, user_id, location='friends'):
		"""accept incoming friend request

		Parameters
		----------
		user_id : str
		location : str
			'friends', 'context menu', or 'user profile'. Defaults to 'friends'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).accept_friend(user_id, location)

	def remove_relationship(self, user_id, location='context menu'):
		"""remove friend, unblock user, OR reject friend request

		Parameters
		----------
		user_id : str
		location : str
			'friends', 'context menu', or 'user profile'. Defaults to 'context menu'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).remove_relationship(user_id, location)

	def block_user(self, user_id, location='context menu'):
		"""block user

		Parameters
		----------
		user_id : str
		location : str
			'friends', 'context menu', or 'user profile'. Defaults to 'context menu'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).block_user(user_id, location)

	"""
	Other user stuff
	"""
	def get_profile(self, user_id, with_mutual_guilds=True):
		"""get a user's profile

		Parameters
		----------
		user_id : str
		with_mutual_guilds : bool (optional)
			fetch data about mutual guilds. Defaults to True
			this parameter does not work on fosscord yet

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		```json
		{
			"connected_accounts": [],
			"premium_guild_since": str ("yyyy-mm-ddThh:mm:ss.SSSSSS+ZZ:ZZ") or None,
			"premium_since": str ("yyyy-mm-ddThh:mm:ss.SSSSSS+ZZ:ZZ") or None,
			"mutual_guilds": list,
			"user": {
				"username": str,
				"discriminator": str,
				"id": str,
				"public_flags": int,
				"avatar": str or None,
				"accent_color": str or None,
				"banner": str or None,
				"bio": str,
				"bot": bool,
			}
		}
		```
		"""
		return imports.User(self.fosscord, self.s, self.log).get_profile(user_id, with_mutual_guilds)

	def info(self):
		"""get bot info

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{
				"id": str,
				"username": str,
				"discriminator": str,
				"avatar": str or None,
				"accent_color": str or None,
				"banner": str or None,
				"phone": str or None,
				"premium": bool,
				"premium_type": int,
				"bot": bool,
				"bio": str,
				"nsfw_allowed": bool,
				"mfa_enabled": bool,
				"verified": bool,
				"disabled": bool,
				"email": str,
				"flags": str,
				"public_flags": int,
				"settings": dict
			}
			```
		"""
		return imports.User(self.fosscord, self.s, self.log).info()

	def get_user_affinities(self):
		"""get user affinities
		idk

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{"user_affinities": list, "inverse_user_affinities": list}
			```
		"""
		return imports.User(self.fosscord, self.s, self.log).get_user_affinities()

	def get_guild_affinities(self):
		"""get guild affinities
		idk

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			{"guild_affinities": list}
			```
		"""
		return imports.User(self.fosscord, self.s, self.log).get_guild_affinities()

	def get_voice_regions(self):
		"""get voice regions

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			[
				{
					"id": str,
					"name": str,
					"custom": bool,
					"deprecated": bool,
					"optimal": bool
				}, ...
			]
			```
		"""
		return imports.User(self.fosscord, self.s, self.log).get_voice_regions()

	"""
	Profile edits
	"""
	def set_avatar(self, image_path):
		"""set profile avatar

		Parameters
		----------
		image_path : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See UserPrivate under Schemas at https://docs.fosscord.com/api/routes
		"""
		return imports.User(self.fosscord, self.s, self.log).set_avatar(image_path)

	def set_profile_color(self, color=None):
		"""set profile color

		Parameters
		----------
		color : str (optional)
			can be constructed using fossbotpy.utils.color.Color
			Defaults to None

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See UserPrivate under Schemas at https://docs.fosscord.com/api/routes
		"""
		return imports.User(self.fosscord, self.s, self.log).set_profile_color(color)

	def set_username(self, name=None, discriminator=None, password=None):
		"""set profile username
		name and/or discriminator must be inputted

		Parameters
		----------
		name : str (optional)
			if not set, then discriminator must be set
		discriminator : str (optional)
			if not set, then name must be set
		password : str (optional)
			defaults to what you set it to when you initialized your client

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See UserPrivate under Schemas at https://docs.fosscord.com/api/routes
		"""
		if not any(name, discriminator):
			Logger.log('Error: name and/or discriminator must be inputted.', None, self.log)
			return
		if password == None:
			password = self.__user_password
		return imports.User(self.fosscord, self.s, self.log).set_username(name, discriminator, password)

	def set_email(self, email, password=None):
		"""set profile email

		Parameters
		----------
		email : str
		password : str (optional)
			defaults to what you set it to when you initialized your client

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See UserPrivate under Schemas at https://docs.fosscord.com/api/routes
		"""
		if password == None:
			password = self.__user_password
		return imports.User(self.fosscord, self.s, self.log).set_email(email, password)

	def set_password(self, new_password, password=None):
		"""set password

		Parameters
		----------
		new_password : str
		password : str (optional)
			defaults to what you set it to when you initialized your client

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See UserPrivate under Schemas at https://docs.fosscord.com/api/routes
		"""
		if password == None:
			password = self.__user_password
		return imports.User(self.fosscord, self.s, self.log).set_password(new_password, password)

	def set_about_me(self, bio):
		"""set profile bio

		Parameters
		----------
		bio : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See UserPrivate under Schemas at https://docs.fosscord.com/api/routes
		"""
		return imports.User(self.fosscord, self.s, self.log).set_about_me(bio)

	def set_banner(self, image_path):
		"""set profile banner

		Parameters
		----------
		image_path : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See UserPrivate under Schemas at https://docs.fosscord.com/api/routes
		"""
		return imports.User(self.fosscord, self.s, self.log).set_banner(image_path)

	def disable_account(self, password=None):
		"""disable account

		Parameters
		----------
		password : str (optional)
			defaults to what you set it to when you initialized your client

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		if password == None:
			password = self.__user_password
		return imports.User(self.fosscord, self.s, self.log).disable_account(password)

	def delete_account(self, password=None):
		"""delete account

		Parameters
		----------
		password : str (optional)
			defaults to what you set it to when you initialized your client

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		if password == None:
			password = self.__user_password
		return imports.User(self.fosscord, self.s, self.log).delete_account(password)

	"""
	User Settings, continued
	"""
	def set_dm_scan_lvl(self, level=0):
		"""set dm scan level

		Parameters
		----------
		level : int (optional)
			0 = do not scan
			1 = scan dms from everyone except friends
			2 = scan
			Defaults to 0

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).set_dm_scan_lvl(level)

	def allow_dms_from_guild_members(self, allow=True, disallowed_guild_ids=None):
		"""allow dms from guild members

		Parameters
		----------
		allow : bool (optional)
			defaults to True
		disallowed_guild_ids : list (optional)
			list of guild id strings

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).allow_dms_from_guild_members(allow, disallowed_guild_ids)

	def allow_friend_requests_from(self, types=['everyone', 'mutual_friends', 'mutual_guilds']):
		"""allow friend requests from...

		Parameters
		----------
		types : list (optional)
			who to allow friend reqs from. Defaults to ['everyone', 'mutual_friends', 'mutual_guilds'].

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).allow_friend_requests_from(types)

	def allow_screen_reader_tracking(self, allow=True):
		"""allow screen reader tracking

		Parameters
		----------
		allow : bool (optional)
			defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).allow_screen_reader_tracking(allow)

	def get_connected_accounts(self):
		"""get connected accounts

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			[]
			```
		"""
		return imports.User(self.fosscord, self.s, self.log).get_connected_accounts()

	def get_payment_sources(self):
		"""get payment sources

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			[]
			```
		"""
		return imports.User(self.fosscord, self.s, self.log).get_payment_sources()

	def get_billing_subscriptions(self):
		"""get billing subscriptions

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			```json
			[]
			```
		"""
		return imports.User(self.fosscord, self.s, self.log).get_billing_subscriptions()

	def set_theme(self, theme='dark'):
		"""set theme
		useless since you can only set dark theme

		Parameters
		----------
		theme : str (optional)
			only option is 'dark'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).set_theme(theme)

	def set_message_display(self, cozy_or_compact='cozy'):
		"""set message display

		Parameters
		----------
		cozy_or_compact : str (optional)
			defaults to 'cozy'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).set_message_display(cozy_or_compact)

	def enable_gif_auto_play(self, enable=True):
		"""enable/disable gif auto play

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_gif_auto_play(enable)

	def enable_animated_emoji(self, enable=True):
		"""enable/disable animated emoji

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_animated_emoji(enable)

	def set_sticker_animation(self, setting='always'):
		"""set sticker animation

		Parameters
		----------
		setting : str (optional)
			'always', 'interaction', or 'never'. Defaults to 'always'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).set_sticker_animation(setting)

	def enable_tts(self, enable=True):
		"""enable/disable text-to-speech

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_tts(enable)

	def enable_linked_image_display(self, enable=True):
		"""enable/disable rendering linked-images

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_linked_image_display(enable)

	def enable_image_display(self, enable=True):
		"""enable/disable displaying images

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_image_display(enable)

	def enable_link_preview(self, enable=True):
		"""enable/disable link preview

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_link_preview(enable)

	def enable_reaction_rendering(self, enable=True):
		"""enable/disable rendering reactions

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_reaction_rendering(enable)

	def enable_emoticon_conversion(self, enable=True):
		"""enable/disable convertion of emoticons to emojis

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_emoticon_conversion(enable)

	def set_afk_timeout(self, timeout_seconds):
		"""set push notification inactive timeout

		Parameters
		----------
		timeout_seconds : int
			in the site you can set from 60 seconds to 600 seconds

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).set_afk_timeout(timeout_seconds)

	def set_locale(self, locale):
		"""set locale

		Parameters
		----------
		locale : str
			ex: 'en-US'

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		response = imports.User(self.fosscord, self.s, self.log).set_locale(locale)
		self.locale = locale
		self.s.headers['Accept-Language'] = locale
		self.s.cookies['locale'] = locale
		return response

	def enable_dev_mode(self, enable=True): #boolean
		"""enable developer mode

		Parameters
		----------
		enable/disable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_dev_mode(enable)

	def enable_activity_display(self, enable=True):
		"""enable/disable displaying activities (note, status activities don't work yet on fosscord)

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_activity_display(enable)

	def enable_source_maps(self, enable=True):
		"""enable/disable source maps
		doesn't really work...

		Parameters
		----------
		enable : bool (optional)
			set to False to disable. Defaults to True

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		return imports.User(self.fosscord, self.s, self.log).enable_source_maps(enable)

	"""
	Guild/Server stuff
	"""
	#get guild info from invite code
	def get_invite(self,invite_code, with_counts=True, with_expiration=True, from_join_guild_nav=False):
		return imports.Guild(self.fosscord, self.s, self.log).get_invite(invite_code, with_counts, with_expiration, from_join_guild_nav)

	#join guild with invite code
	def join_guild(self, invite_code, location='markdown', wait=0):
		return imports.Guild(self.fosscord, self.s, self.log).join_guild(invite_code, location, wait)

	#preview/lurk-join guild. Only applies to current (gateway) session
	def preview_guild(self, guild_id, session_id=None):
		return imports.Guild(self.fosscord, self.s, self.log).preview_guild(guild_id, session_id)

	#leave guild
	def leave_guild(self, guild_id, lurking=False):
		return imports.Guild(self.fosscord, self.s, self.log).leave_guild(guild_id, lurking)

	#create invite
	def create_invite(self, channel_id, max_age_seconds=False, max_uses=False, grant_temp_membership=False, check_invite='', target_type=''):
		return imports.Guild(self.fosscord, self.s, self.log).create_invite(channel_id, max_age_seconds, max_uses, grant_temp_membership, check_invite, target_type)

	def delete_invite(self, invite_code):
		return imports.Guild(self.fosscord, self.s, self.log).delete_invite(invite_code)

	def get_guild_invites(self, guild_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_guild_invites(guild_id)

	def get_channel_invites(self, channel_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_channel_invites(channel_id)

	#get all guilds (this is used by the client when going to the developers portal)
	def get_guilds(self, with_counts=True):
		return imports.Guild(self.fosscord, self.s, self.log).get_guilds(with_counts)

	#get guild channels (this is used by the client when going to the server insights page for a guild)
	def get_guild_channels(self, guild_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_guild_channels(guild_id)

	#get discoverable guilds
	def get_discoverable_guilds(self, offset=0, limit=24):
		return imports.Guild(self.fosscord, self.s, self.log).get_discoverable_guilds(offset, limit)

	def get_guild_regions(self, guild_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_guild_regions(guild_id)

	#create a guild
	def create_guild(self, name, icon=None, channels=[], system_channel_id=None, template='2TffvPucqHkN'):
		return imports.Guild(self.fosscord, self.s, self.log).create_guild(name, icon, channels, system_channel_id, template)

	#delete a guild
	def delete_guild(self, guild_id):
		return imports.Guild(self.fosscord, self.s, self.log).delete_guild(guild_id)

	#kick a user
	def kick(self,guild_id,user_id,reason=''):
		return imports.Guild(self.fosscord, self.s, self.log).kick(guild_id,user_id,reason)

	#ban a user
	def ban(self,guild_id,user_id,delete_messagesDays=0,reason=''):
		return imports.Guild(self.fosscord, self.s, self.log).ban(guild_id,user_id,delete_messagesDays,reason)

	#unban a user
	def revoke_ban(self, guild_id, user_id):
		return imports.Guild(self.fosscord, self.s, self.log).revoke_ban(guild_id, user_id)

	#get guild templates
	def get_guild_templates(self, guild_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_guild_templates(guild_id)

	#get role member ids
	def get_role_member_ids(self, guild_id, role_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_role_member_ids(guild_id, role_id)

	#set roles of a member
	def set_member_roles(self, guild_id, member_id, role_ids):
		return imports.Guild(self.fosscord, self.s, self.log).set_member_roles(guild_id, member_id, role_ids)

	def get_channel(self, channel_id):
		"""get channel data

		Parameters
		----------
		channel_id : str

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
			See Channel under Schemas at https://docs.fosscord.com/api/routes
		"""
		return imports.Guild(self.fosscord, self.s, self.log).get_channel(channel_id)

	"""
	Science. Basically useless on fosscord.
	"""
	def init_science(self):
		try:
			#get analytics token
			response = self.info()
			if response.status_code in (400, 401):
				raise
			resjson = response.json()
			idcheck = res['id'] #if invalid token, this will error
			self.user_data = resjson
		except: #if token invalid
			self.user_data = {'analytics_token': None, 'id': '0'}

		#initialize Science object
		analytics_token = self.user_data.get('analytics_token', '')
		user_id = self.user_data['id']
		self.Science = imports.Science(self.fosscord, self.s, analytics_token, user_id, self.log)

	def science(self, events=[{}]):
		"""send some data over to fosscord

		Parameters
		----------
		events : list of event dictionaries (optional)
			defaults to [{}]

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
		"""
		if self.Science == '':
			self.init_science()
		return self.Science.science(events)

	def calculate_client_uuid(self, event_num='default', user_id='default', increment=True):
		"""calculate client uuid for science reqs

		Parameters
		----------
		event_num : int (optional)
			defaults to 0
		user_id : str (optional)
			defaults to your user id or current discord snowflake (if no user id)
		increment : bool (optional)
			client_uuids are sequencial. Defaults to True

		Returns
		-------
		client uuid string
		"""
		if self.Science == '':
			self.init_science()
		return self.Science.UUIDobj.calculate(event_num, user_id, increment)

	def refresh_client_uuid(self, reset_event_num=True):
		"""refresh client uuid

		Parameters
		----------
		reset_event_num : bool (optional)
			set event num to 0. Defaults to True

		Returns
		-------
		client uuid string
		"""
		if self.Science == '':
			self.init_science()
		return self.Science.UUIDobj.refresh(reset_event_num)

	def parse_client_uuid(self, client_uuid):
		"""parse client uuid

		Parameters
		----------
		client_uuid : str

		Returns
		-------
		dictionary with keys 'user_id', 'random_prefix', 'creation_time', 'event_num'
		"""
		if self.Science == '':
			#no sequential data needed for parsing
			self.Science = imports.Science(self.fosscord, self.s, None, '0', self.log)
			result = self.Science.UUIDobj.parse(client_uuid)
			self.Science = '' #reset
			return result
		else:
			return self.Science.UUIDobj.parse(client_uuid)
