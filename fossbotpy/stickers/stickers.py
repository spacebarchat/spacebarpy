from ..requestsender import Wrapper

class Stickers(object):
	__slots__ = ['fosscord', 's', 'edited_s', 'main_url', 'log']
	def __init__(self, fosscord, s, main_url, log): #s is the requests session object
		self.fosscord = fosscord
		self.main_url = main_url+'/' if not main_url.endswith('/') else main_url
		self.s = s
		header_mods = {'remove': ['Authorization', 'X-Super-Properties', 'X-Debug-Options']}
		self.edited_s = Wrapper.edited_req_session(s, header_mods)
		self.log = log

	def get_stickers(self, country_code, locale):
		country_code = country_code.upper()
		u = '{}sticker-packs?country_code={}&locale={}'
		url = u.format(self.fosscord, country_code, locale)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_sticker_file(self, sticker_id): #this is an apng
		u = '{}stickers/{}.png?size=512'
		url = u.format(self.main_url, sticker_id)
		return Wrapper.send_request(self.edited_s, 'get', url, log=self.log)

	def get_sticker_pack(self, sticker_pack_id):
		u = '{}sticker-packs/{}'
		url = u.format(self.fosscord, sticker_pack_id)
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	