#https://luna.gitlab.io/fosscord-unofficial-docs/science_events.html

from ..requestsender import Wrapper
import time, datetime
import random

from ..utils.client_uuid import Client_UUID
from ..utils.snowflake import Snowflake

class Science(object):
	__slots__ = ['fosscord', 'edited_s', 'analytics_token', 'UUIDobj', 'log']
	def __init__(self, fosscord, s, analytics_token, user_id, log):
		self.fosscord = fosscord
		header_mods = {}
		if s.headers['Authorization'] == '':
			header_mods = {'update':{'Authorization':'fosscord'}}
		self.edited_s = Wrapper.edited_req_session(s, header_mods)
		self.analytics_token = analytics_token
		if user_id == '0':
			user_id = Snowflake.get_snowflake()
		self.UUIDobj = Client_UUID(user_id)
		self.log = log

	def get_current_unix_ms(self):
		return int(time.mktime(datetime.datetime.now().timetuple())*1000)

	def get_tracking_properties(self, duration='random'):
		now = self.get_current_unix_ms()
		tracking_properties = {'client_track_timestamp': now}
		if duration == 'random':
			duration = random.randint(40, 1000)
		tracking_properties['client_send_timestamp'] = now + duration
		tracking_properties['client_uuid'] = self.UUIDobj.calculate('default', 'default', True)
		return tracking_properties

	def science(self, events):
		url = '{}science'.format(self.fosscord)
		for event in events:
			if 'type' not in event:
				event['type'] = 'keyboard_mode_toggled' #random default type
			if ('properties' not in event
				or 'client_send_timestamp' not in event['properties']
				or 'client_track_timestamp' not in event['properties']
				or 'client_uuid' not in event['properties']):
				event['properties'] = self.get_tracking_properties()
			else:
				self.UUIDobj.event_num += 1
		body = {'token': self.analytics_token, 'events':events}
		#one of the many incompatabilities btwn fosscord and discord.
		#in discord you'd remove the auth header if analytics_token was None
		#fosscord requires auth for science however...
		return Wrapper.send_request(self.edited_s, 'post', url, body, log=self.log)
