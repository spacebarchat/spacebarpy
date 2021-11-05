from ..requestsender import Wrapper

#This file includes apis that run when your client starts but idk where to organize them

class Other:
    __slots__ = ['s', 'fosscord', 'log']
    def __init__(self, s, fosscordurl, log):
        self.s = s
        self.fosscord = fosscordurl
        self.log = log

    def get_gateway_url(self):
        url = self.fosscord + 'gateway'
        return Wrapper.send_request(self.s, 'get', url, log=self.log)

    def get_detectables(self):
        url = self.fosscord + 'applications/detectable'
        return Wrapper.send_request(self.s, 'get', url, log=self.log)

    def get_oauth2_tokens(self):
        url = self.fosscord + 'oauth2/tokens'
        return Wrapper.send_request(self.s, 'get', url, log=self.log)