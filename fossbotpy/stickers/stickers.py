from ..RESTapiwrap import *

class Stickers(object):
	__slots__ = ['fosscord', 's', 'log']
	def __init__(self, fosscord, s, log): #s is the requests session object
		self.fosscord = fosscord
		self.s = s
		self.log = log

	def getStickers(self, directoryID, store_listings, locale):
		store_listings = str(store_listings).lower()
		url = self.fosscord+"sticker-packs/directory-v2/"+directoryID+"?with_store_listings="+store_listings+"&locale="+locale
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getStickerFile(self, stickerID, stickerAsset): #this is an apng
		url = "https://media.fosscordapp.net/stickers/"+stickerID+"/"+stickerAsset+".png"
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getStickerJson(self, stickerID, stickerAsset):
		url = "https://fosscord.com/stickers/"+stickerID+"/"+stickerAsset+".json"
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getStickerPack(self, stickerPackID):
		url = self.fosscord+"sticker-packs/"+stickerPackID
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	