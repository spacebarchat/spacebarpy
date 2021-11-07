from ..requestsender import Wrapper
from ..utils.permissions import PERMS, Permissions
from ..utils.contextproperties import ContextProperties

import time
import base64

try:
	from urllib.parse import quote
except ImportError:
	from urllib import quote

class Guild(object):
	__slots__ = ['fosscord', 's', 'log']
	def __init__(self, fosscord, s, log): #s is the requests session object
		self.fosscord = fosscord
		self.s = s
		self.log = log

	'''
	invite codes / server info
	'''
	#get guild info from invite code
	def get_invite(self, invite_code, with_counts, with_expiration, from_join_guild_nav):
		u = '{}invites/{}'
		url = u.format(self.fosscord, invite_code)
		if (with_counts!=None or with_expiration!=None or from_join_guild_nav):
			url += '?'
			data = {}
			if from_join_guild_nav:
				data['inputValue'] = invite_code
			if with_counts != None:
				data['with_counts'] = with_counts
			if with_expiration != None:
				data['with_expiration'] = with_expiration
			url += '&'.join( '%s=%s' % (k, quote(repr(data[k]).lower())) for k in data)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#just the join guild endpoint, default location mimics joining a guild from the ([+]Add a Server) button
	def join_guild_raw(self, invite_code, guild_id=None, channel_id=None, channel_type=None, location='join guild'):
		u = '{}invites/{}'
		url = u.format(self.fosscord, invite_code)
		if location in ('accept invite page', 'join guild'):
			header_mods = {'update':{'X-Context-Properties':ContextProperties.get(location, guild_id=guild_id, channel_id=channel_id, channel_type=channel_type)}}
			return Wrapper.send_request(self.s, 'post', url, {}, header_modifications=header_mods, log=self.log)
		elif location == 'markdown':
			header_mods = {'update':{'X-Context-Properties':ContextProperties.get('markdown')}}
			return Wrapper.send_request(self.s, 'post', url, {}, header_modifications=header_mods, log=self.log)

	def join_guild(self, invite_code, location, wait):
		location = location.lower()
		if location in ("accept invite page", "join guild"):
			guild_data = self.get_invite(
				invite_code,
				with_counts=True,
				with_expiration=True,
				from_join_guild_nav=(location == "join guild")
			).json()
			if wait: time.sleep(wait)
			try:
				return self.join_guild_raw(
					invite_code,
					guild_data["guild"]["id"],
					guild_data["channel"]["id"],
					guild_data["channel"]["type"],
					location
				)
			except:
				return guild_data
		elif location == "markdown":
			return self.join_guild_raw(invite_code, location="markdown")

	def preview_guild(self, guild_id, session_id):
		u = '{}guilds/{}/members/@me?lurker=true'
		url = u.format(self.fosscord, guild_id)
		if session_id != None:
			url += '&session_id={}'.format(session_id)
		return Wrapper.send_request(self.s, 'put', url, header_modifications={'update':{'X-Context-Properties':'e30='}}, log=self.log)

	def leave_guild(self, guild_id, lurking):
		u = '{}users/@me/guilds/{}'
		url = u.format(self.fosscord, guild_id)
		body = {'lurking': lurking}
		return Wrapper.send_request(self.s, 'delete', url, body, log=self.log)

	def create_invite(self, channel_id, max_age_seconds, max_uses, grant_temp_membership, check_invite, target_type): #has to be a channel thats in a guild. also check_invite and target_type are basically useless.
		u = '{}channels/{}/invites'
		url = u.format(self.fosscord, channel_id)
		if max_age_seconds == False:
			max_age_seconds = 0
		if max_uses == False:
			max_uses = 0
		body = {
			"max_age": max_age_seconds,
			"max_uses": max_uses,
			"temporary": grant_temp_membership,
		}
		if check_invite != '':
			body['validate'] = check_invite
		if target_type != '':
			body['target_type'] = target_type
		header_mods = {'update':{'X-Context-Properties':ContextProperties.get('guild header')}}
		return Wrapper.send_request(self.s, 'post', url, body, header_modifications=header_mods, log=self.log)

	def delete_invite(self, invite_code):
		u = '{}invites/{}'
		url = u.format(self.fosscord, invite_code)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def get_guild_invites(self, guild_id):
		u = '{}guilds/{}/invites'
		url = u.format(self.fosscord, guild_id)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_channel_invites(self, channel_id):
		u = '{}channels/{}/invites'
		url = u.format(self.fosscord, channel_id)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_guilds(self, with_counts):
		url = '{}users/@me/guilds'.format(self.fosscord)
		if with_counts != None:
			url += '?with_counts={}'.format(repr(with_counts).lower())
		header_mods = {'update':{'X-Track':self.s.headers.get('X-Super-Properties')}, 'remove':['X-Super-Properties']}
		return Wrapper.send_request(self.s, 'get', url, header_modifications=header_mods, log=self.log)

	def get_guild_channels(self, guild_id):
		u = '{}guilds/{}/channels'
		url = u.format(self.fosscord, guild_id)
		header_mods = {'update':{'X-Track':self.s.headers.get('X-Super-Properties')}, 'remove':['X-Super-Properties']}
		return Wrapper.send_request(self.s, 'get', url, header_modifications=header_mods, log=self.log)

	def get_discoverable_guilds(self, offset, limit):
		u = '{}discoverable-guilds?offset={}&limit={}'
		url = u.format(self.fosscord, offset, limit)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_guild_regions(self, guild_id):
		u = '{}guilds/{}/regions'
		url = u.format(self.fosscord, guild_id)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	'''
	server moderation and management
	'''
	#create a guild
	def create_guild(self, name, icon, channels, system_channel_id, template):
		url = '{}guilds'.format(self.fosscord)
		body = {
			"name": name,
			"icon": icon,
			"channels": channels,
			"system_channel_id": system_channel_id,
			"guild_template_code": template,
		}
		if icon != None:
			with open(icon, 'rb') as image:
				encoded_image = base64.b64encode(image.read()).decode('utf-8')
				body['icon'] = 'data:image/png;base64,'+encoded_image
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	#delete a guild (assuming you are the owner)
	def delete_guild(self, guild_id):
		url = self.fosscord+'guilds/%s/delete' % (guild_id)
		body = {}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	#kick a user
	def kick(self, guild_id, user_id, reason):
		u = '{}guilds/{}/members/{}'
		url = u.format(self.fosscord, guild_id, user_id)
		header_mods = {}
		if reason:
			url += '?reason={}'.format(quote(reason))
			header_mods = {'update':{'X-Audit-Log-Reason':reason}}
		return Wrapper.send_request(self.s, 'delete', url, header_modifications=header_mods, log=self.log)

	#ban a user
	def ban(self, guild_id, user_id, delete_messagesDays, reason):
		u = '{}guilds/{}/bans/{}'
		url = u.format(self.fosscord, guild_id, user_id)
		body = {'delete_message_days': str(delete_messagesDays), 'reason': reason}
		header_mods = {'update':{'X-Audit-Log-Reason':reason}} if reason=='' else {}
		return Wrapper.send_request(self.s, 'put', url, body, header_modifications=header_mods, log=self.log)

	def revoke_ban(self, guild_id, user_id):
		url = self.fosscord+'guilds/'+guild_id+'/bans/'+user_id
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	#lookup a user in a guild. thx Echocage for finding this api endpoint
	'''
	removed as this is a bot-only request. Use bot.gateway.check_guild_members instead.

	def getGuildMember(self, guild_id, user_id):
		url = self.fosscord+'guilds/%s/members/%s' % (guild_id, user_id)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)
	'''

	def get_guild_templates(self, guild_id):
		url = self.fosscord+'guilds/'+guild_id+'/templates'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_role_member_ids(self, guild_id, role_id):
		url = self.fosscord+'guilds/'+guild_id+'/roles/'+role_id+'/member-ids'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def set_member_roles(self, guild_id, member_id, role_ids):
		if isinstance(role_ids, str):
			role_ids = [role_ids]
		url = self.fosscord+'guilds/'+guild_id+'/members/'+member_id
		body = {'roles': role_ids}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	other
	'''

	#the only time this is observed in the client is in a guild
	def get_channel(self, channel_id):
		url = self.fosscord+'channels/'+channel_id
		return Wrapper.send_request(self.s, 'get', url, log=self.log)
