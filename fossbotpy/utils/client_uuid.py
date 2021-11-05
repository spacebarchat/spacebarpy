import random
import time, datetime
import struct
import base64

#thanks fweak for helping out
class Client_UUID(object):
	__slots__ = ['user_id', 'random_prefix', 'creation_time', 'event_num', 'UUID']
	def __init__(self, user_id, creation_time='now', event_num=0):
		self.user_id = int(user_id)
		num = int(4294967296 * random.random())
		self.random_prefix = num if num<=2147483647 else num-4294967296
		self.creation_time = int(time.mktime(datetime.datetime.now().timetuple()) * 1000) if creation_time == 'now' else creation_time
		self.event_num = event_num
		self.UUID = ''

	def calculate(self, event_num, user_id, increment):
		if event_num == 'default':
			event_num = self.event_num
		if user_id == 'default':
			user_id = self.user_id
		else:
			user_id = int(user_id)

		buf = bytearray(struct.pack('24x'))
		buf[0:4] = struct.pack('<i', user_id%4294967296 if user_id%4294967296<=2147483647 else user_id%4294967296-2147483647)
		buf[4:8] = struct.pack('<i', user_id>>32)
		buf[8:12] = struct.pack('<i', self.random_prefix)
		buf[12:16] = struct.pack('<i', self.creation_time%4294967296 if self.creation_time%4294967296<=2147483647 else self.creation_time%4294967296-2147483647)
		buf[16:20] = struct.pack('<i', self.creation_time>>32)
		buf[20:24] = struct.pack('<i', event_num)

		if increment:
			self.event_num += 1
		self.UUID = base64.b64encode(buf).decode('ascii')
		return self.UUID

	def refresh(self, reset_event_num=True):
		self.random_prefix = num if num<=2147483647 else num-4294967296
		self.creation_time = int(time.mktime(datetime.datetime.now().timetuple()) * 1000) if creation_time == 'now' else creation_time
		if reset_event_num:
			self.event_num = 0
		return self.calculate(event_num='default', user_id='default', increment=True)

	@staticmethod
	def parse(client_uuid):
		decoded_client_uuid = base64.b64decode(client_uuid)
		unpacked = []
		for i in range(6):
			unpacked.append(struct.unpack('<i', decoded_client_uuid[4*i:4*i+4])[0])
		UUIDdata = {}
		user_idguess = (unpacked[1]<<32) + unpacked[0]
		UUIDdata['user_id'] = repr(user_idguess if user_idguess%4294967296<=2147483647 else user_idguess+4294967296)
		UUIDdata['random_prefix'] = unpacked[2]
		creation_timeGuess = (unpacked[4]<<32) + unpacked[3]
		UUIDdata['creation_time'] = creation_timeGuess if creation_timeGuess%4294967296<=2147483647 else user_idguess+4294967296
		UUIDdata['event_num'] = unpacked[5]
		return UUIDdata
