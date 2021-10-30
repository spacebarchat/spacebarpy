#to speed up importing fossbotpy & only import modules when they are needed
from .importmanager import Imports
imports = Imports(
	{
		"Wrapper": "fossbotpy.RESTapiwrap",
		"Auth": "fossbotpy.start.auth",
		"SuperProperties": "fossbotpy.start.superproperties",
		"Other": "fossbotpy.start.other",
		"Guild": "fossbotpy.guild.guild",
		"Messages": "fossbotpy.messages.messages",
		"User": "fossbotpy.user.user",
		"Stickers": "fossbotpy.stickers.stickers",
		"Science": "fossbotpy.science.science",
	}
)

#logging to console/file
from .logger import * #imports LogLevel and Logger

#other imports
import time
import base64
import json
import re
import requests
import random

#client initialization
class Client:
	__slots__ = ['log', 'locale', '__user_token', '__user_email', '__user_password', 'user_data', '__proxy_host', '__proxy_port', 'api_version', 'fosscord', 'websocketurl', '__user_agent', 's', '__super_properties', 'gateway', 'Science']
	def __init__(self, email="", password="", token="", proxy_host=None, proxy_port=None, user_agent="random", locale="en-US", build_num="request", base_url="https://dev.fosscord.com/api/v9/", log={"console":True, "file":False}):
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
		self.fosscord = base_url
		if not base_url.endswith('/'):
			self.fosscord += '/'
		main_url = url_params[0]+'//'+url_params[1][:-4]
		#step 2: user agent
		if user_agent != "random":
			self.__user_agent = user_agent
		else:
			import random_user_agent.user_agent #only really want to import this if needed
			self.__user_agent = random_user_agent.user_agent.UserAgent(limit=100).get_random_user_agent()
			Logger.log('Randomly generated user agent: '+self.__user_agent, None, log)
		#step 3: http request headers
		headers = {
			"Origin": main_url,
			"User-Agent": self.__user_agent,
			"Accept": "*/*",
			"Accept-Encoding": "gzip, deflate, br",
			"Accept-Language": self.locale,
			"Cache-Control": "no-cache",
			"Pragma": "no-cache",
			"Referer": "{}/channels/@me".format(main_url),
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-origin",
			"X-Debug-Options": "bugReporterEnabled",
			"Connection": "keep-alive",
			"Content-Type": "application/json"
		}
		self.s = requests.Session()
		self.s.headers.update(headers)
		if self.__proxy_host != None: #self.s.proxies defaults to {}
			proxies = {
			'http': "http://" + self.__proxy_host+':'+self.__proxy_port,
			'https': "https://" + self.__proxy_host+':'+self.__proxy_port
			}
			self.s.proxies.update(proxies)
		#step 4: cookies
		self.s.cookies.update({"locale": self.locale})
		#step 5: super-properties (part of headers)
		self.__super_properties = imports.SuperProperties(self.s, buildnum=build_num, log=log).get_super_properties(self.__user_agent, self.locale)
		self.s.headers.update({"X-Super-Properties": base64.b64encode(json.dumps(self.__super_properties).encode()).decode("utf-8")})
		#step 6: token/authorization
		token_provided = self.__user_token not in ("",None,False)
		if not token_provided:
			login_response = imports.Auth(self.s, self.fosscord, log).login(email=email, password=password, undelete=False, captcha=None, source=None, gift_code_sku_id=None)
			self.__user_token = login_response.json().get('token') #update token from "" to actual value
		self.s.headers.update({"Authorization": self.__user_token}) #update headers
		#step 7: gateway (object initialization)
		from .gateway.gateway import GatewayServer
		self.websocketurl = imports.Other(self.s, self.fosscord, self.log).get_gateway_url().json()['url']
		self.websocketurl += '/?encoding=json&v={}'.format(self.api_version) #&compress=zlib-stream #fosscord's zlib-stream is kinda broken rn
		self.gateway = GatewayServer(self.websocketurl, self.__user_token, self.__super_properties, self.s, self.fosscord, log) #self.s contains proxy host and proxy port already
		#step 8: somewhat prepare for science events
		self.Science = ""

##########################################################

	'''
	test token
	'''
	def check_token(self, token):
		edited_s = imports.Wrapper().edited_req_session(self.s, {"update":{"Authorization":token}})
		settings_test = imports.User(self.fosscord, edited_s, self.log).enable_dev_mode().status_code == 200
		info_test = imports.User(self.fosscord, edited_s, self.log).info().status_code == 204
		if settings_test:
			Logger.log("Valid, non-locked token.", None, self.log)
		elif info_test == 200:
			Logger.log("Valid, but locked token.", None, self.log)
		else:
			Logger.log("Invalid token.", None, self.log)
		return settings_test, info_test

	'''
	start
	'''
	def register(self, email, password, username=None, invite=None, dob="1970-01-01", gift_code_sku_id=None, captcha=None):
		return imports.Auth(self.s, self.fosscord, self.log).register(email, password, username, invite, dob, gift_code_sku_id, captcha)

	def login(self, email, password, undelete=False, source=None, gift_code_sku_id=None, captcha=None):
		return imports.Auth(self.s, self.fosscord, self.log).login(email, password, undelete, captcha, source, gift_code_sku_id)

	def get_build_number(self):
		return imports.SuperProperties(self.s, "request", self.log).request_build_number()

	def get_super_properties(self, user_agent, buildnum="request", locale=None):
		return imports.SuperProperties(self.s, buildnum, self.log).get_super_properties(user_agent, locale) #self.locale

	def get_gateway_url(self):
		return imports.Other(self.s, self.fosscord, self.log).get_gateway_url()

	def get_detectables(self):
		return imports.Other(self.s, self.fosscord, self.log).get_detectables()

	def get_oauth2_tokens(self):
		return imports.Other(self.s, self.fosscord, self.log).get_oauth2_tokens()

	'''
	Messages
	'''
	#create DM
	def create_dm(self,recipients):
		return imports.Messages(self.fosscord,self.s,self.log).create_dm(recipients)

	#delete channel/DM/DM group
	def delete_channel(self, channel_id):
		return imports.Messages(self.fosscord,self.s,self.log).delete_channel(channel_id)

	#remove from DM group
	def remove_from_dm_group(self, channel_id, user_id):
		return imports.Messages(self.fosscord,self.s,self.log).remove_from_dm_group(channel_id, user_id)

	#add to DM group
	def add_to_dm_group(self, channel_id, user_id):
		return imports.Messages(self.fosscord,self.s,self.log).add_to_dm_group(channel_id, user_id)

	#create DM group invite link
	def create_dm_group_invite(self, channel_id, max_age_seconds=86400):
		return imports.Messages(self.fosscord,self.s,self.log).create_dm_group_invite(channel_id, max_age_seconds)

	#change DM group name
	def set_dm_group_name(self, channel_id, name):
		return imports.Messages(self.fosscord,self.s,self.log).set_dm_group_name(channel_id, name)

	#change DM icon
	def set_dm_group_icon(self, channel_id, image_path):
		return imports.Messages(self.fosscord,self.s,self.log).set_dm_group_icon(channel_id, image_path)

	#get recent messages
	def get_messages(self,channel_id,num=1,before_date=None,around_message=None): # num <= 100, before_date is a snowflake
		return imports.Messages(self.fosscord,self.s,self.log).get_messages(channel_id,num,before_date,around_message)

	#get message by channel ID and message ID
	def get_message(self, channel_id, message_id):
		return imports.Messages(self.fosscord,self.s,self.log).get_message(channel_id, message_id)

	#greet with stickers
	def greet(self, channel_id, sticker_ids=["749054660769218631"]):
		return imports.Messages(self.fosscord,self.s,self.log).greet(channel_id, sticker_ids)

	#send messages
	def send_message(self, channel_id, message="", nonce="calculate", tts=False, embed=None, message_reference=None, allowed_mentions=None, sticker_ids=None):
		return imports.Messages(self.fosscord,self.s,self.log).send_message(channel_id, message, nonce, tts, embed, message_reference, allowed_mentions, sticker_ids)

	#send files (local or link)
	def send_file(self,channel_id,filelocation,isurl=False,message="", tts=False, message_reference=None, sticker_ids=None):
		return imports.Messages(self.fosscord,self.s,self.log).send_file(channel_id,filelocation,isurl,message, tts, message_reference, sticker_ids)

	#reply, with a message and/or file
	def reply(self, guild_id, channel_id, message_id, message="", nonce="calculate", tts=False, embed=None, allowed_mentions={"parse":["users","roles","everyone"],"replied_user":False}, sticker_ids=None, file=None, isurl=False):
		return imports.Messages(self.fosscord,self.s,self.log).reply(guild_id, channel_id, message_id, message, nonce, tts, embed, allowed_mentions, sticker_ids, file, isurl)

	#search messages
	def search_messages(self, guild_id=None, channel_id=None, author_id=None, author_type=None, mentions_user_id=None, has=None, link_hostname=None, embed_provider=None, embed_type=None, attachment_extension=None, attachment_filename=None, mentions_everyone=None, include_nsfw=None, after_date=None, before_date=None, text_search=None, after_num_results=None, limit=None):
		return imports.Messages(self.fosscord,self.s,self.log).search_messages(guild_id, channel_id, author_id, author_type, mentions_user_id, has, link_hostname, embed_provider, embed_type, attachment_extension, attachment_filename, mentions_everyone, include_nsfw, after_date, before_date, text_search, after_num_results, limit)

	#filter search_messages, takes in the output of search_messages (a requests response object) and outputs a list of target messages
	def filter_search_results(self,search_response):
		return imports.Messages(self.fosscord,self.s,self.log).filter_search_results(search_response)

	#sends the typing action for 10 seconds (or technically until you change the page)
	def typing_action(self,channel_id):
		return imports.Messages(self.fosscord,self.s,self.log).typing_action(channel_id)

	#delete message
	def delete_message(self,channel_id,message_id):
		return imports.Messages(self.fosscord,self.s,self.log).delete_message(channel_id,message_id)

	#edit message
	def edit_message(self,channel_id,message_id,new_message):
		return imports.Messages(self.fosscord,self.s,self.log).edit_message(channel_id, message_id, new_message)

	#pin message
	def pin_message(self,channel_id,message_id):
		return imports.Messages(self.fosscord,self.s,self.log).pin_message(channel_id,message_id)

	#un-pin message
	def un_pin_message(self,channel_id,message_id):
		return imports.Messages(self.fosscord,self.s,self.log).un_pin_message(channel_id,message_id)

	#get pinned messages
	def get_pins(self,channel_id):
		return imports.Messages(self.fosscord,self.s,self.log).get_pins(channel_id)

	#add reaction
	def add_reaction(self,channel_id,message_id,emoji):
		return imports.Messages(self.fosscord,self.s,self.log).add_reaction(channel_id,message_id,emoji)

	#remove reaction
	def remove_reaction(self,channel_id,message_id,emoji):
		return imports.Messages(self.fosscord,self.s,self.log).remove_reaction(channel_id,message_id,emoji)

	#acknowledge message (mark message read)
	def ack_message(self,channel_id,message_id,ack_token=None):
		return imports.Messages(self.fosscord,self.s,self.log).ack_message(channel_id,message_id,ack_token)

	#unacknowledge message (mark message unread)
	def un_ack_message(self,channel_id,message_id,num_mentions=0):
		return imports.Messages(self.fosscord,self.s,self.log).un_ack_message(channel_id,message_id,num_mentions)

	def bulk_ack(self, data):
		return imports.Messages(self.fosscord,self.s,self.log).bulk_ack(data)

	def get_trending_gifs(self, provider="tenor", locale="en-US", media_format="mp4"):
		return imports.Messages(self.fosscord,self.s,self.log).get_trending_gifs(provider, locale, media_format)

	'''
	Stickers
	'''
	def get_stickers(self, directory_id="758482250722574376", store_listings=False, locale="en-US"):
		return imports.Stickers(self.fosscord,self.s,self.log).get_stickers(directory_id, store_listings, locale)

	def get_sticker_file(self, sticker_id, sticker_asset): #this is an animated png
		return imports.Stickers(self.fosscord,self.s,self.log).get_sticker_file(sticker_id, sticker_asset)

	def get_sticker_json(self, sticker_id, sticker_asset):
		return imports.Stickers(self.fosscord,self.s,self.log).get_sticker_json(sticker_id, sticker_asset)

	def get_sticker_pack(self, sticker_pack_id):
		return imports.Stickers(self.fosscord,self.s,self.log).get_sticker_pack(sticker_pack_id)

	'''
	User relationships
	'''
	#get relationships
	def get_relationships(self):
		return imports.User(self.fosscord,self.s,self.log).get_relationships()

	#get mutual friends
	def get_mutual_friends(self, user_id):
		return imports.User(self.fosscord,self.s,self.log).get_mutual_friends(user_id)

	#create outgoing friend request
	def request_friend(self, user): #you can input a user_id(snowflake) or a user discriminator
		return imports.User(self.fosscord,self.s,self.log).request_friend(user)

	#accept incoming friend request
	def accept_friend(self, user_id, location="friends"):
		return imports.User(self.fosscord,self.s,self.log).accept_friend(user_id, location)

	#remove friend OR unblock user
	def remove_relationship(self, user_id, location="context menu"):
		return imports.User(self.fosscord,self.s,self.log).remove_relationship(user_id, location)

	#block user
	def block_user(self, user_id, location="context menu"):
		return imports.User(self.fosscord,self.s,self.log).block_user(user_id, location)

	'''
	Other user stuff
	'''
	def get_profile(self, user_id, with_mutual_guilds=True):
		return imports.User(self.fosscord,self.s,self.log).get_profile(user_id, with_mutual_guilds)

	def info(self, with_analytics_token=None):
		return imports.User(self.fosscord,self.s,self.log).info(with_analytics_token)

	def get_user_affinities(self):
		return imports.User(self.fosscord,self.s,self.log).get_user_affinities()

	def get_guild_affinities(self):
		return imports.User(self.fosscord,self.s,self.log).get_guild_affinities()

	def get_mentions(self, limit=25, role_mentions=True, everyone_mentions=True):
		return imports.User(self.fosscord,self.s,self.log).get_mentions(limit, role_mentions, everyone_mentions)

	def remove_mention_from_inbox(self, message_id):
		return imports.User(self.fosscord,self.s,self.log).remove_mention_from_inbox(message_id)

	def get_my_stickers(self):
		return imports.User(self.fosscord,self.s,self.log).get_my_stickers()

	def get_notes(self, user_id):
		return imports.User(self.fosscord,self.s,self.log).get_notes(user_id)

	def set_user_note(self, user_id, note):
		return imports.User(self.fosscord,self.s,self.log).set_user_note(user_id, note)

	def get_rt_cregions(self):
		return imports.User(self.fosscord,self.s,self.log).get_rt_cregions()

	def get_voice_regions(self):
		return imports.User(self.fosscord,self.s,self.log).get_voice_regions()

	'''
	Profile edits
	'''
	# set avatar
	def set_avatar(self,image_path):
		return imports.User(self.fosscord,self.s,self.log).set_avatar(image_path)

	#set profile color
	def set_profile_color(self, color=None):
		return imports.User(self.fosscord,self.s,self.log).set_profile_color(color)

	#set username
	def set_username(self, username): #USER PASSWORD NEEDS TO BE SET BEFORE THIS IS RUN
		return imports.User(self.fosscord,self.s,self.log).set_username(username, password=self.__user_password)

	#set email
	def set_email(self, email): #USER PASSWORD NEEDS TO BE SET BEFORE THIS IS RUN
		return imports.User(self.fosscord,self.s,self.log).set_email(email, password=self.__user_password)

	#set password
	def set_password(self, new_password): #USER PASSWORD NEEDS TO BE SET BEFORE THIS IS RUN
		return imports.User(self.fosscord,self.s,self.log).set_password(new_password, password=self.__user_password)

	#set discriminator
	def set_discriminator(self, discriminator): #USER PASSWORD NEEDS TO BE SET BEFORE THIS IS RUN
		return imports.User(self.fosscord,self.s,self.log).set_discriminator(discriminator, password=self.__user_password)

	#set about me
	def set_about_me(self, bio):
		return imports.User(self.fosscord,self.s,self.log).set_about_me(bio)

	#set banner
	def set_banner(self, image_path):
		return imports.User(self.fosscord,self.s,self.log).set_banner(image_path)

	def disable_account(self, password):
		return imports.User(self.fosscord,self.s,self.log).disable_account(password)

	def delete_account(self, password):
		return imports.User(self.fosscord,self.s,self.log).delete_account(password)

	'''
	User Settings, continued
	'''
	def set_d_mscan_lvl(self, level=1): # 0<=level<=2
		return imports.User(self.fosscord,self.s,self.log).set_d_mscan_lvl(level)

	def allow_d_ms_from_server_members(self, allow=True, disallowed_guild_i_ds=None):
		return imports.User(self.fosscord,self.s,self.log).allow_d_ms_from_server_members(allow, disallowed_guild_i_ds)

	def allow_friend_requests_from(self, types=["everyone", "mutual_friends", "mutual_guilds"]):
		return imports.User(self.fosscord,self.s,self.log).allow_friend_requests_from(types)

	def analytics_consent(self, grant=[], revoke=[]):
		return imports.User(self.fosscord,self.s,self.log).analytics_consent(grant, revoke)

	def allow_screen_reader_tracking(self, allow=True):
		return imports.User(self.fosscord,self.s,self.log).allow_screen_reader_tracking(allow)

	def request_my_data(self):
		return imports.User(self.fosscord,self.s,self.log).request_my_data()

	def get_connected_accounts(self):
		return imports.User(self.fosscord,self.s,self.log).get_connected_accounts()

	def get_connection_url(self, account_type):
		return imports.User(self.fosscord,self.s,self.log).get_connection_url(account_type)

	def enable_connection_display_on_profile(self, account_type, account_username, enable=True):
		return imports.User(self.fosscord,self.s,self.log).enable_connection_display_on_profile(account_type, account_username, enable)

	def enable_connection_display_on_status(self, account_type, account_username, enable=True):
		return imports.User(self.fosscord,self.s,self.log).enable_connection_display_on_status(account_type, account_username, enable)

	def remove_connection(self, account_type, account_username):
		return imports.User(self.fosscord,self.s,self.log).remove_connection(account_type, account_username)

	def get_billing_history(self, limit=20):
		return imports.User(self.fosscord,self.s,self.log).get_billing_history(limit)

	def get_payment_sources(self):
		return imports.User(self.fosscord,self.s,self.log).get_payment_sources()

	def get_billing_subscriptions(self):
		return imports.User(self.fosscord,self.s,self.log).get_billing_subscriptions()

	def get_stripe_client_secret(self):
		return imports.User(self.fosscord,self.s,self.log).get_stripe_client_secret()

	def set_theme(self, theme): #"light" or "dark"
		return imports.User(self.fosscord,self.s,self.log).set_theme(theme)

	def set_message_display(self, CozyOrCompact): #"cozy" or "compact"
		return imports.User(self.fosscord,self.s,self.log).set_message_display(CozyOrCompact)

	def enable_gif_auto_play(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord,self.s,self.log).enable_gif_auto_play(enable)

	def enable_animated_emoji(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord,self.s,self.log).enable_animated_emoji(enable)

	def set_sticker_animation(self, setting): #string, default="always"
		return imports.User(self.fosscord,self.s,self.log).set_sticker_animation(setting)

	def enable_tts(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord,self.s,self.log).enable_tts(enable)

	def enable_linked_image_display(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord,self.s,self.log).enable_linked_image_display(enable)

	def enable_image_display(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord,self.s,self.log).enable_image_display(enable)

	def enable_link_preview(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord,self.s,self.log).enable_link_preview(enable)

	def enable_reaction_rendering(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord,self.s,self.log).enable_reaction_rendering(enable)

	def enable_emoticon_conversion(self, enable=True): #boolean, default=True
		return imports.User(self.fosscord,self.s,self.log).enable_emoticon_conversion(enable)

	def set_af_ktimeout(self, timeout_seconds):
		return imports.User(self.fosscord,self.s,self.log).set_af_ktimeout(timeout_seconds)

	def set_locale(self, locale):
		response = imports.User(self.fosscord,self.s,self.log).set_locale(locale)
		self.locale = locale
		self.s.headers["Accept-Language"] = self.locale
		self.s.cookies["locale"] = self.locale
		return response

	def enable_dev_mode(self, enable=True): #boolean
		return imports.User(self.fosscord,self.s,self.log).enable_dev_mode(enable)

	def activate_application_test_mode(self, application_id):
		return imports.User(self.fosscord,self.s,self.log).activate_application_test_mode(application_id)

	def get_application_data(self, application_id, with_guild=False):
		return imports.User(self.fosscord,self.s,self.log).get_application_data(application_id, with_guild)

	def enable_activity_display(self, enable=True):
		return imports.User(self.fosscord,self.s,self.log).enable_activity_display(enable)

	def set_hypesquad(self, house):
		return imports.User(self.fosscord,self.s,self.log).set_hypesquad(house)

	def leave_hypesquad(self):
		return imports.User(self.fosscord,self.s,self.log).leave_hypesquad()

	def get_build_overrides(self):
		return imports.User(self.fosscord,self.s,self.log).get_build_overrides()

	def enable_source_maps(self, enable=True):
		return imports.User(self.fosscord,self.s,self.log).enable_source_maps()

	def suppress_everyone_pings(self, guild_id, suppress=True):
		return imports.User(self.fosscord,self.s,self.log).suppress_everyone_pings(guild_id, suppress)

	def suppress_role_mentions(self, guild_id, suppress=True):
		return imports.User(self.fosscord,self.s,self.log).suppress_role_mentions(guild_id, suppress)

	def enable_mobile_push_notifications(self, guild_id, enable=True):
		return imports.User(self.fosscord,self.s,self.log).enable_mobile_push_notifications(guild_id, enable)

	def set_channel_notification_overrides(self, guild_id, overrides):
		return imports.User(self.fosscord,self.s,self.log).set_channel_notification_overrides(guild_id, overrides)

	def set_message_notifications(self, guild_id, notifications):
		return imports.User(self.fosscord,self.s,self.log).set_message_notifications(guild_id, notifications)

	def mute_guild(self, guild_id, mute=True, duration=None):
		return imports.User(self.fosscord,self.s,self.log).mute_guild(guild_id, mute, duration)

	def mute_dm(self, DMID, mute=True, duration=None):
		return imports.User(self.fosscord,self.s,self.log).mute_dm(DMID, mute, duration)

	def set_thread_notifications(self, thread_id, notifications):
		return imports.User(self.fosscord,self.s,self.log).set_thread_notifications(thread_id, notifications)

	def get_report_menu(self):
		return imports.User(self.fosscord,self.s,self.log).get_report_menu()

	def report_spam(self, channel_id, message_id, report_type="first_dm", guild_id=None, version="1.0", variant="1", language="en"):
		return imports.User(self.fosscord,self.s,self.log).report_spam(channel_id, message_id, report_type, guild_id, version, variant, language)

	def get_handoff_token(self, key):
		return imports.User(self.fosscord,self.s,self.log).get_handoff_token(key)

	def invite_to_call(self, channel_id, user_ids=None):
		return imports.User(self.fosscord,self.s,self.log).invite_to_call(channel_id, user_ids)

	def decline_call(self, channel_id):
		return imports.User(self.fosscord,self.s,self.log).decline_call(channel_id)

	def logout(self, provider=None, voip_provider=None):
		return imports.User(self.fosscord,self.s,self.log).logout(provider, voip_provider)

	'''
	Guild/Server stuff
	'''
	#get guild info from invite code
	def get_info_from_invite_code(self,invite_code, with_counts=True, with_expiration=True, from_join_guild_nav=False):
		return imports.Guild(self.fosscord,self.s,self.log).get_info_from_invite_code(invite_code, with_counts, with_expiration, from_join_guild_nav)

	#join guild with invite code
	def join_guild(self, invite_code, location="accept invite page", wait=0):
		return imports.Guild(self.fosscord,self.s,self.log).join_guild(invite_code, location, wait)

	#preview/lurk-join guild. Only applies to current (gateway) session
	def preview_guild(self, guild_id, session_id=None):
		return imports.Guild(self.fosscord,self.s,self.log).preview_guild(guild_id, session_id)

	#leave guild
	def leave_guild(self, guild_id, lurking=False):
		return imports.Guild(self.fosscord,self.s,self.log).leave_guild(guild_id, lurking)

	#create invite
	def create_invite(self, channel_id, max_age_seconds=False, max_uses=False, grant_temp_membership=False, check_invite="", target_type=""):
		return imports.Guild(self.fosscord,self.s,self.log).create_invite(channel_id, max_age_seconds, max_uses, grant_temp_membership, check_invite, target_type)

	def delete_invite(self, invite_code):
		return imports.Guild(self.fosscord,self.s,self.log).delete_invite(invite_code)

	def get_guild_invites(self, guild_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_guild_invites(guild_id)

	def get_channelInvites(self, channel_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_channelInvites(channel_id)

	#get all guilds (this is used by the client when going to the developers portal)
	def get_guilds(self, with_counts=True):
		return imports.Guild(self.fosscord,self.s,self.log).get_guilds(with_counts)

	#get guild channels (this is used by the client when going to the server insights page for a guild)
	def get_guild_channels(self, guild_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_guild_channels(guild_id)

	#get discoverable guilds
	def get_discoverable_guilds(self, offset=0, limit=24):
		return imports.Guild(self.fosscord,self.s,self.log).get_discoverable_guilds(offset, limit)

	def get_guild_regions(self, guild_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_guild_regions(guild_id)

	#create a guild
	def create_guild(self, name, icon=None, channels=[], system_channel_id=None, template="2TffvPucqHkN"):
		return imports.Guild(self.fosscord,self.s,self.log).create_guild(name, icon, channels, system_channel_id, template)

	#delete a guild
	def delete_guild(self, guild_id):
		return imports.Guild(self.fosscord,self.s,self.log).delete_guild(guild_id)

	#kick a user
	def kick(self,guild_id,user_id,reason=""):
		return imports.Guild(self.fosscord,self.s,self.log).kick(guild_id,user_id,reason)

	#ban a user
	def ban(self,guild_id,user_id,delete_messagesDays=0,reason=""):
		return imports.Guild(self.fosscord,self.s,self.log).ban(guild_id,user_id,delete_messagesDays,reason)

	#unban a user
	def revoke_ban(self, guild_id, user_id):
		return imports.Guild(self.fosscord,self.s,self.log).revoke_ban(guild_id, user_id)

	#get number of members in each role
	def get_role_member_counts(self, guild_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_role_member_counts(guild_id)

	#get integrations (includes applications aka bots)
	def get_guild_integrations(self, guild_id, include_applications=True):
		return imports.Guild(self.fosscord,self.s,self.log).get_guild_integrations(guild_id, include_applications)

	#get guild templates
	def get_guild_templates(self, guild_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_guild_templates(guild_id)

	#get role member ids
	def get_role_member_i_ds(self, guild_id, role_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_role_member_i_ds(guild_id, role_id)

	#add members to role (add a role to multiple members at the same time)
	def add_members_to_role(self, guild_id, role_id, member_ids):
		return imports.Guild(self.fosscord,self.s,self.log).add_members_to_role(guild_id, role_id, member_ids)

	#set roles of a member
	def set_member_roles(self, guild_id, member_id, role_i_ds):
		return imports.Guild(self.fosscord,self.s,self.log).set_member_roles(guild_id, member_id, role_i_ds)

	def get_member_verification_data(self, guild_id, with_guild=False, invite_code=None):
		return imports.Guild(self.fosscord,self.s,self.log).get_member_verification_data(guild_id, with_guild, invite_code)

	def agree_guild_rules(self, guild_id, form_fields, version="2021-01-05T01:44:32.163000+00:00"):
		return imports.Guild(self.fosscord,self.s,self.log).agree_guild_rules(guild_id, form_fields, version)

	def create_thread(self, channel_id, name, message_id=None, public=True, archive_after='24 hours'):
		return imports.Guild(self.fosscord,self.s,self.log).create_thread(channel_id, name, message_id, public, archive_after)

	def leave_thread(self, thread_id, location="Sidebar Overflow"):
		return imports.Guild(self.fosscord,self.s,self.log).leave_thread(thread_id, location)

	def join_thread(self, thread_id, location="Banner"):
		return imports.Guild(self.fosscord,self.s,self.log).join_thread(thread_id, location)

	def archive_thread(self, thread_id, lock=True):
		return imports.Guild(self.fosscord,self.s,self.log).archive_thread(thread_id, lock)

	def unarchive_thread(self, thread_id, lock=False):
		return imports.Guild(self.fosscord,self.s,self.log).unarchive_thread(thread_id, lock)

	def lookup_school(self, email, allow_multiple_guilds=True, use_verification_code=True):
		return imports.Guild(self.fosscord,self.s,self.log).lookup_school(email, allow_multiple_guilds, use_verification_code)

	def school_hub_waitlist_signup(self, email, school):
		return imports.Guild(self.fosscord,self.s,self.log).school_hub_waitlist_signup(email, school)

	def school_hub_signup(self, email, hub_id):
		return imports.Guild(self.fosscord,self.s,self.log).school_hub_signup(email, hub_id)

	def verify_school_hub_signup(self, hub_id, email, code):
		return imports.Guild(self.fosscord,self.s,self.log).verify_school_hub_signup(hub_id, email, code)

	def get_school_hub_guilds(self, hub_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_school_hub_guilds(hub_id)

	def get_school_hub_directory_counts(self, hub_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_school_hub_directory_counts(hub_id)

	def join_guild_from_school_hub(self, hub_id, guild_id):
		return imports.Guild(self.fosscord,self.s,self.log).join_guild_from_school_hub(hub_id, guild_id)

	def search_school_hub(self, hub_id, query):
		return imports.Guild(self.fosscord,self.s,self.log).search_school_hub(hub_id, query)

	def get_my_school_hub_guilds(self, hub_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_my_school_hub_guilds(hub_id)

	def set_school_hub_guild_details(self, hub_id, guild_id, description, directory_id):
		return imports.Guild(self.fosscord,self.s,self.log).set_school_hub_guild_details(hub_id, guild_id, description, directory_id)

	def get_live_stages(self, extra=False):
		return imports.Guild(self.fosscord,self.s,self.log).get_live_stages(extra)

	def get_channel(self, channel_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_channel(channel_id)

	def get_guild_activities_config(self, guild_id):
		return imports.Guild(self.fosscord,self.s,self.log).get_guild_activities_config(guild_id)

	'''
	"Science", aka fosscord's tracking endpoint (https://luna.gitlab.io/fosscord-unofficial-docs/science.html - "fosscord argues that they need to collect the data in the case the User allows the usage of the data later on. Which in [luna's] opinion is complete bullshit. Have a good day.")
	'''
	def init_science(self):
		try:
			#get analytics token
			response = imports.User(self.fosscord,self.s,self.log).info(with_analytics_token=True)
			if response.status_code == 401:
				raise
			self.user_data = response.json() #this is essentially the connection test. We need it cause we can get important data without connecting to the gateway.
		except:
			self.user_data = {"analytics_token": None, "id": "0"} #if token invalid
		#initialize Science object
		self.Science = imports.Science(self.fosscord, self.s, self.log, self.user_data.get("analytics_token", ""), self.user_data["id"])

	def science(self, events): #the real prep for science events happens down here, and only once for each client obj
		if self.Science == "":
			self.init_science()
		return self.Science.science(events)

	def calculate_client_uuid(self, event_num="default", user_id="default", increment=True):
		if self.Science == "":
			self.init_science()
		return self.Science.UUIDobj.calculate(event_num, user_id, increment)

	def refresh_client_uuid(self, reset_event_num=True):
		if self.Science == "":
			self.init_science()
		return self.Science.UUIDobj.refresh(reset_event_num)

	def parse_client_uuid(self, client_uuid):
		if self.Science == "":
			self.Science = imports.Science(self.fosscord, self.s, self.log, None, "0", "") #no sequential data needed for parsing
			result = self.Science.UUIDobj.parse(client_uuid)
			self.Science = "" #reset
			return result
		else:
			return self.Science.UUIDobj.parse(client_uuid)
