from requests_toolbelt import MultipartEncoder
import random,string
import time, datetime
import os.path
import json
import base64

from ..utils.fileparse import Fileparse
from ..utils.contextproperties import ContextProperties
from ..utils.snowflake import Snowflake
from ..requestsender import Wrapper

try:
	from urllib.parse import quote_plus, urlparse, urlencode
except ImportError:
	from urllib import quote_plus, urlencode
	from urlparse import urlparse

class Channels(object):
	__slots__ = ['fosscord', 's', 'log']
	def __init__(self, fosscord, s, log): #s is the requests session object
		self.fosscord = fosscord
		self.s = s
		self.log = log

	#create a DM
	def create_dm(self, recipients):
		url = '{}users/@me/channels'.format(self.fosscord)

		if isinstance(recipients, str):
			recipients = [recipients]
		body = {'recipients': recipients}

		if len(recipients)>1:
			context = ContextProperties.get('new group dm')
		else:
			context = 'e30=' #{}
		header_mods = {'update':{'X-Context-Properties':context}}

		return Wrapper.send_request(self.s, 'post', url, body, header_modifications=header_mods, log=self.log)

	#delete_channel (also works for deleting dms/dm-groups)
	def delete_channel(self, channel_id):
		u = '{}channels/{}'
		url = u.format(self.fosscord, channel_id)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def remove_from_dm_group(self, channel_id, user_id):
		u = '{}channels/{}/recipients/{}'
		url = u.format(self.fosscord, channel_id, user_id)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def add_to_dm_group(self, channel_id, user_id):
		u = '{}channels/{}/recipients/{}'
		url = u.format(self.fosscord, channel_id, user_id)
		context = ContextProperties.get('add friends to dm')
		header_mods = {'update':{'X-Context-Properties':context}}
		return Wrapper.send_request(self.s, 'put', url, header_modifications=header_mods, log=self.log)

	def create_dm_group_invite(self, channel_id, max_age_seconds):
		u = '{}channels/{}/invites'
		url = u.format(self.fosscord, channel_id)
		if max_age_seconds == False:
			max_age_seconds = 0
		body = {'max_age': max_age_seconds}
		context = ContextProperties.get('Group DM Invite Create')
		header_mods = {'update':{'X-Context-Properties':context}}
		return Wrapper.send_request(self.s, 'post', url, body, header_modifications=header_mods, log=self.log)

	def set_dm_group_name(self, channel_id, name):
		u = '{}channels/{}'
		url = u.format(self.fosscord, channel_id)
		body = {'name': name}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def set_dm_group_icon(self, channel_id, image_path):
		u = '{}channels/{}'
		url = u.format(self.fosscord, channel_id)
		with open(image_path, 'rb') as image:
			encoded_image = base64.b64encode(image.read()).decode('utf-8')
		body = {'icon':'data:image/png;base64,'+encoded_image}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	#get messages
	def get_messages(self, channel_id, num, before_date, around_message):
		u = '{}channels/{}/messages?limit={}'
		url = u.format(self.fosscord, channel_id, num)
		if before_date != None:
			url += '&before={}'.format(before_date)
		elif around_message != None:
			url += '&around={}'.format(around_message)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#get message by channel ID and message ID
	#this doesnt work yet on fosscord cause fosscord is doing weird stuff with the around parameter...
	def get_message(self, channel_id, message_id):
		res = self.get_messages(channel_id, 1, None, message_id)
		if len(res._content)>2 and res.json()[0]['id'] != message_id:
			res._content = '[]'
		return res

	#greet with stickers
	def greet(self, channel_id, sticker_ids):
		u = '{}channels/{}/greet'
		url = u.format(self.fosscord, channel_id)
		if isinstance(sticker_ids, str):
			sticker_ids = [sticker_ids]
		body = {'sticker_ids': sticker_ids}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	#text message
	def send_message(self, channel_id, message, nonce, tts, embed, message_reference, allowed_mentions, sticker_ids):
		u = '{}channels/{}/messages'
		url = u.format(self.fosscord, channel_id)
		if nonce == 'calculate':
			body = {'content': message, 'tts': tts, 'nonce': Snowflake.get_snowflake()}
		else:
			body = {'content': message, 'tts': tts, 'nonce': str(nonce)}
		if embed != None:
			body['embed'] = embed
		if message_reference != None:
			body['message_reference'] = message_reference
		if allowed_mentions != None:
			body['allowed_mentions'] = allowed_mentions
		if sticker_ids != None:
			body['sticker_ids'] = sticker_ids
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	#send file
	def send_file(self, channel_id, file_location, is_url, message, tts, embed, message_reference, sticker_ids):
		#guess extension from file data
		mimetype, extensiontype, fd = Fileparse(self.s,self.log).parse(file_location,is_url)

		if mimetype == 'invalid': #error out
			return

		if is_url: #get filename
			a = urlparse(file_location)
			if len(os.path.basename(a.path))>0: #if everything is normal...
				filename = os.path.basename(a.path)
			else:
				if mimetype == 'unsupported': #if filetype not detected and extension not given
					filename = 'unknown'
				else: #if filetype detected but extension not given
					filename = 'unknown.'+extensiontype
		else: #local file
			filename = os.path.basename(os.path.normpath(file_location))

		#now time to post the file
		u = '{}channels/{}/messages'
		url = u.format(self.fosscord, channel_id)
		payload = {'content':message,'tts':tts}

		if message_reference != None:
			payload['message_reference'] = message_reference
			payload['type'] = 19
		if sticker_ids != None:
			payload['sticker_ids'] = sticker_ids
		if embed != None:
			payload['embed'] = embed
		if not is_url:
			with open(file_location, 'rb') as f:
				fd = f.read()

		fields={'file':(filename, fd, mimetype), 'payload_json':(None, json.dumps(payload))}

		string = ''.join(random.sample(string.ascii_letters+string.digits, 16))
		m = MultipartEncoder(fields=fields, boundary='----WebKitFormBoundary'+string)

		header_mods = {'update':{'Content-Type':m.content_type}}
		return Wrapper.send_request(self.s, 'post', url, body=m, header_modifications=header_mods, log=self.log)

	#doesn't work yet on fosscord
	def search_messages(self, guild_id, channel_id, author_id, author_type, mentions_user_id, has, link_hostname, embed_provider, embed_type, attachment_extension, attachment_filename, mentions_everyone, include_nsfw, after_date, before_date, text_search, after_num_results, limit): #classic fosscord search function, results with key 'hit' are the results you searched for, after_num_results (aka offset) is multiples of 25 and indicates after which messages (type int), filterResults defaults to False
		if guild_id:
			url = self.fosscord+'guilds/'+guild_id+'/messages/search?'
		else:
			if isinstance(channel_id, str):
				url = self.fosscord+'channels/{}/messages/search?'.format(channel_id)
			else:
				url = self.fosscord+'channels/{}/messages/search?'.format(channel_id[0])
		allqueryparams = []
		if channel_id:
			if isinstance(channel_id, str):
				channel_id = [channel_id]
			for i in channel_id:
				allqueryparams.append(('channel_id', str(i)))
		if author_id:
			if isinstance(author_id, str):
				author_id = [author_id]
			for i in author_id:
				allqueryparams.append(('author_id', str(i)))
		if author_type:
			if isinstance(author_type, str):
				author_type = [author_type]
			for i in author_type:
				allqueryparams.append(('author_type', str(i)))
		if mentions_user_id:
			if isinstance(mentions_user_id, str):
				mentions_user_id = [mentions_user_id]
			for i in mentions_user_id:
				allqueryparams.append(('mentions', str(i)))
		if has:
			if isinstance(has, str):
				has = [has]
			for i in has:
				allqueryparams.append(('has', str(i)))
		if link_hostname:
			if isinstance(link_hostname, str):
				link_hostname = [link_hostname]
			for i in link_hostname:
				allqueryparams.append(('link_hostname', str(i)))
		if embed_provider:
			if isinstance(embed_provider, str):
				embed_provider = [embed_provider]
			for i in embed_provider:
				allqueryparams.append(('embed_provider', str(i)))
		if embed_type:
			if isinstance(embed_type, str):
				embed_type = [embed_type]
			for i in embed_type:
				allqueryparams.append(('embed_type', str(i)))
		if attachment_extension:
			if isinstance(attachment_extension, str):
				attachment_extension = [attachment_extension]
			for i in attachment_extension:
				allqueryparams.append(('attachment_extension', str(i)))
		if attachment_filename:
			if isinstance(attachment_filename, str):
				attachment_filename = [attachment_filename]
			for i in attachment_filename:
				allqueryparams.append(('attachment_filename', str(i)))
		if mentions_everyone:
			allqueryparams.append(('mention_everyone', repr(mentions_everyone).lower()))
		if before_date:
			allqueryparams.append(('max_id', str(before_date)))
		if after_date:
			allqueryparams.append(('min_id', str(after_date)))
		if text_search:
			allqueryparams.append(('content', str(text_search)))
		if include_nsfw:
			allqueryparams.append(('include_nsfw', True))
		if after_num_results:
			allqueryparams.append(('offset', str(after_num_results)))
		if limit!=None:
			allqueryparams.append(('limit', str(limit)))
		querystring = urlencode(allqueryparams)
		url += querystring
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#doesnt work yet on fosscord because searching messages hasn't been implented into the api
	def filter_search_results(self, search_response): #only input is the requests response object outputted from search_messages, returns type list
		jsonresponse = search_response.json()['messages']
		filtered_messages = []
		for group in jsonresponse:
			for result in group:
				if 'hit' in result:
					filtered_messages.append(result)
		return filtered_messages

	def typing_action(self, channel_id): #sends the typing action for 10 seconds (or until you change the page)
		u = '{}channels/{}/typing'
		url = u.format(self.fosscord, channel_id)
		return Wrapper.send_request(self.s, 'post', url, log=self.log)

	def edit_message(self, channel_id, message_id, new_message):
		u = '{}channels/{}/messages/{}'
		url = u.format(self.fosscord, channel_id, message_id)
		body = {'content': new_message}
		return Wrapper.send_request(self.s, 'patch', url, body, log=self.log)

	def delete_message(self, channel_id, message_id):
		u = '{}channels/{}/messages/{}'
		url = u.format(self.fosscord, channel_id, message_id)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def pin_message(self, channel_id, message_id):
		u = '{}channels/{}/pins/{}'
		url = u.format(self.fosscord, channel_id, message_id)
		return Wrapper.send_request(self.s, 'put', url, log=self.log)

	def unpin_message(self, channel_id, message_id):
		u = '{}channels/{}/pins/{}'
		url = u.format(self.fosscord, channel_id, message_id)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def get_pins(self, channel_id): #get pinned messages
		u = '{}channels/{}/pins'
		url = u.format(self.fosscord, channel_id)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def add_reaction(self, channel_id, message_id, emoji):
		parsed = quote_plus(emoji)
		u = '{}channels/{}/messages/{}/reactions/{}/%40me'
		url = u.format(self.fosscord, channel_id, message_id, parsed)
		return Wrapper.send_request(self.s, 'put', url, log=self.log)

	def remove_my_reaction(self, channel_id, message_id, emoji):
		parsed = quote_plus(emoji)
		u = '{}channels/{}/messages/{}/reactions/{}/%40me'
		url = u.format(self.fosscord, channel_id, message_id, parsed)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def remove_reaction(self, channel_id, message_id, emoji):
		parsed = quote_plus(emoji)
		u = '{}channels/{}/messages/{}/reactions/{}'
		url = u.format(self.fosscord, channel_id, message_id, parsed)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def clear_reactions(self, channel_id, message_id):
		u = '{}channels/{}/messages/{}/reactions'
		url = u.format(self.fosscord, channel_id, message_id)
		return Wrapper.send_request(self.s, 'delete', url, log=self.log)

	def get_reactions(self, channel_id, message_id, emoji, limit):
		parsed = quote_plus(emoji)
		u = '{}channels/{}/messages/{}/reactions/{}?limit={}'
		url = u.format(self.fosscord, channel_id, message_id, parsed, limit)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	#acknowledge message (mark message read)
	def ack_message(self, channel_id, message_id, ack_token):
		u = '{}channels/{}/messages/{}/ack'
		url = u.format(self.fosscord, channel_id, message_id)
		body = {'token': ack_token}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	#unacknowledge message (mark message unread)
	def unack_message(self, channel_id, message_id, num_mentions):
		u = '{}channels/{}/messages/{}/ack'
		url = u.format(self.fosscord, channel_id, message_id)
		body = {'manual': True, 'mention_count': num_mentions}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	#doesnt work yet in fosscord
	def bulk_ack(self, data):
		u = '{}read-states/ack-bulk'
		url = u.format(self.fosscord)
		body = {'read_states': data}
		return Wrapper.send_request(self.s, 'post', url, body, log=self.log)

	def get_trending_gifs(self, provider, locale, media_format):
		u = '{}gifs/trending?provider={}&locale={}&media_format={}'
		url = u.format(self.fosscord, provider, locale, media_format)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)