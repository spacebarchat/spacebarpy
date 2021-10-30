from ..RESTapiwrap import *
import time, datetime
import random

from ..utils.client_uuid import Client_UUID
from ..utils.snowflake import Snowflake

class Science(object):
	__slots__ = ['fosscord', 's', 'log', 'analytics_token', 'UUIDobj']
	def __init__(self, fosscord, s, log, analytics_token, user_id): #s is the requests session object
		self.fosscord = fosscord
		self.s = s
		self.log = log
		self.analytics_token = analytics_token
		if user_id == "0":
			user_id = Snowflake.get_snowflake()
		self.UUIDobj = Client_UUID(user_id)

	def get_current_unix_ms(self): #returns unix ts in milliseconds
		return int(time.mktime(datetime.datetime.now().timetuple()) * 1000)

	def get_tracking_properties(self, duration="random"):
		now = self.get_current_unix_ms()
		tracking_properties = {"client_track_timestamp": now}
		if duration == "random":
			tracking_properties["client_send_timestamp"] = now+random.randint(40, 1000)
		else:
			tracking_properties["client_send_timestamp"] = now+duration
		tracking_properties["client_uuid"] = self.UUIDobj.calculate(event_num="default", user_id="default", increment=True)
		return tracking_properties

	def science(self, events): #https://luna.gitlab.io/fosscord-unofficial-docs/science_events.html
		url = self.fosscord +"science"
		for event in events:
			if "type" not in event:
				event["type"] = "keyboard_mode_toggled" #random default type
			if "properties" not in event or "client_send_timestamp" not in event["properties"] or "client_track_timestamp" not in event["properties"] or "client_uuid" not in event["properties"]:
				event["properties"] = self.get_tracking_properties()
			else:
				self.UUIDobj.event_num += 1
		body = {'token': self.analytics_token, 'events':events}
		if self.analytics_token == None: #if not logged in. ex: bot=discum.Client(token='poop')
			header_modifications = {"remove": ["Authorization"]}
			return Wrapper.send_request(self.s, 'post', url, body, header_modifications=header_modifications, log=self.log)
		else:
			return Wrapper.send_request(self.s, 'post', url, body, log=self.log)
