from ..RESTapiwrap import *

#This file includes apis that run when your client starts but idk where to organize them
#Maybe they'll get organized eventually, idk
class Other:
    __slots__ = ['s', 'fosscord', 'log']
    def __init__(self, s, fosscordurl, log):
        self.s = s
        self.fosscord = fosscordurl
        self.log = log

    def getGatewayUrl(self):
        url = self.fosscord + "gateway"
        return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

    def getfosscordStatus(self):
        url = "https://status.fosscord.com/api/v2/scheduled-maintenances/upcoming.json"
        return Wrapper.sendRequest(self.s, 'get', url, headerModifications={"remove":["Authorization", "X-Super-Properties"]}, log=self.log)

    def getDetectables(self):
        url = self.fosscord + "applications/detectable"
        return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

    def getOauth2Tokens(self):
        url = self.fosscord + "oauth2/tokens"
        return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

    def getVersionStableHash(self, underscore=None):
        if isinstance(underscore, int):
            underscore = str(underscore)
        url = "https://fosscord.com/assets/version.stable.json"
        if isinstance(underscore, str):
            url += "?_="+underscore
        return Wrapper.sendRequest(self.s, 'get', url, headerModifications={"remove":["Authorization", "X-Super-Properties"]}, log=self.log)