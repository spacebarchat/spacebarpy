from ..RESTapiwrap import *
from ..utils.contextproperties import ContextProperties
import time

from ..logger import Logger

class Auth:
	'''
	Manages HTTP authentication
	'''
	__slots__ = ['fosscord', 'log', 'edited_s']
	def __init__(self, s, fosscord, log):
		self.fosscord = fosscord
		self.log = log
		self.edited_s = Wrapper.editedReqSession(s, {"remove": ["Authorization"]})

	def register(self, email, username, password, invite, dob, gift_code_sku_id, captcha):
		url = self.fosscord + "auth/register"
		body = {
			"email": email,
			"username": username,
			"password": password,
			"invite": invite,
			"consent": True,
			"date_of_birth": dob,
			"gift_code_sku_id": gift_code_sku_id,
			"captcha_key": captcha,
		}
		return Wrapper.sendRequest(self.edited_s, 'post', url, body, log=self.log)

	def login(self, email, password, undelete, captcha, source, gift_code_sku_id):
		url = self.fosscord + "auth/login"
		body = {
			"login": email,
			"password": password,
			"undelete": undelete,
			"captcha_key": captcha,
			"login_source": source,
			"gift_code_sku_id": gift_code_sku_id,
		}
		return Wrapper.sendRequest(self.edited_s, 'post', url, body, log=self.log)
