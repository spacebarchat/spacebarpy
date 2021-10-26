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

	def lazyGuild(self, guild_id, channel_ranges=None, typing=None, threads=None, activities=None, members=None, thread_member_lists=None):
		imports.GuildRequest(self.gatewayobject).lazyGuild(guild_id, channel_ranges, typing, threads, activities, members, thread_member_lists)

	def searchGuildMembers(self, guild_ids, query="", limit=10, presences=True, user_ids=None, nonce=None):
		imports.GuildRequest(self.gatewayobject).searchGuildMembers(guild_ids, query, limit, presences, user_ids, nonce)

	def DMchannel(self, channel_id):
		imports.DmRequest(self.gatewayobject).DMchannel(channel_id)

	def call(self, channelID, guildID=None, mute=False, deaf=False, video=False):
		imports.MediaRequest(self.gatewayobject).call(channelID, guildID, mute, deaf, video)

	def endCall(self):
		imports.MediaRequest(self.gatewayobject).endCall()