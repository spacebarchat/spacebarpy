from ..types import Types

#parse
class ChannelParse(object): #can either be a guild channel or a DM or something else
	@staticmethod
	def channel_create(response):
		channel_data = dict(response['d'])
		channel_data['type'] = Types.channel_types[response['d']['type']]
		if channel_data['type'] in ('dm', 'group_dm'): #private_channel
			if 'recipient_ids' not in channel_data and 'recipients' in channel_data: #should be true, running this check just in case
				channel_data['recipient_ids'] = [i['id'] for i in channel_data['recipients']]
		return channel_data

	@staticmethod
	def channel_delete(response):
		channel_data = dict(response['d'])
		channel_data['type'] = Types.channel_types[response['d']['type']]
		if channel_data['type'] in ('dm', 'group_dm'): #private_channel
			if 'recipient_ids' not in channel_data and 'recipients' in channel_data:
				channel_data['recipient_ids'] = [i['id'] for i in channel_data['recipients']]
		return channel_data