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
	__slots__ = ['log', 'locale', '__user_token', '__user_email', '__user_password', 'user_data', '__proxy_host', '__proxy_port', 'api_version', 'fosscord', 'main_url', 'websocketurl', '__user_agent', 's', '__super_properties', 'gateway', 'Science']
	def __init__(self, email='', password='', token='', proxy_host=None, proxy_port=None, user_agent='random', locale='en-US', build_num='request', base_url='https://dev.fosscord.com/api/v9/', log={'console':True, 'file':False}):
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
		#step 3: http request headers
		headers = {
			'Origin': main_url,
			'User-Agent': self.__user_agent,
			'Accept': '*/*',
			'Accept-Encoding': 'gzip, deflate',
			'Accept-Language': self.locale,
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'Referer': '{}/channels/@me'.format(main_url),
			'Sec-Fetch-Dest': 'empty',
			'Sec-Fetch-Mode': 'cors',
			'Sec-Fetch-Site': 'same-origin',
			'X-Debug-Options': 'logGatewayEvents,logOverlayEvents,logAnalyticsEvents,bugReporterEnabled',
			'Connection': 'keep-alive',
			'Content-Type': 'application/json'
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
		#step 5: super-properties (part of headers)
		self.__super_properties = imports.SuperProperties(self.s, build_num, log).get_super_properties(self.__user_agent, self.locale)
		jsonsp = json.dumps(self.__super_properties).encode()
		self.s.headers.update({'X-Super-Properties': base64.b64encode(jsonsp).decode('utf-8')})
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
		pass #logging out doesn't actually do anything so...

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
		settings_test = user.enable_dev_mode()
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
	def register(self, email, password, username=None, invite=None, dob='1970-01-01', gift_code_sku_id=None, captcha=None):
		"""registers an account

		Parameters
		----------
		email : str
		password : str
		username : str (optional)
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
		return imports.Auth(self.s, self.fosscord, self.log).register(email, password, username, invite, dob, gift_code_sku_id, captcha)

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
		"""
		return imports.Other(self.s, self.fosscord, self.log).get_detectables()

	def get_oauth2_tokens(self):
		"""get oauth2 tokens (doesn't do anything)

		Returns
		-------
		[requests.Response object](https://www.w3schools.com/python/ref_requests_response.asp)
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
			"premium_guild_since": str ('yyyy-mm-ddThh:mm:ss.SSSSSS+ZZ:ZZ') or None,
			"premium_since": str ('yyyy-mm-ddThh:mm:ss.SSSSSS+ZZ:ZZ') or None,
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
		return imports.User(self.fosscord, self.s, self.log).info(with_analytics_token)

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

	def get_mentions(self, limit=25, role_mentions=True, everyone_mentions=True):
		return imports.User(self.fosscord, self.s, self.log).get_mentions(limit, role_mentions, everyone_mentions)

	def remove_mention_from_inbox(self, message_id):
		return imports.User(self.fosscord, self.s, self.log).remove_mention_from_inbox(message_id)

	def get_my_stickers(self):
		return imports.User(self.fosscord, self.s, self.log).get_my_stickers()

	def get_rtc_regions(self):
		return imports.User(self.fosscord, self.s, self.log).get_rt_cregions()

	def get_voice_regions(self):
		return imports.User(self.fosscord, self.s, self.log).get_voice_regions()

	"""
	Profile edits
	"""
	# set avatar
	def set_avatar(self,image_path):
		return imports.User(self.fosscord, self.s, self.log).set_avatar(image_path)

	#set profile color
	def set_profile_color(self, color=None):
		return imports.User(self.fosscord, self.s, self.log).set_profile_color(color)

	#set username
	def set_username(self, name, discriminator): #USER PASSWORD NEEDS TO BE SET BEFORE THIS IS RUN
		return imports.User(self.fosscord, self.s, self.log).set_username(name, discriminator, password=self.__user_password)

	#set email
	def set_email(self, email): #USER PASSWORD NEEDS TO BE SET BEFORE THIS IS RUN
		return imports.User(self.fosscord, self.s, self.log).set_email(email, password=self.__user_password)

	#set password
	def set_password(self, new_password): #USER PASSWORD NEEDS TO BE SET BEFORE THIS IS RUN
		return imports.User(self.fosscord, self.s, self.log).set_password(new_password, password=self.__user_password)

	#set about me
	def set_about_me(self, bio):
		return imports.User(self.fosscord, self.s, self.log).set_about_me(bio)

	#set banner
	def set_banner(self, image_path):
		return imports.User(self.fosscord, self.s, self.log).set_banner(image_path)

	def disable_account(self, password):
		return imports.User(self.fosscord, self.s, self.log).disable_account(password)

	def delete_account(self, password):
		return imports.User(self.fosscord, self.s, self.log).delete_account(password)

	"""
	User Settings, continued
	"""
	def set_d_mscan_lvl(self, level=1): # 0<=level<=2
		return imports.User(self.fosscord, self.s, self.log).set_d_mscan_lvl(level)

	def allow_d_ms_from_server_members(self, allow=True, disallowed_guild_i_ds=None):
		return imports.User(self.fosscord, self.s, self.log).allow_d_ms_from_server_members(allow, disallowed_guild_i_ds)

	def allow_friend_requests_from(self, types=['everyone', 'mutual_friends', 'mutual_guilds']):
		return imports.User(self.fosscord, self.s, self.log).allow_friend_requests_from(types)

	def analytics_consent(self, grant=[], revoke=[]):
		return imports.User(self.fosscord, self.s, self.log).analytics_consent(grant, revoke)

	def allow_screen_reader_tracking(self, allow=True):
		return imports.User(self.fosscord, self.s, self.log).allow_screen_reader_tracking(allow)

	def request_my_data(self):
		return imports.User(self.fosscord, self.s, self.log).request_my_data()

	def get_connected_accounts(self):
		return imports.User(self.fosscord, self.s, self.log).get_connected_accounts()

	def get_connection_url(self, account_type):
		return imports.User(self.fosscord, self.s, self.log).get_connection_url(account_type)

	def enable_connection_display_on_profile(self, account_type, account_username, enable=True):
		return imports.User(self.fosscord, self.s, self.log).enable_connection_display_on_profile(account_type, account_username, enable)

	def enable_connection_display_on_status(self, account_type, account_username, enable=True):
		return imports.User(self.fosscord, self.s, self.log).enable_connection_display_on_status(account_type, account_username, enable)

	def remove_connection(self, account_type, account_username):
		return imports.User(self.fosscord, self.s, self.log).remove_connection(account_type, account_username)

	def get_billing_history(self, limit=20):
		return imports.User(self.fosscord, self.s, self.log).get_billing_history(limit)

	def get_payment_sources(self):
		return imports.User(self.fosscord, self.s, self.log).get_payment_sources()

	def get_billing_subscriptions(self):
		return imports.User(self.fosscord, self.s, self.log).get_billing_subscriptions()

	def get_stripe_client_secret(self):
		return imports.User(self.fosscord, self.s, self.log).get_stripe_client_secret()

	def set_theme(self, theme): #'light' or 'dark'
		return imports.User(self.fosscord, self.s, self.log).set_theme(theme)

	def set_message_display(self, CozyOrCompact): #'cozy' or 'compact'
		return imports.User(self.fosscord, self.s, self.log).set_message_display(CozyOrCompact)

	def enable_gif_auto_play(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord, self.s, self.log).enable_gif_auto_play(enable)

	def enable_animated_emoji(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord, self.s, self.log).enable_animated_emoji(enable)

	def set_sticker_animation(self, setting): #string, default='always'
		return imports.User(self.fosscord, self.s, self.log).set_sticker_animation(setting)

	def enable_tts(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord, self.s, self.log).enable_tts(enable)

	def enable_linked_image_display(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord, self.s, self.log).enable_linked_image_display(enable)

	def enable_image_display(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord, self.s, self.log).enable_image_display(enable)

	def enable_link_preview(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord, self.s, self.log).enable_link_preview(enable)

	def enable_reaction_rendering(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord, self.s, self.log).enable_reaction_rendering(enable)

	def enable_emoticon_conversion(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord, self.s, self.log).enable_emoticon_conversion(enable)

	def set_af_ktimeout(self, timeout_seconds):
		return imports.User(self.fosscord, self.s, self.log).set_af_ktimeout(timeout_seconds)

	def set_locale(self, locale):
		response = imports.User(self.fosscord, self.s, self.log).set_locale(locale)
		self.locale = locale
		self.s.headers['Accept-Language'] = self.locale
		self.s.cookies['locale'] = self.locale
		return response

	def enable_dev_mode(self, enable=True): #boolean
		return imports.User(self.fosscord, self.s, self.log).enable_dev_mode(enable)

	def activate_application_test_mode(self, application_id):
		return imports.User(self.fosscord, self.s, self.log).activate_application_test_mode(application_id)

	def get_application_data(self, application_id, with_guild=False):
		return imports.User(self.fosscord, self.s, self.log).get_application_data(application_id, with_guild)

	def enable_activity_display(self, enable=True):
		return imports.User(self.fosscord, self.s, self.log).enable_activity_display(enable)

	def set_hypesquad(self, house):
		return imports.User(self.fosscord, self.s, self.log).set_hypesquad(house)

	def leave_hypesquad(self):
		return imports.User(self.fosscord, self.s, self.log).leave_hypesquad()

	def get_build_overrides(self):
		return imports.User(self.fosscord, self.s, self.log).get_build_overrides()

	def enable_source_maps(self, enable=True):
		return imports.User(self.fosscord, self.s, self.log).enable_source_maps()

	def suppress_everyone_pings(self, guild_id, suppress=True):
		return imports.User(self.fosscord, self.s, self.log).suppress_everyone_pings(guild_id, suppress)

	def suppress_role_mentions(self, guild_id, suppress=True):
		return imports.User(self.fosscord, self.s, self.log).suppress_role_mentions(guild_id, suppress)

	def enable_mobile_push_notifications(self, guild_id, enable=True):
		return imports.User(self.fosscord, self.s, self.log).enable_mobile_push_notifications(guild_id, enable)

	def set_channel_notification_overrides(self, guild_id, overrides):
		return imports.User(self.fosscord, self.s, self.log).set_channel_notification_overrides(guild_id, overrides)

	def set_message_notifications(self, guild_id, notifications):
		return imports.User(self.fosscord, self.s, self.log).set_message_notifications(guild_id, notifications)

	def mute_guild(self, guild_id, mute=True, duration=None):
		return imports.User(self.fosscord, self.s, self.log).mute_guild(guild_id, mute, duration)

	def mute_dm(self, DMID, mute=True, duration=None):
		return imports.User(self.fosscord, self.s, self.log).mute_dm(DMID, mute, duration)

	def set_thread_notifications(self, thread_id, notifications):
		return imports.User(self.fosscord, self.s, self.log).set_thread_notifications(thread_id, notifications)

	def get_report_menu(self):
		return imports.User(self.fosscord, self.s, self.log).get_report_menu()

	def report_spam(self, channel_id, message_id, report_type='first_dm', guild_id=None, version='1.0', variant='1', language='en'):
		return imports.User(self.fosscord, self.s, self.log).report_spam(channel_id, message_id, report_type, guild_id, version, variant, language)

	def get_handoff_token(self, key):
		return imports.User(self.fosscord, self.s, self.log).get_handoff_token(key)

	def invite_to_call(self, channel_id, user_ids=None):
		return imports.User(self.fosscord, self.s, self.log).invite_to_call(channel_id, user_ids)

	def decline_call(self, channel_id):
		return imports.User(self.fosscord, self.s, self.log).decline_call(channel_id)

	def logout(self, provider=None, voip_provider=None):
		return imports.User(self.fosscord, self.s, self.log).logout(provider, voip_provider)

	"""
	Guild/Server stuff
	"""
	#get guild info from invite code
	def get_info_from_invite_code(self,invite_code, with_counts=True, with_expiration=True, from_join_guild_nav=False):
		return imports.Guild(self.fosscord, self.s, self.log).get_info_from_invite_code(invite_code, with_counts, with_expiration, from_join_guild_nav)

	#join guild with invite code
	def join_guild(self, invite_code, location='accept invite page', wait=0):
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

	def get_channelInvites(self, channel_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_channelInvites(channel_id)

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

	#get number of members in each role
	def get_role_member_counts(self, guild_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_role_member_counts(guild_id)

	#get integrations (includes applications aka bots)
	def get_guild_integrations(self, guild_id, include_applications=True):
		return imports.Guild(self.fosscord, self.s, self.log).get_guild_integrations(guild_id, include_applications)

	#get guild templates
	def get_guild_templates(self, guild_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_guild_templates(guild_id)

	#get role member ids
	def get_role_member_i_ds(self, guild_id, role_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_role_member_i_ds(guild_id, role_id)

	#add members to role (add a role to multiple members at the same time)
	def add_members_to_role(self, guild_id, role_id, member_ids):
		return imports.Guild(self.fosscord, self.s, self.log).add_members_to_role(guild_id, role_id, member_ids)

	#set roles of a member
	def set_member_roles(self, guild_id, member_id, role_i_ds):
		return imports.Guild(self.fosscord, self.s, self.log).set_member_roles(guild_id, member_id, role_i_ds)

	def get_member_verification_data(self, guild_id, with_guild=False, invite_code=None):
		return imports.Guild(self.fosscord, self.s, self.log).get_member_verification_data(guild_id, with_guild, invite_code)

	def agree_guild_rules(self, guild_id, form_fields, version='2021-01-05T01:44:32.163000+00:00'):
		return imports.Guild(self.fosscord, self.s, self.log).agree_guild_rules(guild_id, form_fields, version)

	def create_thread(self, channel_id, name, message_id=None, public=True, archive_after='24 hours'):
		return imports.Guild(self.fosscord, self.s, self.log).create_thread(channel_id, name, message_id, public, archive_after)

	def leave_thread(self, thread_id, location='Sidebar Overflow'):
		return imports.Guild(self.fosscord, self.s, self.log).leave_thread(thread_id, location)

	def join_thread(self, thread_id, location='Banner'):
		return imports.Guild(self.fosscord, self.s, self.log).join_thread(thread_id, location)

	def archive_thread(self, thread_id, lock=True):
		return imports.Guild(self.fosscord, self.s, self.log).archive_thread(thread_id, lock)

	def unarchive_thread(self, thread_id, lock=False):
		return imports.Guild(self.fosscord, self.s, self.log).unarchive_thread(thread_id, lock)

	def get_live_stages(self, extra=False):
		return imports.Guild(self.fosscord, self.s, self.log).get_live_stages(extra)

	def get_channel(self, channel_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_channel(channel_id)

	def get_guild_activities_config(self, guild_id):
		return imports.Guild(self.fosscord, self.s, self.log).get_guild_activities_config(guild_id)

	"""
	Science. Basically useless on fosscord.
	"""
	def init_science(self):
		try:
			#get analytics token
			response = imports.User(self.fosscord, self.s, self.log).info(True)
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
