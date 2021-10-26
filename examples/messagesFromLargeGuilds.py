#not receiving messages from large guilds? simply run bot.gateway.subscribeToGuildEvents(wait=1) while
#the gateway is running and then you'll get messages from those large guilds

import fossbotpy
bot = fossbotpy.Client(token='token', base_url='https://dev.fosscord.com/api/v9/')

@bot.gateway.command
def helloworld(resp):
    if resp.event.ready:
        bot.gateway.subscribeToGuildEvents(wait=1)
    if resp.event.message:
        m = resp.parsed.auto()
        guildID = m.get('guild_id') #dms have no guild_id
        channelID = m['channel_id']
        username = m['author']['username']
        discriminator = m['author']['discriminator']
        content = m['content']
        print("> guild {} channel {} | {}#{}: {}".format(guildID, channelID, username, discriminator, content))

bot.gateway.run()
