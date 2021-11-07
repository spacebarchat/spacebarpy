import base64
import datetime

from ..requestsender import Wrapper
from ..utils.contextproperties import ContextProperties
from ..utils.color import Color
from ..utils.snowflake import Snowflake

class User(object):
	__slots__ = ['fosscord', 's', 'log']
	def __init__(self, fosscord, s, log):
		self.fosscord = fosscord
		self.s = s
		self.log = log

	def get_relationships(self):
		url = '{}users/@me/relationships'.format(self.fosscord)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#currently does not work on fosscord
	def get_mutual_friends(self, user_id):
		u = +'{}users/{}/relationships'
		url = u.format(self.fosscord, user_id)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def request_friend(self, user):
		if '#' in user:
			url = '{}users/@me/relationships'.format(self.fosscord)
			body = {'username': user.split('#')[0], 'discriminator': int(user.split('#')[1])}
			header_mods = {'update':{'X-Context-Properties': ContextProperties.get('add friend')}}
			return Wrapper.send_request(self.s, 'post', url, body, header_modifications=header_mods, log=self.log)
		else:
			u = '{}users/@me/relationships/{}'
			url = u.format(self.fosscord, user)
			body = {}
			header_mods = {'update':{'X-Context-Properties':ContextProperties.get('context menu')}}
			return Wrapper.send_request(self.s, 'put', url, body, header_modifications=header_mods, log=self.log)

	def accept_friend(self, user_id, location):
		u = '{}users/@me/relationships/{}'
		url = u.format(self.fosscord, user_id)
		body = {}
		header_mods = {'update':{'X-Context-Properties':ContextProperties.get(location)}}
		return Wrapper.send_request(self.s, 'put', url, body, header_modifications=header_mods, log=self.log)

	def remove_relationship(self, user_id, location):
		u = '{}users/@me/relationships/{}'
		url = u.format(self.fosscord, user_id)
		header_mods = {'update':{'X-Context-Properties':ContextProperties.get(location)}}
		return Wrapper.send_request(self.s, 'delete', url, header_modifications=header_mods, log=self.log)

	def block_user(self, user_id, location):
		u = '{}users/@me/relationships/{}'
		url = u.format(self.fosscord, user_id)
		body = {'type': 2}
		header_mods = {'update':{'X-Context-Properties':ContextProperties.get(location)}}
		return Wrapper.send_request(self.s, 'put', url, body, header_modifications=header_mods, log=self.log)

	def get_profile(self, user_id, with_mutual_guilds):
		u = '{}users/{}/profile'
		url = u.format(self.fosscord, user_id)
		if with_mutual_guilds not in (None, False):
			url += '?with_mutual_guilds=true'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#simple. bot.info() for own user data
	def info(self):
		url = '{}users/@me'.format(self.fosscord)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_user_affinities(self):
		url = '{}users/@me/affinities/users'.format(self.fosscord)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#guild affinities with respect to current user
	def get_guild_affinities(self):
		url = '{}users/@me/affinities/guilds'.format(self.fosscord)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_voice_regions(self):
		url = self.fosscord+'voice/regions'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def set_status_helper(self, status, timeout=None): #Dont run this function by itself; status options are: online, idle, dnd, invisible
		url = self.fosscord+'users/@me/settings'
		if status in ('online', 'idle', 'dnd', 'invisible'):
			body = {'status': status}
		return Wrapper.send_request(self.s, 'patch', url, body, timeout=timeout, log=self.log)

	def set_custom_status_helper(self, customstatus, emoji, expires_at, timeout=None): #Dont run this function by itself
		url = self.fosscord+'users/@me/settings'
		body = {'custom_status': {}}
		if customstatus not in (None, ''):
			body['custom_status']['text'] = customstatus
		if emoji != None:
			if ':' in emoji:
				name, ID = emoji.split(':')
				body['custom_status']['emoji_name'] = name
				body['custom_status']['emoji_id'] = ID
			else:
				body['custom_status']['emoji_name'] = emoji
		if expires_at != None: #assume unix timestamp
			expires_at = float(expires_at)
			dt = datetime.datetime.fromtimestamp(expires_at)
			timestamp = dt.isoformat('T')+'Z'
			body['custom_status']['expires_at'] = timestamp
		if body['custom_status'] == {}:
			body['custom_status'] = None
		return Wrapper.send_request(self.s, 'patch', url, body, timeout=timeout, log=self.log)

	# USER SETTINGS
	'''
	My Account
	'''	
	def set_avatar(self, image_path): #local image, set to None to delete avatar
		url = self.fosscord+'users/@me'
		with open(image_path, 'rb') as image:
			encoded_image = base64.b64encode(image.read()).decode('utf-8')
		body = {'avatar':'data:image/png;base64,'+encoded_image}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_profile_color(self, color):
		url = self.fosscord+'users/@me'
		body = {'accent_color': Color.get(color)}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_username(self, name, discriminator, password):
		url = self.fosscord+'users/@me'
		body = {'username': name, 'password': password, 'discriminator':discriminator}
		if not name:
			body.pop('username')
		if not discriminator:
			body.pop('discriminator')
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_email(self, email, password):
		url = self.fosscord+'users/@me'
		body = {'email': email, 'password': password}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_password(self, new_password, password):
		url = self.fosscord+'users/@me'
		body = {'password': password, 'new_password': new_password}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_about_me(self, bio):
		url = self.fosscord+'users/@me'
		body = {'bio': bio}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_banner(self, image_path):
		url = self.fosscord+'users/@me'
		with open(image_path, 'rb') as image:
			encoded_image = base64.b64encode(image.read()).decode('utf-8')
		body = {'banner':'data:image/png;base64,'+encoded_image}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def disable_account(self, password):
		url = self.fosscord+'users/@me/disable'
		body = {'password': password}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	def delete_account(self, password):
		url = self.fosscord+'users/@me/delete'
		body = {'password': password}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	'''
	Privacy & Safety
	'''
	def set_dm_scan_lvl(self, level):
		url = self.fosscord+'users/@me/settings'
		body = {'explicit_content_filter': int(level)}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def allow_dms_from_guild_members(self, allow, disallowed_guild_ids):
		url = self.fosscord+'users/@me/settings'
		body = {'restricted_guilds':disallowed_guild_ids, 'default_guilds_restricted':not allow}
		if not disallowed_guild_ids: #if False or None
			body.pop('restricted_guilds')
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def allow_friend_requests_from(self, types):
		url = self.fosscord+'users/@me/settings'
		body = {'friend_source_flags': {'all': True, 'mutual_friends': True, 'mutual_guilds': True}}
		types = [i.lower().strip() for i in types]
		if 'everyone' not in types:
			body['friend_source_flags']['all'] = False
		if 'mutual_friends' not in types:
			body['friend_source_flags']['mutual_friends'] = False
		if 'mutual_guilds' not in types:
			body['friend_source_flags']['mutual_guilds'] = False
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def allow_screen_reader_tracking(self, allow): #more fosscord tracking stuff
		url = self.fosscord+'users/@me/settings'
		body = {'allow_accessibility_detection': allow}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Connections
	'''
	def get_connected_accounts(self):
		url = self.fosscord+'users/@me/connections'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	# BILLING SETTINGS
	'''
	Billing
	'''
	def get_payment_sources(self):
		url = self.fosscord+'users/@me/billing/payment-sources'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_billing_subscriptions(self):
		url = self.fosscord+'users/@me/billing/subscriptions'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	# APP SETTINGS
	'''
	Appearance
	'''
	def set_theme(self, theme):
		url = self.fosscord+'users/@me/settings'
		body = {'theme': theme.lower()}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_message_display(self, cozy_or_compact):
		url = self.fosscord+'users/@me/settings'
		if cozy_or_compact.lower() == 'compact':
			body = {'message_display_compact': True}
		else:
			body = {'message_display_compact': False}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Accessibility
	'''
	def enable_gif_auto_play(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'gif_auto_play': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_animated_emoji(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'animate_emoji': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_sticker_animation(self, setting):
		url = self.fosscord+'users/@me/settings'
		if setting.lower() == 'always':
			body = {'animate_stickers': 0}
		elif setting.lower() == 'interaction':
			body = {'animate_stickers': 1}
		elif setting.lower() == 'never':
			body = {'animate_stickers': 2}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_tts(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'enable_tts_command': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Text & Images
	'''

	def enable_linked_image_display(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'inline_embed_media': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_image_display(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'inline_attachment_media': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_link_preview(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'render_embeds': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_reaction_rendering(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'render_reactions': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def enable_emoticon_conversion(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'convert_emoticons': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Notifications
	'''
	def set_afk_timeout(self, timeout_seconds):
		url = self.fosscord+'users/@me/settings'
		body = {'afk_timeout': timeout_seconds}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Language
	'''
	def set_locale(self, locale):
		url = self.fosscord+'users/@me/settings'
		body = {'locale': locale}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	Advanced
	'''
	def enable_dev_mode(self, enable):
		url = self.fosscord+'users/@me/settings'
		body = {'developer_mode': enable}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	# ACTIVITY SETTINGS
	'''
	Activity Status
	'''
	def enable_activity_display(self, enable, timeout=None):
		url = self.fosscord+'users/@me/settings'
		body = {'show_current_game': enable}
		Wrapper.send_request(self.s, 'patch', url, body, timeout=timeout, log=self.log)

	# OTHER SETTINGS

	'''
	Developer Options
	'''
	def enable_source_maps(self, enable):
		url = 'https://fosscord.com/__development/source_maps'
		if enable:
			return Wrapper.send_request(self.s, 'put', url, header_modifications={'remove':['X-Super-Properties', 'X-Fingerprint']}, log=self.log)
		else:
			return Wrapper.send_request(self.s, 'delete', url, header_modifications={'remove':['X-Super-Properties', 'X-Fingerprint']}, log=self.log)

