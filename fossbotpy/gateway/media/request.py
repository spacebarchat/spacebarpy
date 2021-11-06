#request
#not really implemented yet into fosscord, but these work

class MediaRequest(object):
	__slots__ = ['gatewayobj']
	def __init__(self, gatewayobj):
		self.gatewayobj = gatewayobj

	def call(self, channel_id, guild_id=None, mute=False, deaf=False, video=False):
		self.gatewayobj.send(
		    {
		        'op': self.gatewayobj.OPCODE.VOICE_STATE_UPDATE,
		        'd': {
		            'guild_id': guild_id,
		            'channel_id': channel_id,
		            'self_mute': mute,
		            'self_deaf': deaf,
		            'self_video': video,
		        },
		    }
		)

	def end_call(self):
		self.gatewayobj.send(
		    {
		        'op': self.gatewayobj.OPCODE.VOICE_STATE_UPDATE,
		        'd': {
		            'guild_id': None,
		            'channel_id': None,
		            'self_mute': False,
		            'self_deaf': False,
		            'self_video': False,
		        },
		    }
		)

