import json
import inspect
import time
import requests
from .logger import * #imports LogLevel and Logger

#functions for REST requests in Wrapper class
class Wrapper:
	#returns formatted log string and color for REST requests
	@staticmethod
	def log_formatter(function, data, part):
		# [+] (<class->function) Method -> url
		if part == "url":
			text = "{} -> {}".format(data[0].title(), data[1])
			color = LogLevel.SEND
		# [+] (<class->function) body
		elif part == "body":
			try:
				text = json.dumps(data)
			except:
				text = str(data)
			color = LogLevel.SEND
		# [+] (<class->function) Response <- response.text
		elif part == "response":
			text = "Response <- {}".format(data.encode('utf-8'))
			color = LogLevel.RECEIVE
		formatted = " [+] {} {}".format(function, text)
		return formatted, color

	#decompression for brotli
	@staticmethod
	def brdecompress(payload, log):
		try:
			import brotli
			data = brotli.decompress(payload)
			return data
		except:
			return payload

	#header modifications, like endpoints that don't need auth, superproperties, etc; also for updating headers like xfingerprint
	@staticmethod
	def edited_req_session(reqsession, header_modifications):
		edited = requests.Session()
		edited.headers.update(reqsession.headers.copy())
		edited.proxies.update(reqsession.proxies.copy())
		edited.cookies.update(reqsession.cookies.copy())
		if header_modifications not in ({}, None):
			if "update" in header_modifications:
				edited.headers.update(header_modifications["update"])
			if "remove" in header_modifications:
				for header in header_modifications["remove"]:
					if header in edited.headers:
						del edited.headers[header]
		return edited

	#only for "Connection reset by peer" errors. Influenced by praw's retry code
	@staticmethod
	def retry_logic(req_method, url, data, log):
		remaining_attempts = 3
		while True:
			try:
				return req_method(url=url, **data)
			except requests.exceptions.ConnectionError:
				if log:
					Logger.log("Connection reset by peer. Retrying...", None, log)
					time.sleep(0.3)
				remaining_attempts -= 1
				if remaining_attempts == 0:
					break
			except Exception:
				break
		return None

	#reqsession, method, url, body=None, header_modifications={}, timeout=None, log={"console":True, "file":False}
	@staticmethod
	def send_request(*args, **kwargs): #header_modifications = {"update":{}, "remove":[]}
		#weird way to set vars ik, but python was doing some weird things like not updating header_modifications so...temp fix...
		body = kwargs.get('body', None)
		header_modifications = kwargs.get('header_modifications', {})
		timeout = kwargs.get('timeout', None)
		log = kwargs.get('log', None)
		if len(args) >= 3:
			reqsession, method, url = args[0:3]
			if len(args) == 4:
				body = args[-1]
		else:
			Logger.log('requests session, method, and url required.', None, log)
			return
		#ugly code above...hopefully temporary
		if hasattr(reqsession, method): #just checks if post, get, whatever is a valid requests method
			# 1. find function
			stack = inspect.stack()
			function_name = "({}->{})".format(str(stack[1][0].f_locals['self']).split(' ')[0], stack[1][3])
			# 2. edit request session if needed
			if body == None:
				if header_modifications.get('remove', None) == None:
					header_modifications['remove'] = ['Content-Type']
				else:
					header_modifications['remove'].append('Content-Type')
			s = Wrapper.edited_req_session(reqsession, header_modifications)
			# 3. log url
			text, color = Wrapper.log_formatter(function_name, [method, url], part="url")
			Logger.log(text, color, log)
			# 4. format body and log
			data = {} #now onto the body (if exists)
			if body != None:
				if isinstance(body, dict):
					data = {'data': json.dumps(body)}
				else:
					data = {'data': body}
				if log:
					text, color = Wrapper.log_formatter(function_name, body, part="body")
					Logger.log(text, color, log)
			# 5. put timeout in data if needed (when we don't want to wait for a response from fosscord)
			if timeout != None:
				data['timeout'] = timeout
			# 6. the request
			response = Wrapper.retry_logic(getattr(s, method), url, data, log)
			# 7. brotli decompression of response
			if response and response.headers.get('Content-Encoding') == "br": #decompression; gzip/deflate is automatically handled by requests module
				response._content = Wrapper.brdecompress(response.content, log)
			# 8. log response
			if response != None:
				text, color = Wrapper.log_formatter(function_name, response.text, part="response")
				Logger.log(text, color, log)
			# 9. return response object with decompressed content
			return response
		else:
			Logger.log('Invalid request method.', None, log)
