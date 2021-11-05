import fossbotpy
bot = fossbotpy.Client(token='token', base_url='https://dev.fosscord.com/api/v9/')

@bot.gateway.command
def helloworld(resp):
    if resp.event.ready:
        user = bot.gateway.session.user
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))
    if resp.event.message:
        m = resp.parsed.auto()
        guild_id = m['guild_id'] if 'guild_id' in m else None #because DMs are technically channels too
        channel_id = m['channel_id']
        username = m['author']['username']
        discriminator = m['author']['discriminator']
        content = m['content']
        print("> guild {} channel {} | {}#{}: {}".format(guild_id, channel_id, username, discriminator, content))

bot.gateway.run(auto_reconnect=True)
