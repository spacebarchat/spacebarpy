class Embedder(object):
    __slots__ = ['json_embed']
    def __init__(self):
        self.json_embed = {"fields": []} #Create a 'fields' key otherwise we can't add anything to it, plus it doesn't effect anything if nothing is added.

    def read(self):
        return self.json_embed

    def title(self,title):
        self.json_embed.update({'title': title}) 

    def description(self,description):
        self.json_embed.update({'description': description}) 

    def url(self,url):
        self.json_embed.update({'url': url}) 

    def color(self,color):
        self.json_embed.update({'color': color}) 

    def footer(self,text,icon_url=""):
        self.json_embed.update({'footer': {
            'icon_url': icon_url,
            'text': text
        }}) 

    def image(self,url):
        self.json_embed.update({'image': {
            'url': url,
        }})

    def thumbnail(self,url):
        self.json_embed.update({'thumbnail': {
            'url': url,
        }})

    def author(self,name,url="",icon_url=""):
        self.json_embed.update({'author': {
            'name': name,
            'url': url,
            'icon_url':icon_url
        }})

    def fields(self,name,value,inline=False):
        self.json_embed['fields'].append({
            'name': name,
            'value': value,
            'inline': inline
        })
    
    