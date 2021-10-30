from ..RESTapiwrap import *

class Stickers(object):
	__slots__ = ['fosscord', 's', 'log']
	def __init__(self, fosscord, s, log): #s is the requests session object
		self.fosscord = fosscord
		self.s = s
		self.log = log

	def get_stickers(self, directory_id, store_listings, locale):
		store_listings = str(store_listings).lower()
		url = self.fosscord+"sticker-packs/directory-v2/"+directory_id+"?with_store_listings="+store_listings+"&locale="+locale
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_sticker_file(self, sticker_id, sticker_asset): #this is an apng
		url = "https://media.fosscordapp.net/stickers/"+sticker_id+"/"+sticker_asset+".png"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_sticker_json(self, sticker_id, sticker_asset):
		url = "https://fosscord.com/stickers/"+sticker_id+"/"+sticker_asset+".json"
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	def get_sticker_pack(self, sticker_pack_id):
		url = self.fosscord+"sticker-packs/"+sticker_pack_id
		return Wrapper.send_request(self.s, 'get', url, log=self.log)

	