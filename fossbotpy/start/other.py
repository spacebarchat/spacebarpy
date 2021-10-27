from ..RESTapiwrap import *

#This file includes apis that run when your client starts but idk where to organize them

class Other:
    __slots__ = ['s', 'fosscord', 'log']
    def __init__(self, s, fosscordurl, log):
        self.s = s
        self.fosscord = fosscordurl
        self.log = log

    def getGatewayUrl(self):
        url = self.fosscord + "gateway"
        return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

    def getDetectables(self):
        url = self.fosscord + "applications/detectable"
        return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

    def getOauth2Tokens(self):
        url = self.fosscord + "oauth2/tokens"
        return Wrapper.sendRequest(self.s, 'get', url, log=self.log)