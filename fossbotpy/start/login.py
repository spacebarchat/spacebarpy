from ..RESTapiwrap import *
from ..utils.contextproperties import ContextProperties
import time

from ..logger import Logger

class Login:
	'''
	Manages HTTP authentication
	'''
	__slots__ = ['fosscord', 'log', 'editedS', 'xfingerprint']
	def __init__(self, s, fosscordurl, log):
		self.fosscord = fosscordurl
		self.log = log
		self.editedS = Wrapper.editedReqSession(s, {"remove": ["Authorization", "X-Fingerprint"]})

	def getXFingerprint(self):
		url = self.fosscord + "experiments"
		reqxfinger = Wrapper.sendRequest(self.editedS, 'get', url, headerModifications={"update":{"X-Context-Properties":ContextProperties.get("/app")}}, log=self.log)
		xfingerprint = reqxfinger.json().get('fingerprint')
		if not xfingerprint:
			Logger.log('xfingerprint could not be fetched.', None, self.log)
		return xfingerprint

	def login(self, email, password, undelete, captcha, source, gift_code_sku_id):
		url = self.fosscord + "auth/login"
		self.xfingerprint = self.getXFingerprint()
		self.editedS.headers.update({"X-Fingerprint": self.xfingerprint})
		body = {
			"email": email,
			"password": password,
			"undelete": undelete,
			"captcha_key": captcha,
			"login_source": source,
			"gift_code_sku_id": gift_code_sku_id
		}
		response = Wrapper.sendRequest(self.editedS, 'post', url, body, log=self.log)
		return response, self.xfingerprint
