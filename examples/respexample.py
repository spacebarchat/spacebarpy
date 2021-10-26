#the following example uses all 3 attributes of resp

import fossbotpy
bot = fossbotpy.Client(token='token', base_url='https://dev.fosscord.com/api/v9/')

@bot.gateway.command
def resptest(resp):
	if resp.event.message:
		print(resp.raw) #raw response
		print(resp.parsed.message_create()['type'] == resp.parsed.auto()['type']) #will print True

bot.gateway.run()
