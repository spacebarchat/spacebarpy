import websocket
import json
import time
import random
import zlib
import copy

try:
	import thread
except ImportError:
	import _thread as thread

#session data, response object, requests, and parsing
from .session import Session
from .response import Resp
from .request import Request
from .parse import Parse

#log to console/file
from ..logger import * #imports LogLevel and Logger

#dynamic imports
from ..importmanager import Imports
imports = Imports(
	{
		'GuildCombo': 'fossbotpy.gateway.guild.combo',
	}
)

#exceptions
class InvalidSessionException(Exception):
	pass

class NeedToReconnectException(Exception):
	pass

class ConnectionResumableException(Exception): #for certain close codes. 'exception'
	pass

class ConnectionManuallyClosedException(Exception):
	pass

def exception_checker(e, types): #this is an A or B or ... check
	for i in types:
		if isinstance(e,i):
			return True
	return False

#gateway class
class GatewayServer:

	__slots__ = ['token', 'super_properties', 'auth', 'RESTurl', 'sessionobj', 'proxy_host', 'proxy_port', 'keep_data', 'log', 'interval', 'session_id', 'sequence', 'READY', 'session', 'zlib_streamed', 'ws', '_after_message_hooks', '_last_err', '_last_close_event', 'connected', 'resumable', 'voice_data', 'member_fetching_status', 'reset_members_on_session_reconnect', 'update_session_data', 'guild_member_searches', '_last_ack', 'latency', 'request', 'parse', '_zlib', 'connection_kwargs']

	class OPCODE:
		# Name                         Code  Client Action   Description
		DISPATCH =                     0  #  Receive         dispatches an event
		HEARTBEAT =                    1  #  Send/Receive    used for ping checking
		IDENTIFY =                     2  #  Send            used for client handshake
		#PRESENCE_UPDATE =             3  #  Send            used to update the client status *does not work yet in fosscord
		VOICE_STATE_UPDATE =           4  #  Send            used to join/move/leave voice channels
		VOICE_SERVER_PING =            5  #  Send            used for voice ping checking
		RESUME =                       6  #  Send            used to resume a closed connection
		RECONNECT =                    7  #  Receive         used to tell when to reconnect (sometimes...)
		REQUEST_GUILD_MEMBERS =        8  #  Send            used to request guild members (when searching for members in the search bar of a guild)
		INVALID_SESSION =              9  #  Receive         used to notify client they have an invalid session id
		HELLO =                        10 #  Receive         sent immediately after connecting, contains heartbeat and server debug information
		HEARTBEAT_ACK =                11 #  Sent            immediately following a client heartbeat that was received
		#GUILD_SYNC =                  12 #  Receive         supposedly guild_sync but not used...idk
		DM_UPDATE =                    13 #  Send            used to get dm features
		LAZY_REQUEST =                 14 #  Send            fosscord responds back with GUILD_MEMBER_LIST_UPDATE type SYNC...
		LOBBY_CONNECT =                15 #  ?? pretty sure this doesnt work yet in fosscord
		LOBBY_DISCONNECT =             16 #  ?? pretty sure this doesnt work yet in fosscord
		LOBBY_VOICE_STATES_UPDATE =    17 #  Receive pretty sure this doesnt work yet in fosscord
		STREAM_CREATE =                18 #  ?? pretty sure this doesnt work yet in fosscord
		STREAM_DELETE =                19 #  ?? pretty sure this doesnt work yet in fosscord
		STREAM_WATCH =                 20 #  ?? pretty sure this doesnt work yet in fosscord
		STREAM_PING =                  21 #  Send pretty sure this doesnt work yet in fosscord
		STREAM_SET_PAUSED =            22 #  ?? pretty sure this doesnt work yet in fosscord
		REQUEST_APPLICATION_COMMANDS = 24 #  ?? interactions not implemented yet in fosscord

	def __init__(self, websocketurl, token, super_properties, sessionobj='', RESTurl='', log={'console':True, 'file':False}): #session obj needed for proxies and some combo gateway functions (that also require http api wraps)
		self.token = token
		self.super_properties = super_properties
		self.auth = {
				'token': self.token,
				'capabilities': 125,
				'properties': self.super_properties,
				'presence': {
					'status': 'online',
					'since': 0,
					'activities': [],
					'afk': False
				},
				'compress': False,
				'client_state': {
					'guild_hashes': {},
					'highest_last_message_id': '0',
					'read_state_version': 0,
					'user_guild_settings_version': -1
				}
			}
		self.RESTurl = RESTurl #for helper http requests
		self.sessionobj = sessionobj #for helper http requests

		self.proxy_host = None if 'https' not in sessionobj.proxies else sessionobj.proxies['https'][8:].split(':')[0]
		self.proxy_port = None if 'https' not in sessionobj.proxies else sessionobj.proxies['https'][8:].split(':')[1]

		self.keep_data = ('dms', 'guilds', 'guild_channels') #keep data even after leaving dm, guild, or guild channel
		self.log = log

		self.interval = None
		self.session_id = None
		self.sequence = 0
		self.READY = False #becomes True once READY is received
		self.session = Session({})

		#websocket.enableTrace(True) #for debugging
		self.zlib_streamed = True if '&compress=zlib-stream' in websocketurl else False
		self.ws = self._get_ws_app(websocketurl)

		self._after_message_hooks = []
		self._last_err = None
		self._last_close_event = None

		self.connected = False
		self.resumable = False

		self.voice_data = {} #voice connections dependent on current (connected) session

		self.member_fetching_status = {'first': []}
		self.reset_members_on_session_reconnect = True #reset members after each session
		self.update_session_data = True
		self.guild_member_searches = {}

		#latency
		self._last_ack = None
		self.latency = None

		#gateway requests and parsing
		self.request = Request(self)
		self.parse = Parse

		#extra gateway connection kwargs
		self.connection_kwargs = {}

	#WebSocketApp, more info here: https://github.com/websocket-client/websocket-client/blob/master/websocket/_app.py#L84
	def _get_ws_app(self, websocketurl):
		headers = {
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'en-US,en;q=0.9',
			'Cache-Control': 'no-cache',
			'Pragma': 'no-cache',
			'Sec-WebSocket-Extensions': 'permessage-deflate; client_max_window_bits',
			'User-Agent': self.super_properties['browser_user_agent']
		}
		ws = websocket.WebSocketApp(websocketurl,
									header = headers,
									on_open=lambda ws: self.on_open(ws),
									on_message=lambda ws, msg: self.on_message(ws, msg),
									on_error=lambda ws, msg: self.on_error(ws, msg),
									on_close=lambda ws, close_code, close_msg: self.on_close(ws, close_code, close_msg)
									)
		return ws

	def decompress(self, bmessage): #input is byte message
		data = self._zlib.decompress(bmessage)
		if data == b'':
			return {'op':-1, 'd':{}, 's':-1, 't':''}
		try:
			jsonmessage = json.loads(data)
			return jsonmessage
		except:
			return data

	def on_open(self, ws):
		self.connected = True
		self.member_fetching_status = {'first': []}
		Logger.log('[gateway] Connected to websocket.', None, self.log)
		if not self.resumable:
			#send presences if 1 or more activites in previous session. Whether or not you're invisible doesn't matter apparently.
			if len(self.session.settings_ready) != 0:
				if self.session.user_settings.get('activities') not in (None, {}):
					self.auth['presence']['status'] = self.session.user_settings.get('status')
					self.auth['presence']['activities'] = imports.UserCombo(self).constructActivitiesList()
			self.send({'op': self.OPCODE.IDENTIFY, 'd': self.auth})
		else:
			self.resumable = False
			self.send({'op': self.OPCODE.RESUME, 'd': {'token': self.token, 'session_id': self.session_id, 'seq': self.sequence-1 if self.sequence>0 else self.sequence}})

	def on_message(self, ws, message):
		if self.zlib_streamed:
			response = self.decompress(message)
		else:
			response = json.loads(message.encode('UTF8'))
		if response['op'] != self.OPCODE.HEARTBEAT_ACK:
			self.sequence += 1
		resp = Resp(copy.deepcopy(response))
		if response['op'] == -1:
			Logger.log('[gateway] < invalid response received', LogLevel.RECEIVE, self.log)
		else:
			Logger.log('[gateway] < {}'.format(response), LogLevel.RECEIVE, self.log)
		Logger.log('[gateway] < {}'.format(response), LogLevel.RECEIVE, self.log)
		if response['op'] == self.OPCODE.HELLO: #only happens once, first message sent to client
			self.interval = (response['d']['heartbeat_interval'])/1000 #if this fails make an issue and I'll revert it back to the old method (slightly smaller wait time than heartbeat)
			thread.start_new_thread(self._heartbeat, ())
		elif response['op'] == self.OPCODE.HEARTBEAT_ACK:
			if self._last_ack != None:
				self.latency = time.perf_counter() - self._last_ack
		elif response['op'] == self.OPCODE.HEARTBEAT:
			self.send({'op': self.OPCODE.HEARTBEAT,'d': self.sequence})
		elif response['op'] == self.OPCODE.INVALID_SESSION:
			Logger.log('[gateway] Invalid session.', None, self.log)
			self._last_err = InvalidSessionException('Invalid Session Error.')
			if self.resumable:
				self.resumable = False
				self.sequence = 0
				self.close()
			else:
				self.sequence = 0
				self.close()
		elif response['op'] == self.OPCODE.RECONNECT:
			Logger.log('[gateway] Received opcode 7 (reconnect).', None, self.log)
			self._last_err = NeedToReconnectException('Fosscord sent an opcode 7 (reconnect).')
			self.close()
		if self.interval == None and response['op']!=-1:
			Logger.log('[gateway] Identify failed.', None, self.log)
			self.close()
		if resp.event.ready:
			self._last_err = None
			self.session_id = response['d']['session_id']
			settings_ready = resp.parsed.ready() #parsed
			if not self.reset_members_on_session_reconnect and self.session.read():
				for guild_id in settings_ready['guilds']:
					settings_ready['guilds'][guild_id]['members'] = self.session.guild(guild_id).members
			self.session.set_settings_ready(settings_ready)
			self.READY = True			
		if self.update_session_data:
			self.session_updates(resp)
		thread.start_new_thread(self._response_loop, (resp,))

	def on_error(self, ws, error):
		Logger.log('[gateway] < {}'.format(error), LogLevel.WARNING, self.log)
		self._last_err = error

	def on_close(self, ws, close_code, close_msg):
		self.connected = False
		self.READY = False #reset self.READY
		if close_code or close_msg:
			self._last_close_event = {'code': close_code, 'reason': close_msg}
			Logger.log('[gateway] close status code: ' + str(close_code), None, self.log)
			Logger.log('[gateway] close message: ' + str(close_msg), None, self.log)
			if not (4000<close_code<=4010):
				self.resumable = True
				self._last_err = ConnectionResumableException('Connection is resumable.')
			if close_code in (None, 1000, 1001, 1006):
				self._last_err = ConnectionManuallyClosedException('Disconnection initiated by client using close function.')
		Logger.log('[gateway] websocket closed', None, self.log)

	#Fosscord needs heartbeats, or else connection will sever
	def _heartbeat(self):
		Logger.log('[gateway] entering heartbeat', None, self.log)
		while self.connected:
			if self.interval == None: #can't replicate the issue so consider this a temp patch
				self.interval = 41.25
			time.sleep(self.interval)
			if not self.connected:
				break
			self.send({'op': self.OPCODE.HEARTBEAT,'d': self.sequence})
			self._last_ack = time.perf_counter()
		return

	#just a wrapper for ws.send
	def send(self, payload):
		Logger.log('[gateway] > {}'.format(payload), LogLevel.SEND, self.log)
		self.ws.send(json.dumps(payload))

	def close(self):
		self.connected = False
		self.READY = False #reset self.READY
		if not exception_checker(self._last_err, [InvalidSessionException, NeedToReconnectException]):
			self._last_err = ConnectionManuallyClosedException('Disconnection initiated by client using close function.')
		Logger.log('[gateway] websocket closed', None, self.log) #don't worry if this message prints twice
		self.ws.close()

	def command(self, func):
		if callable(func):
			self._after_message_hooks.append(func)
			return func
		elif isinstance(func, dict): #because I can't figure out out to neatly pass params to decorators :(. Normal behavior still works; use as usual.
			priority = func.pop('priority', len(self._after_message_hooks))
			self._after_message_hooks.insert(priority, func)
			return func['function']

	#kinda influenced by https://github.com/scrubjay55/Reddit_ChatBot_Python/blob/master/Reddit_ChatBot_Python/WebSockClient.py (Apache License 2.0)
	def _response_loop(self, resp): #thx ToasterUwU for bringing up dummy threads
		commandslist = self._after_message_hooks[:] #create a copy
		for func in commandslist:
			if callable(func):
				func(resp)
			elif isinstance(func, dict):
				function = func['function']
				params = func['params'] if 'params' in func else {}
				function(resp, **params)
		return

	def remove_command(self, func, exact_match=True, all_matches=False):
		try:
			if exact_match:
				self._after_message_hooks.index(func) #for raising the value error
				if all_matches:
					self._after_message_hooks = [i for i in self._after_message_hooks if i!=func]
				else: #simply remove first found
					del self._after_message_hooks[self._after_message_hooks.index(func)]
			else:
				commands_copy = [i if callable(i) else i['function'] for i in self._after_message_hooks] #list of just functions
				commands_copy.index(func) #for raising the value error
				if all_matches:
					self._after_message_hooks = [i for (i,j) in zip(self._after_message_hooks, commands_copy) if j!=func]
				else:
					del self._after_message_hooks[commands_copy.index(func)]
		except ValueError:
			Logger.log('{} not found in _after_message_hooks.'.format(func), None, self.log)
			pass

	def clear_commands(self):
		self._after_message_hooks = []

	def reset_session(self): #just resets some variables that in-turn, resets the session (client side). Do not run this while running run().
		self.interval = None
		self.session_id = None
		self.sequence = 0
		self.READY = False #becomes True once READY is received
		self._last_err = None
		self.voice_data = {}
		self.resumable = False #you can't resume anyways without session_id and sequence
		self._last_ack = None
		if self.reset_members_on_session_reconnect:
			self.member_fetching_status = {'first': []}

	#kinda influenced by https://github.com/scrubjay55/Reddit_ChatBot_Python (Apache License 2.0)
	def run(self, auto_reconnect=True):
		if auto_reconnect:
			while True:
				try:
					self._zlib = zlib.decompressobj()
					self.ws.run_forever(ping_interval=10, ping_timeout=5, http_proxy_host=self.proxy_host, http_proxy_port=self.proxy_port, **self.connection_kwargs)
					raise self._last_err
				except KeyboardInterrupt:
					self._last_err = KeyboardInterrupt('Keyboard Interrupt Error')
					Logger.log('[gateway] Connection forcibly closed using Keyboard Interrupt.', None, self.log)
					break
				except Exception as e:
					if auto_reconnect:
						if not exception_checker(e, [KeyboardInterrupt]):
							if exception_checker(e, [ConnectionResumableException]):
								self._last_err = None
								wait_time = random.randrange(1,6)
								Logger.log('[gateway] Connection Dropped. Attempting to resume last valid session in {} seconds.'.format(wait_time), None, self.log)
								time.sleep(wait_time)
							elif exception_checker(e, [ConnectionManuallyClosedException]):
								Logger.log('[gateway] Connection forcibly closed using close function.', None, self.log)
								break
							else:
								self.reset_session()
								Logger.log('[gateway] Connection Dropped. Retrying in 10 seconds.', None, self.log)
								time.sleep(10)
		else:
			self._zlib = zlib.decompressobj()
			self.ws.run_forever(ping_interval=10, ping_timeout=5, http_proxy_host=self.proxy_host, http_proxy_port=self.proxy_port, **self.connection_kwargs)

	######################################################
	def session_updates(self, resp):
		#***guilds
		#guild created
		if resp.event.guild:
			guild_data = resp.parsed.guild_create(my_user_id=self.session.user['id']) #user id needed for updating personal roles in that guild
			guild_id = guild_data['id']
			voice_state_data = guild_data.pop('voice_states', [])
			if not self.reset_members_on_session_reconnect and guild_id in self.session.guild_ids:
				guilddata['members'] = self.session.guild(guild_id).members
			self.session.set_guild_data(guild_id, guild_data)
			self.session.set_voice_state_data(guild_id, voice_state_data)
		#guild deleted
		elif resp.event.guild_deleted:
			if 'guilds' in self.keep_data:
				self.session.guild(resp.raw['d']['id']).update_data({'removed': True})  #add the indicator
			else:
				self.session.remove_guild_data(resp.raw['d']['id'])

		#***channels (dms and guilds)
		#channel created (either dm or guild channel)
		elif resp.event.channel:
			channel_data = resp.parsed.channel_create()
			channel_id = channel_data['id']
			if channel_data['type'] in ('dm', 'group_dm'): #dm
				self.session.set_dm_data(channel_id, channel_data)
			else: #other channels
				guild_id = channel_data.pop('guild_id')
				self.session.guild(guild_id).set_channel_data(channel_id, channel_data)
		#channel deleted (either dm or guild channel)
		elif resp.event.channel_deleted:
			channel_data = resp.parsed.channel_delete() #updated data :) ...unlike guild_delete events
			channel_data['removed'] = True #add the indicator
			channel_id = channel_data['id']
			if channel_data['type'] in ('dm', 'group_dm'): #dm
				if 'dms' in self.keep_data:
					self.session.DM(channel_id).update_data(channel_data)
				else:
					self.session.remove_dm_data(channel_id)
			else: #other channels (guild channels)
				guild_id = channel_data.pop('guild_id')
				if 'guild_channels' in self.keep_data:
					self.session.guild(guild_id).update_channel_data(channel_id, channel_data)
				else:
					self.session.guild(guild_id).remove_channel_data(channel_id)

		#***user updates
		#user settings updated
		elif resp.event.settings_updated:
			self.session.update_user_settings(resp.raw['d'])
		#user session replaced (useful for syncing activities btwn client and server)
		elif resp.event.session_replaced:
			new_status = resp.parsed.sessions_replace(session_id=self.session_id) #contains both status and activities
			self.session.update_user_settings(new_status)
	######################################################

	'''
	Guild/Server stuff
	'''
	#op14 related stuff
	def get_member_fetching_params(self, target_range_starts): #more for just proof of concept. target_range_starts must not contain duplicates and must be a list of integers
		target_range_starts = {i:1 for i in target_range_starts} #remove duplicates but preserve order
		if target_range_starts.get(0)!=None and target_range_starts.get(100)!=None:
			keys = list(target_range_starts)
			if keys.index(100)<keys.index(0):
				target_range_starts.pop(0) #needs to be removed or else fetch_members will enter an infinite loop because of how fosscord responds to member list requests
		start_index = 1 #can't start at 0 because can't divide by 0. No need to specify a stop index since fetch_members continues until end of multipliers
		method = [0] #because start_index is 1
		for index,i in enumerate(target_range_starts):
			method.append(i/(index+1))
		return start_index, method #return start_index and multipliers

	def fetch_members(self, guild_id, channel_id, method='overlap', keep=[], consider_updates=True, start_index=0, stop_index=1000000000, reset=True, wait=None, priority=0):
		if guild_id in self.member_fetching_status and reset_members_on_session_reconnect:
			del self.member_fetching_status[guild_id] #just resetting tracker on the specific guild_id
		self.command(
			{
				'function': imports.GuildCombo(self).fetch_members,
				'priority': priority,
				'params': {
					'guild_id': guild_id,
					'channel_id': channel_id,
					'method': method,
					'keep': keep,
					'consider_updates': consider_updates,
					'start_index': start_index,
					'stop_index': stop_index,
					'reset': reset,
					'wait': wait
				},
			}
		)


	def finished_member_fetching(self, guild_id):
		return self.member_fetching_status.get(guild_id) == 'done'

	def find_visible_channels(self, guild_id, types=['guild_text', 'dm', 'guild_voice', 'group_dm', 'guild_category', 'guild_news', 'guild_store', 'guild_news_thread', 'guild_public_thread', 'guild_private_thread', 'guild_stage_voice'], find_first=False):
		if len(self.session.read()[0]) == 0: #if never connected to gateway
			return
		return imports.GuildCombo(self).find_visible_channels(guild_id, types, find_first)

	#sends a series of opcode 14s to tell fosscord that you're looking at guild channels
	def subscribe_to_guild_events(self, only_large=False, wait=None):
		imports.GuildCombo(self).subscribe_to_guild_events(only_large, wait)

	#op8 related stuff
	def query_guild_members(self, guild_ids, query, save_as_query_override=None, limit=10, presences=True, keep=[]):
		if isinstance(guild_ids, str):
			guild_ids = [guild_ids]
		imports.GuildCombo(self).search_guild_members(guild_ids, query, save_as_query_override, limit, presences, None, keep)

	def check_guild_members(self, guild_ids, user_ids, presences=True, keep=[]):
		if isinstance(guild_ids, str):
			guild_ids = [guild_ids]
		imports.GuildCombo(self).search_guild_members(guild_ids, '', None, 10, presences, user_ids, keep)

	def finished_guild_search(self, guild_ids, query='', save_as_query_override=None, user_ids=None, keep=False):
		if isinstance(guild_ids, str):
			guild_ids = [guild_ids]
		save_as_query = query.lower() if save_as_query_override==None else save_as_query_override.lower()
		command = {
			'function': imports.GuildCombo(self).handle_guild_member_searches,
			'params': {
				'guild_ids': guild_ids,
				'save_as_query': save_as_query,
				'is_query_overridden': save_as_query_override != None,
				'user_ids': user_ids,
				'keep': keep
			},
		}
		if keep == False: #if keep param not provided, look if params are subset of command_list function params
			command['params'].pop('keep')
			for c in self._after_message_hooks:
				if isinstance(c, dict):
					if c.get('function').__func__ == imports.GuildCombo(self).handle_guild_member_searches.__func__:
						d1 = command['params']
						d2 = c.get('params', {})
						if all(key in d2 and d2[key] == d1[key] for key in d1): #https://stackoverflow.com/a/41579450/14776493
							return False #not finished yet with guild search
			return True
		else:
			return command not in self._after_message_hooks
