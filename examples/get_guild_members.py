import fossbotpy
bot = fossbotpy.Client(token='token', base_url='https://dev.fosscord.com/api/v9/')

def close_after_fetching(resp, guild_id):
	if bot.gateway.finished_member_fetching(guild_id):
		lenmembersfetched = len(bot.gateway.session.guild(guild_id).members) #this line is optional
		print(str(lenmembersfetched)+' members fetched') #this line is optional
		bot.gateway.remove_command({'function': close_after_fetching, 'params': {'guild_id': guild_id}})
		bot.gateway.close()

def get_members(guild_id, channel_id):
	bot.gateway.fetch_members(guild_id, channel_id, keep="all", wait=1) #get all user attributes, wait 1 second between requests
	bot.gateway.command({'function': close_after_fetching, 'params': {'guild_id': guild_id}})
	bot.gateway.run()
	bot.gateway.reset_session() #saves 10 seconds when gateway is run again
	return bot.gateway.session.guild(guild_id).members

members = get_members('322850917248663552', '754536220826009670') #yes, the channel_id input is required
