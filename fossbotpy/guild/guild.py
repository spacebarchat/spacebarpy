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
	def get_info_from_invite_code(self, invite_code, with_counts, with_expiration, from_join_guild_nav):
		url = self.fosscord+'invites/'+invite_code
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
	def join_guildRaw(self, invite_code, guild_id=None, channel_id=None, channel_type=None, location='join guild'):
		url = self.fosscord+'invites/'+invite_code
		if location in ('accept invite page', 'join guild'):
			return Wrapper.send_request(self.s, 'post', url, {}, header_modifications={'update':{'X-Context-Properties':ContextProperties.get(location, guild_id=guild_id, channel_id=channel_id, channel_type=channel_type)}}, log=self.log)
		elif location == 'markdown':
			return Wrapper.send_request(self.s, 'post', url, {}, header_modifications={'update':{'X-Context-Properties':ContextProperties.get('markdown')}}, log=self.log)

	def join_guild(self, invite_code, location, wait):
		location = location.lower()
		if location in ('accept invite page', 'join guild'):
			guild_data = self.get_info_from_invite_code(invite_code, with_counts=True, with_expiration=True, from_join_guild_nav=(location.lower()=='join guild')).json()
			if wait: time.sleep(wait)
			return self.join_guildRaw(invite_code, guild_data['guild']['id'], guild_data['channel']['id'], guild_data['channel']['type'], location)
		elif location == 'markdown':
			return self.join_guildRaw(invite_code, location='markdown')

	def preview_guild(self, guild_id, session_id):
		url = self.fosscord+'guilds/'+guild_id+'/members/@me?lurker=true'
		if session_id != None:
			url += '&session_id='+session_id
		return Wrapper.send_request(self.s, 'put', url, header_modifications={'update':{'X-Context-Properties':'e30='}}, log=self.log)

	def leave_guild(self, guild_id, lurking):
		url = self.fosscord+'users/@me/guilds/'+guild_id
		body = {'lurking': lurking}
		return Wrapper.send_request(self.s, 'delete', url, body, log=self.log)

	def create_invite(self, channel_id, max_age_seconds, max_uses, grant_temp_membership, check_invite, target_type): #has to be a channel thats in a guild. also check_invite and target_type are basically useless.
		url = self.fosscord+'channels/'+channel_id+'/invites'
		if max_age_seconds == False:
			max_age_seconds = 0
		if max_uses == False:
			max_uses = 0
		body = {'max_age': max_age_seconds, 'max_uses': max_uses, 'temporary': grant_temp_membership}
		if check_invite != '':
			body['validate'] = check_invite
		if target_type != '':
			body['target_type'] = target_type
		return Wrapper.send_request(self.s, 'post', url, body, header_modifications={'update':{'X-Context-Properties':ContextProperties.get('guild header')}}, log=self.log)

	def delete_invite(self, invite_code):
		url = self.fosscord+'invites/'+invite_code
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def get_guild_invites(self, guild_id):
		url = self.fosscord+'guilds/'+guild_id+'/invites'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_channelInvites(self, channel_id):
		url = self.fosscord+'channels/'+channel_id+'/invites'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_guilds(self, with_counts):
		url = self.fosscord+'users/@me/guilds'
		if with_counts != None:
			url += '?with_counts='+repr(with_counts).lower()
		header_mods = {'update':{'X-Track':self.s.headers.get('X-Super-Properties')}, 'remove':['X-Super-Properties']}
		return Wrapper.send_request(self.s, 'get', url, header_modifications=header_mods, log=self.log)

	def get_guild_channels(self, guild_id):
		url = self.fosscord+'guilds/'+guild_id+'/channels'
		header_mods = {'update':{'X-Track':self.s.headers.get('X-Super-Properties')}, 'remove':['X-Super-Properties']}
		return Wrapper.send_request(self.s, 'get', url, header_modifications=header_mods, log=self.log)

	def get_discoverable_guilds(self, offset, limit):
		url = self.fosscord+'discoverable-guilds?offset='+repr(offset)+'&limit='+repr(limit)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_guild_regions(self, guild_id):
		url = self.fosscord+'guilds/'+guild_id+'/regions'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	'''
	server moderation and management
	'''
	#create a guild
	def create_guild(self, name, icon, channels, system_channel_id, template):
		url = self.fosscord+'guilds'
		body = {'name': name, 'icon':icon, 'channels':channels, 'system_channel_id':system_channel_id, 'guild_template_code':template}
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
		url = self.fosscord+'guilds/%s/members/%s?reason=%s' % (guild_id, user_id, quote(reason))
		header_mods = {'update':{'X-Audit-Log-Reason':reason}} if reason=='' else {}
		return Wrapper.send_request(self.s, 'delete', url, header_modifications=header_mods, log=self.log)

	#ban a user
	def ban(self, guild_id, user_id, delete_messagesDays, reason):
		url = self.fosscord+'guilds/%s/bans/%s' % (guild_id, user_id)
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

	def get_role_member_counts(self, guild_id):
		url = self.fosscord+'guilds/'+guild_id+'/roles/member-counts'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_guild_integrations(self, guild_id, include_applications):
		url = self.fosscord+'guilds/'+guild_id+'/integrations'
		if include_applications != None:
			url += '?include_applications='+repr(include_applications).lower()
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_guild_templates(self, guild_id):
		url = self.fosscord+'guilds/'+guild_id+'/templates'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_role_member_i_ds(self, guild_id, role_id):
		url = self.fosscord+'guilds/'+guild_id+'/roles/'+role_id+'/member-ids'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def add_members_to_role(self, guild_id, role_id, member_ids):
		if isinstance(member_ids, str):
			member_ids = [member_ids]
		url = self.fosscord+'guilds/'+guild_id+'/roles/'+role_id+'/members'
		body = {'member_ids':member_ids}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_member_roles(self, guild_id, member_id, role_i_ds):
		if isinstance(role_i_ds, str):
			role_i_ds = [role_i_ds]
		url = self.fosscord+'guilds/'+guild_id+'/members/'+member_id
		body = {'roles': role_i_ds}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	other stuff
	'''

	#get member verification data
	def get_member_verification_data(self, guild_id, with_guild, invite_code):
		url = self.fosscord+'guilds/'+guild_id+'/member-verification?with_guild='+str(with_guild).lower()
		if invite_code != None:
			url += '&invite_code='+invite_code
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def agree_guild_rules(self, guild_id, form_fields, version):
		url = self.fosscord+'guilds/'+guild_id+'/requests/@me'
		form_fields[0]['response'] = True
		body = {'version':version, 'form_fields':form_fields}
		return Wrapper.send_request(self.s, 'put', url, body, log=self.log)

	### threads
	#create thread
	def create_thread(self, channel_id, name, message_id, public, archive_after):
		url = self.fosscord+'channels/'+channel_id
		if message_id:
			url += '/messages/'+message_id
		url += '/threads'
		choice = archive_after.lower()
		if choice == '1 hour':
			archive_afterSeconds = 60
		elif choice in ('24 hour', '24 hours', '1 day'):
			archive_afterSeconds = 1440
		elif choice in ('3 day', '3 days'):
			archive_afterSeconds = 4320
		elif choice in ('1 week', '7 day', '7 days'):
			archive_afterSeconds = 10080
		thread_type = 11 if public else 12
		body = {'name': name, 'type': thread_type, 'auto_archive_duration': archive_afterSeconds}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)
	#leave thread
	def leave_thread(self, thread_id, location):
		url = self.fosscord+'channels/'+thread_id+'/thread-members/@me?location='+quote(location)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)
	#join thread
	def join_thread(self, thread_id, location):
		url = self.fosscord+'channels/'+thread_id+'/thread-members/@me?location='+quote(location)
		return Wrapper.send_request(self.s, 'post', url, log=self.log)
	#archive thread
	def archive_thread(self, thread_id, lock):
		url = self.fosscord+'channels/'+thread_id
		body = {'archived': True, 'locked': lock}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)
	#unarchive thread
	def unarchive_thread(self, thread_id, lock):
		url = self.fosscord+'channels/'+thread_id
		body = {'archived': False, 'locked': lock}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	'''
	other
	'''
	def get_live_stages(self, extra):
		url = self.fosscord+'stage-instances'
		if extra:
			url += '/extra'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#the only time this is observed in the client is in a guild
	def get_channel(self, channel_id):
		url = self.fosscord+'channels/'+channel_id
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_guild_activities_config(self, guild_id):
		url = self.fosscord+'activities/guilds/'+guild_id+'/config'
		return Wrapper.send_request(self.s, 'get', url, log=self.log)
