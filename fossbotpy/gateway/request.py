from ..importmanager import Imports
imports = Imports(
	{
		"GuildRequest": "fossbotpy.gateway.guild.request",
		"DmRequest": "fossbotpy.gateway.dms.request",
		"MediaRequest": "fossbotpy.gateway.media.request",
	}
)

class Request(object):
	__slots__ = ['gatewayobject']
	def __init__(self, gatewayobject):
		self.gatewayobject = gatewayobject #remember that the requests session obj is also passed in here

	def lazy_guild(self, guild_id, channel_ranges=None, typing=None, threads=None, activities=None, members=None, thread_member_lists=None):
		imports.GuildRequest(self.gatewayobject).lazy_guild(guild_id, channel_ranges, typing, threads, activities, members, thread_member_lists)

	def search_guild_members(self, guild_ids, query="", limit=10, presences=True, user_ids=None, nonce=None):
		imports.GuildRequest(self.gatewayobject).search_guild_members(guild_ids, query, limit, presences, user_ids, nonce)

	def DMchannel(self, channel_id):
		imports.DmRequest(self.gatewayobject).DMchannel(channel_id)

	def call(self, channel_id, guild_id=None, mute=False, deaf=False, video=False):
		imports.MediaRequest(self.gatewayobject).call(channel_id, guild_id, mute, deaf, video)

	def end_call(self):
		imports.MediaRequest(self.gatewayobject).end_call()