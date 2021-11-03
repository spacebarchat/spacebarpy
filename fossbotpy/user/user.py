import base64
import datetime
from ..requestsender import Wrapper
from ..utils.contextproperties import ContextProperties
from ..utils.color import Color
from ..utils.snowflake import Snowflake

class User(object):
	__slots__ = ['fosscord', 's', 'log']
	def __init__(self, fosscord, s, log): #s is the requests session object
		self.fosscord = fosscord
		self.s = s
		self.log = log

	def get_relationships(self):
		url = self.fosscord+"users/@me/relationships"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_mutual_friends(self, user_id):
		url = self.fosscord+"users/"+user_id+"/relationships"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def request_friend(self, user):
		if "#" in user:
			url = self.fosscord+"users/@me/relationships"
			body = {"username": user.split("#")[0], "discriminator": int(user.split("#")[1])}
			return Wrapper.send_request(self.s, 'post', url, body, header_modifications={"update":{"X-Context-Properties": ContextProperties.get("add friend")}}, log=self.log)
		else:
			url = self.fosscord+"users/@me/relationships/"+user
			body = {}
			return Wrapper.send_request(self.s, 'put', url, body, header_modifications={"update":{"X-Context-Properties":ContextProperties.get("context menu")}}, log=self.log)

	def accept_friend(self, user_id, location):
		url = self.fosscord+"users/@me/relationships/"+user_id
		body = {}
		return Wrapper.send_request(self.s, 'put', url, body, header_modifications={"update":{"X-Context-Properties":ContextProperties.get(location)}}, log=self.log)

	def remove_relationship(self, user_id, location): #for removing friends, unblocking people
		url = self.fosscord+"users/@me/relationships/"+user_id
		return Wrapper.send_request(self.s, 'delete', url, header_modifications={"update":{"X-Context-Properties":ContextProperties.get(location)}}, log=self.log)

	def block_user(self, user_id, location):
		url = self.fosscord+"users/@me/relationships/"+user_id
		body = {"type": 2}
		return Wrapper.send_request(self.s, 'put', url, body, header_modifications={"update":{"X-Context-Properties":ContextProperties.get(location)}}, log=self.log)

	def get_profile(self, user_id, with_mutual_guilds):
		url = self.fosscord+"users/"+user_id+"/profile"
		if with_mutual_guilds != None:
			url += "?with_mutual_guilds="+repr(with_mutual_guilds).lower()
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def info(self, with_analytics_token): #simple. bot.info() for own user data
		url = self.fosscord+"users/@me"
		if with_analytics_token != None:
			url += "?with_analytics_token="+repr(with_analytics_token).lower()
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_user_affinities(self):
		url = self.fosscord+"users/@me/affinities/users"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#guild affinities with respect to current user, decided to organize this wrap in here b/c that's how the api is organized
	def get_guild_affinities(self):
		url = self.fosscord+"users/@me/affinities/guilds"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_mentions(self, limit, role_mentions, everyone_mentions):
		role_mentions = str(role_mentions).lower()
		everyone_mentions = str(everyone_mentions).lower()
		url = self.fosscord+"users/@me/mentions?limit="+str(limit)+"&roles="+role_mentions+"&everyone="+everyone_mentions
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def remove_mention_from_inbox(self, message_id):
		url = self.fosscord+"users/@me/mentions/"+message_id
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def get_my_stickers(self):
		url = self.fosscord+"users/@me/sticker-packs"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_notes(self, user_id):
		url = self.fosscord+"users/@me/notes/"+user_id
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def set_user_note(self, user_id, note):
		url = self.fosscord+'users/@me/notes/'+user_id
		body = {"note": note}
		return Wrapper.send_request(self.s, 'put', url, body, log=self.log)

	def get_rt_cregions(self):
		url = "https://latency.fosscord.media/rtc"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_voice_regions(self):
		url = self.fosscord+'voice/regions'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def set_status_helper(self, status, timeout=None): #Dont run this function by itself; status options are: online, idle, dnd, invisible
		url = self.fosscord+"users/@me/settings"
		if status in ("online", "idle", "dnd", "invisible"):
			body = {"status": status}
		return Wrapper.send_request(self.s, 'patch', url, body, timeout=timeout, log=self.log)

	def set_custom_status_helper(self, customstatus, emoji, expires_at, timeout=None): #Dont run this function by itself
		url = self.fosscord+"users/@me/settings"
		body = {"custom_status": {}}
		if customstatus not in (None, ""):
			body["custom_status"]["text"] = customstatus
		if emoji != None:
			if ":" in emoji:
				name, ID = emoji.split(":")
				body["custom_status"]["emoji_name"] = name
				body["custom_status"]["emoji_id"] = ID
			else:
				body["custom_status"]["emoji_name"] = emoji
		if expires_at != None: #assume unix timestamp
			expires_at = float(expires_at)
			dt = datetime.datetime.fromtimestamp(expires_at)
			timestamp = dt.isoformat("T")+"Z"
			body["custom_status"]["expires_at"] = timestamp
		if body["custom_status"] == {}:
			body["custom_status"] = None
		return Wrapper.send_request(self.s, 'patch', url, body, timeout=timeout, log=self.log)

	# USER SETTINGS
	'''
	My Account
	'''	
	def set_avatar(self, image_path): #local image, set to None to delete avatar
		url = self.fosscord+"users/@me"
		with open(image_path, "rb") as image:
			encoded_image = base64.b64encode(image.read()).decode('utf-8')
		body = {"avatar":"data:image/png;base64,"+encoded_image}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_profile_color(self, color):
		url = self.fosscord+"users/@me"
		body = {"accent_color": Color.get(color)}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_username(self, username, discriminator, password):
		url = self.fosscord+"users/@me"
		body = {"username": username, "password": password, "discriminator":discriminator}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_email(self, email, password):
		url = self.fosscord+"users/@me"
		body = {"email": email, "password": password}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_password(self, new_password, password):
		url = self.fosscord+"users/@me"
		body = {"password": password, "new_password": new_password}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	#as of right now, you need to be in the beta program for this to work
	def set_about_me(self, bio):
		url = self.fosscord+"users/@me"
		body = {"bio": bio}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	#as of right now, you need to be in the beta program for this to work
	def set_banner(self, image_path):
		url = self.fosscord+"users/@me"
		with open(image_path, "rb") as image:
			encoded_image = base64.b64encode(image.read()).decode('utf-8')
		body = {"banner":"data:image/png;base64,"+encoded_image}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def disable_account(self, password):
		url = self.fosscord+"users/@me/disable"
		body = {"password": password}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	def delete_account(self, password):
		url = self.fosscord+"users/@me/delete"
		body = {"password": password}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	'''
	Privacy & Safety
	'''
	def set_d_mscan_lvl(self, level):
		url = self.fosscord+"users/@me/settings"
		body = {"explicit_content_filter": int(level)}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def allow_d_ms_from_server_members(self, allow, disallowed_guild_i_ds):
		url = self.fosscord+"users/@me/settings"
		body = {"restricted_guilds":disallowed_guild_i_ds, "default_guilds_restricted":not allow}
		if not disallowed_guild_i_ds: #if False or None
			body.pop("restricted_guilds")
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def allow_friend_requests_from(self, types):
		url = self.fosscord+"users/@me/settings"
		body = {"friend_source_flags": {"all": True, "mutual_friends": True, "mutual_guilds": True}}
		types = [i.lower().strip() for i in types]
		if "everyone" not in types:
			body["friend_source_flags"]["all"] = False
		if "mutual_friends" not in types:
			body["friend_source_flags"]["mutual_friends"] = False
		if "mutual_guilds" not in types:
			body["friend_source_flags"]["mutual_guilds"] = False
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def analytics_consent(self, grant, revoke): #personalization, usage_statistics
		url = self.fosscord+"users/@me/consent"
		body = {"grant":grant,"revoke":revoke}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	def allow_screen_reader_tracking(self, allow): #more fosscord tracking stuff
		url = self.fosscord+"users/@me/settings"
		body = {"allow_accessibility_detection": allow}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def request_my_data(self):
		url = self.fosscord+"users/@me/harvest"
		return Wrapper.send_request(self.s, 'post', url, log=self.log)

	'''
	Connections
	'''
	def get_connected_accounts(self):
		url = self.fosscord+"users/@me/connections"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_connection_url(self, account_type):
		url = self.fosscord+"connections/"+account_type+"/authorize"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def enable_connection_display_on_profile(self, account_type, account_username, enable):
		url = self.fosscord+"users/@me/connections/"+account_type+"/"+account_username
		body = {"visibility": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_connection_display_on_status(self, account_type, account_username, enable):
		url = self.fosscord+"users/@me/connections/"+account_type+"/"+account_username
		body = {"show_activity": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def remove_connection(self, account_type, account_username):
		url = self.fosscord+"users/@me/connections/"+account_type+"/"+account_username
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	# BILLING SETTINGS
	'''
	Billing
	'''
	def get_billing_history(self, limit):
		url = self.fosscord+"users/@me/billing/payments?limit="+str(limit)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_payment_sources(self):
		url = self.fosscord+"users/@me/billing/payment-sources"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_billing_subscriptions(self):
		url = self.fosscord+"users/@me/billing/subscriptions"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_stripe_client_secret(self): #for adding new payment methods. Stripe api wraps are not included because discum is just a fosscord api wrapper.
		url = self.fosscord+"users/@me/billing/stripe/setup-intents"
		return Wrapper.send_request(self.s, 'post', url, log=self.log)

	# APP SETTINGS
	'''
	Appearance
	'''
	def set_theme(self, theme):
		url = self.fosscord+"users/@me/settings"
		body = {"theme": theme.lower()}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_message_display(self, CozyOrCompact):
		url = self.fosscord+"users/@me/settings"
		if CozyOrCompact.lower() == "compact":
			body = {"message_display_compact": True}
		else:
			body = {"message_display_compact": False}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Accessibility
	'''
	def enable_gif_auto_play(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"gif_auto_play": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_animated_emoji(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"animate_emoji": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_sticker_animation(self, setting):
		url = self.fosscord+"users/@me/settings"
		if setting.lower() == "always":
			body = {"animate_stickers": 0}
		elif setting.lower() == "interaction":
			body = {"animate_stickers": 1}
		elif setting.lower() == "never":
			body = {"animate_stickers": 2}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_tts(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"enable_tts_command": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Text & Images
	'''

	def enable_linked_image_display(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"inline_embed_media": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_image_display(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"inline_attachment_media": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_link_preview(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"render_embeds": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_reaction_rendering(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"render_reactions": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_emoticon_conversion(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"convert_emoticons": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Notifications
	'''
	def set_af_ktimeout(self, timeout_seconds):
		url = self.fosscord+"users/@me/settings"
		body = {"afk_timeout": timeout_seconds}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Language
	'''
	def set_locale(self, locale):
		url = self.fosscord+"users/@me/settings"
		body = {"locale": locale}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Advanced
	'''
	def enable_dev_mode(self, enable):
		url = self.fosscord+"users/@me/settings"
		body = {"developer_mode": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def activate_application_test_mode(self, application_id):
		url = self.fosscord+"applications/"+application_id+"/skus"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_application_data(self, application_id, with_guild):
		url = self.fosscord+"applications/"+application_id+"/public?with_guild="+str(with_guild).lower()
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	# ACTIVITY SETTINGS
	'''
	Activity Status
	'''
	def enable_activity_display(self, enable, timeout=None):
		url = self.fosscord+"users/@me/settings"
		body = {"show_current_game": enable}
		Wrapper.send_request(self.s, 'patch', url, body, timeout=timeout, log=self.log)

	# OTHER SETTINGS
	'''
	HypeSquad
	'''
	def set_hypesquad(self, house):
		url = self.fosscord+"hypesquad/online"
		if house.lower() == "bravery":
			body = {"house_id": 1}
		elif house.lower() == "brilliance":
			body = {"house_id": 2}
		elif house.lower() == "balance":
			body = {"house_id": 3}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	def leave_hypesquad(self):
		url = self.fosscord+"hypesquad/online"
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	'''
	Developer Options
	'''
	def get_build_overrides(self):
		url = "https://fosscord.com/__development/build_overrides"
		return Wrapper.send_request(self.s, 'get', url, header_modifications={"remove":["Authorization", "X-Super-Properties", "X-Fingerprint"]}, log=self.log)

	def enable_source_maps(self, enable):
		url = "https://fosscord.com/__development/source_maps"
		if enable:
			return Wrapper.send_request(self.s, 'put', url, header_modifications={"remove":["X-Super-Properties", "X-Fingerprint"]}, log=self.log)
		else:
			return Wrapper.send_request(self.s, 'delete', url, header_modifications={"remove":["X-Super-Properties", "X-Fingerprint"]}, log=self.log)

	'''
	Notification Settings
	'''
	@staticmethod
	def index(input_list, search_item): #only used for notification settings, returning -1 doesn't make sense in this context
		try:
			return input_list.index(search_item)
		except ValueError:
			return 0

	def suppress_everyone_pings(self, guild_id, suppress):
		url = self.fosscord+"users/@me/guilds/"+str(guild_id)+"/settings"
		body = {"suppress_everyone": suppress}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def suppress_role_mentions(self, guild_id, suppress):
		url = self.fosscord+"users/@me/guilds/"+str(guild_id)+"/settings"
		body = {"suppress_roles": suppress}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_mobile_push_notifications(self, guild_id, enable):
		url = self.fosscord+"users/@me/guilds/"+str(guild_id)+"/settings"
		body = {"mobile_push": enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_channel_notification_overrides(self, guild_id, overrides):
		url = self.fosscord+"users/@me/guilds/"+str(guild_id)+"/settings"
		if type(overrides[0]) in (tuple, list):
			msg_notification_types = ["all messages", "only mentions", "nothing"]
			overrides = {str(channel):{"message_notifications": self.index(msg_notification_types, msg.lower()), "muted":muted} for channel,msg,muted in overrides}
		body = {"channel_overrides": overrides}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_message_notifications(self, guild_id, notifications):
		url = self.fosscord+"users/@me/guilds/"+str(guild_id)+"/settings"
		msg_notification_types = ["all messages", "only mentions", "nothing"]
		body = {"message_notifications": self.index(msg_notification_types, notifications.lower())}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def mute_guild(self, guild_id, mute, duration):
		url = self.fosscord+"users/@me/guilds/"+str(guild_id)+"/settings"
		body = {"muted": mute}
		if mute and duration is not None:
			end_time = (datetime.datetime.utcnow()+datetime.timedelta(minutes=duration)).isoformat()[:-3]+'Z' #https://stackoverflow.com/a/54272238/14776493
			body["mute_config"] = {"selected_time_window":duration, "end_time":end_time}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def mute_dm(self, DMID, mute, duration):
		url = self.fosscord+"users/@me/guilds/%40me/settings"
		data = {"muted": mute}
		if mute:
			if duration is not None:
				end_time = (datetime.datetime.utcnow()+datetime.timedelta(minutes=duration)).isoformat()[:-3]+'Z'
				data["mute_config"] = {"selected_time_window":duration, "end_time":end_time}
			else:
				data["mute_config"] = {"selected_time_window":-1, "end_time":None}
		body = {"channel_overrides":{str(DMID):data}}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_thread_notifications(self, thread_id, notifications):
		url = self.fosscord+"channels/"+thread_id+"/thread-members/@me/settings"
		thread_notification_types = ["all messages", "only mentions", "nothing"]
		flags = 1<<(self.index(thread_notification_types, notifications.lower())+1)
		body = {"flags": flags}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def get_report_menu(self):
		url = self.fosscord+'reporting/menu/first_dm'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def report_spam(self, channel_id, message_id, report_type, guild_id, version, variant, language):
		url = self.fosscord+'reporting/'+report_type
		body = {
			"id": Snowflake.get_snowflake(),
			"version": version,
			"variant": variant,
			"language": language,
			"breadcrumbs": [7],
			"elements": {},
			"name": report_type,
			"channel_id": channel_id,
			"message_id": message_id,
		}
		if report_type in ('guild_directory_entry', 'stage_channel', 'guild'):
			body["guild_id"] = guild_id
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	def get_handoff_token(self, key):
		url = self.fosscord+'auth/handoff'
		body = {"key": key}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	def invite_to_call(self, channel_id, user_ids):
		url = self.fosscord+'channels/'+channel_id+'/call/ring'
		body = {"recipients": user_ids}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	def decline_call(self, channel_id):
		url = self.fosscord+'channels/'+channel_id+'/call/stop-ringing'
		body = {}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	'''
	Logout
	'''
	def logout(self, provider, voip_provider):
		url = self.fosscord+"auth/logout"
		body = {"provider": provider, "voip_provider": voip_provider}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

