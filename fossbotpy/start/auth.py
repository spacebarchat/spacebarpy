import time
import random

from ..requestsender import Wrapper
from ..utils.contextproperties import ContextProperties

from ..logger import Logger

class Auth:
	'''
	Manages HTTP authentication
	'''
	__slots__ = ['fosscord', 'log', 'edited_s']
	def __init__(self, s, fosscord, log):
		self.fosscord = fosscord
		self.log = log
		self.edited_s = Wrapper.edited_req_session(s, {'remove': ['Authorization']})

	#username choices from dev.fosscord.com source
	def random_username(self):
		prefix = [
			"mysterious",
			"adventurous",
			"courageous",
			"precious",
			"cynical",
			"despicable",
			"suspicious",
			"gorgeous",
			"lovely",
			"stunning",
			"based",
			"keyed",
			"ratioed",
			"twink",
			"phoned"
		]
		suffix = [
			"Anonymous",
			"Lurker",
			"User",
			"Enjoyer",
			"Hunk",
			"Top",
			"Bottom",
			"Sub",
			"Coolstar",
			"Wrestling",
			"TylerTheCreator",
			"Ad"
		]
		return '{}{}'.format(random.choice(prefix), random.choice(suffix))

	def register(self, email, username, password, invite, dob, gift_code_sku_id, captcha):
		url = self.fosscord + 'auth/register'
		if not username and not email:
			username = self.random_username()
		body = {
			'email': email,
			'username': username,
			'password': password,
			'invite': invite,
			'consent': True,
			'date_of_birth': dob,
			'gift_code_sku_id': gift_code_sku_id,
			'captcha_key': captcha,
		}
		return Wrapper.send_request(self.edited_s, 'post', url, body, log=self.log)

	def login(self, emailphone, password, undelete, captcha, source, gift_code_sku_id):
		url = self.fosscord + 'auth/login'
		body = {
			'login': emailphone,
			'password': password,
			'undelete': undelete,
			'captcha_key': captcha,
			'login_source': source,
			'gift_code_sku_id': gift_code_sku_id,
		}
		return Wrapper.send_request(self.edited_s, 'post', url, body, log=self.log)
