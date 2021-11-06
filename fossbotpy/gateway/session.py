class Session:
	__slots__ = []
	settings_ready = {}
	def __init__(self, input_settings_ready):
		Session.settings_ready = input_settings_ready

	def set_settings_ready(self, data):
		Session.settings_ready = dict(data)

	@property
	def guild(self):
		return Guild

	@property
	def DM(self):
		return DM

	@property
	def relationship(self):
		return Relationship

	@property
	def user_guild_setting(self):
		return UserGuildSetting

	def read(self): #returns all Session settings
		return self.settings_ready

	###***USER***###
	@property
	def user(self):
		return self.settings_ready['user']

	###***GUILDS***### (general)
	@property
	def guilds(self):
		return self.settings_ready['guilds']

	@property
	def all_guild_i_ds(self): #even if you're not in that guild
		return list(self.settings_ready['guilds'])

	@property
	def guild_ids(self): #only for guilds that you're in
		return [guild_id for guild_id in self.guilds if 'removed' not in self.guilds[guild_id]]

	def set_guild_data(self, guild_id, guild_data):
		self.settings_ready['guilds'][guild_id] = guild_data

	def remove_guild_data(self, guild_id):
		self.settings_ready['guilds'].pop(guild_id, None)

	def set_dm_data(self, channel_id, channel_data):
		self.settings_ready['private_channels'][channel_id] = channel_data

	def remove_dm_data(self, channel_id):
		self.settings_ready['private_channels'].pop(channel_id, None)

	def set_voice_state_data(self, guild_id, voice_state_data):
		self.settings_ready_supp['voice_states'][guild_id] = voice_state_data

	###***RELATIONSHIPS***### (general)
	@property
	def relationships(self):
		return self.settings_ready['relationships']
	
	@property
	def relationship_i_ds(self):
		return list(self.settings_ready['relationships'])

	#friends
	@property
	def friends(self):
		f = {}
		for i in self.relationships: #where i is a user id
			if self.relationships[i]['type'] in ('friend', 1):
				f[i] = self.relationships[i]
		return f
	
	@property
	def friend_i_ds(self):
		return list(self.friends)

	#blocked	
	@property
	def blocked(self):
		b = {}
		for i in self.relationships: #where i is a user id
			if self.relationships[i]['type'] in ('blocked', 2):
				b[i] = self.relationships[i]
		return b
	
	@property
	def blocked_i_ds(self):
		return list(self.blocked)
	
	#incoming	
	@property
	def incoming_friend_requests(self):
		ifr = {}
		for i in self.relationships:
			if self.relationships[i]['type'] in ('pending_incoming', 3):
				ifr[i] = self.relationships[i]
		return ifr
	
	@property
	def incoming_friend_request_i_ds(self):
		return list(self.incoming_friend_requests)

	#outgoing
	@property
	def outgoing_friend_requests(self):
		ofr = {}
		for i in self.relationships:
			if self.relationships[i]['type'] in ('pending_outgoing', 4):
				ofr[i] = self.relationships[i]
		return ofr
	
	@property
	def outgoing_friend_request_i_ds(self):
		return list(self.outgoing_friend_requests)

	#friend merged presences	
	@property
	def online_friends(self):
		return self.settings_ready_supp['online_friends']
	
	@property
	def online_friend_i_ds(self):
		return list(self.online_friends)
		

	###***DMs***### (general)
	@property
	def DMs(self):
		return self.settings_ready['private_channels']

	@property
	def DMIDs(self):
		return list(self.DMs)
		

	###***USER SETTINGS***### (general)
	@property
	def user_guild_settings(self):
		return self.settings_ready['user_guild_settings'] #so uh...this is not only for guilds. It also covers group DMs so uh yea...weird naming
	
	@property
	def user_settings(self):
		return self.settings_ready['user_settings']
	
	@property
	def options_for_user_settings(self):
		return list(self.settings_ready['user_settings'])
		
	def update_user_settings(self, data):
		self.settings_ready['user_settings'].update(data)

	###other stuff
	@property
	def analytics_token(self):
		return self.settings_ready['analytics_token']

	@property
	def connected_accounts(self):
		return self.settings_ready['connected_accounts']

	@property
	def consents(self):
		return self.settings_ready['consents']

	@property
	def experiments(self):
		return self.settings_ready['experiments']

	@property
	def friend_suggestion_count(self):
		return self.settings_ready['friend_suggestion_count']

	@property
	def guild_experiments(self):
		return self.settings_ready['guild_experiments']

	@property
	def read_states(self):
		return self.settings_ready['read_state'] #another advantage of using websockets instead of requests (see https://github.com/discord/discord-api-docs/issues/13)

	@property
	def geo_ordered_rtc_regions(self):
		return self.settings_ready['geo_ordered_rtc_regions']

	@property
	def cached_users(self): #idk what these are
		return self.settings_ready['users']

	@property
	def tutorial(self):
		return self.settings_ready['tutorial'] #that tutorial you get when you first make an account


###specific guild
class Guild(Session):
	__slots__ = ['guild_id']
	def __init__(self, guild_id):
		self.guild_id = guild_id

	@property
	def data(self): #self.settings_ready['guilds']
		return Session.settings_ready['guilds'][self.guild_id]

	def set_data(self, new_data):
		Session.settings_ready['guilds'][self.guild_id] = new_data

	def update_data(self, data):
		Session.settings_ready['guilds'][self.guild_id].update(data)

	@property
	def unavailable(self):
		return 'unavailable' in Session.settings_ready['guilds'][self.guild_id]

	@property
	def has_members(self):
		return len(Session.settings_ready['guilds'][self.guild_id]['members']) >= 0

	@property
	def members(self):
		return Session.settings_ready['guilds'][self.guild_id]['members']

	@property
	def member_ids(self):
		return list(self.members)

	def reset_members(self):
		Session.settings_ready['guilds'][self.guild_id]['members'] = {}

	def update_one_member(self, user_id, user_properties):
		Session.settings_ready['guilds'][self.guild_id]['members'][user_id] = user_properties

	def update_members(self, memberdata): #where member data is a dictionary --> {userId: {properties}, ...}
		Session.settings_ready['guilds'][self.guild_id]['members'].update(memberdata)

	@property
	def owner(self):
		return Session.settings_ready['guilds'][self.guild_id]['owner_id'] #returns type int

	@property
	def boost_lvl(self):
		return Session.settings_ready['guilds'][self.guild_id]['premium_tier']

	@property
	def emojis(self):
		return Session.settings_ready['guilds'][self.guild_id]['emojis']

	@property
	def emoji_i_ds(self):
		return list(self.emojis)

	@property
	def banner(self):
		return Session.settings_ready['guilds'][self.guild_id]['banner']

	@property
	def discovery_splash(self): #not sure what this is about, something about server discoverability i guess (https://discord.com/developers/docs/resources/guild)
		return Session.settings_ready['guilds'][self.guild_id]['discovery_splash']

	@property
	def msg_notification_settings(self): #returns an int, 0=all messages, 1=only mentions (https://discord.com/developers/docs/resources/guild#guild-object-default-message-notification-level)
		return Session.settings_ready['guilds'][self.guild_id]['default_message_notifications']

	@property
	def rules_channel_id(self):
		return Session.settings_ready['guilds'][self.guild_id]['rules_channel_id']

	@property
	def verification_lvl(self): #returns an int, 0-4 (https://discord.com/developers/docs/resources/guild#guild-object-verification-level)
		return Session.settings_ready['guilds'][self.guild_id]['verification_level']

	@property
	def features(self): #returns a list of strings (https://discord.com/developers/docs/resources/guild#guild-object-guild-features)
		return Session.settings_ready['guilds'][self.guild_id]['features']

	@property
	def join_time(self): #returns when you joined the server, type string
		return Session.settings_ready['guilds'][self.guild_id]['joined_at']

	@property
	def region(self):
		return Session.settings_ready['guilds'][self.guild_id]['region']

	@property
	def application_id(self): #returns application id of the guild creator if it is bot-created (https://discord.com/developers/docs/resources/guild#guild-object-guild-features)
		return Session.settings_ready['guilds'][self.guild_id]['application_id']

	@property
	def afk_channel_id(self): #not sure what this is
		return Session.settings_ready['guilds'][self.guild_id]['afk_channel_id']

	@property
	def icon(self): #https://discord.com/developers/docs/reference#image-formatting
		return Session.settings_ready['guilds'][self.guild_id]['icon']

	@property
	def name(self):
		return Session.settings_ready['guilds'][self.guild_id]['name']

	@property
	def max_video_channel_users(self):
		return Session.settings_ready['guilds'][self.guild_id]['max_video_channel_users']

	@property
	def roles(self): #https://discord.com/developers/docs/topics/permissions#role-object
		return Session.settings_ready['guilds'][self.guild_id]['roles']

	@property
	def public_updates_channel_id(self):
		return Session.settings_ready['guilds'][self.guild_id]['public_updates_channel_id']

	@property
	def system_channel_flags(self): #https://discord.com/developers/docs/resources/guild#guild-object-system-channel-flags
		return Session.settings_ready['guilds'][self.guild_id]['system_channel_flags']

	@property
	def mfa_lvl(self): #https://discord.com/developers/docs/resources/guild#guild-object-mfa-level
		return Session.settings_ready['guilds'][self.guild_id]['mfa_level']

	@property
	def afk_timeout(self): #returns type int, unit seconds, https://discord.com/developers/docs/resources/guild
		return Session.settings_ready['guilds'][self.guild_id]['afk_timeout']

	@property
	def hashes(self): #https://github.com/fosscord/fosscord-api-docs/issues/1642
		return Session.settings_ready['guilds'][self.guild_id]['guild_hashes']

	@property
	def system_channel_id(self): #returns an int, the id of the channel where guild notices such as welcome messages and boost events are posted
		return Session.settings_ready['guilds'][self.guild_id]['system_channel_id']

	@property
	def lazy(self): #slightly different naming format since it returns a boolean (https://luna.gitlab.io/fosscord-unofficial-docs/lazy_guilds.html)
		return Session.settings_ready['guilds'][self.guild_id]['lazy']

	@property
	def num_boosts(self): #get number of boosts the server has gotten
		return Session.settings_ready['guilds'][self.guild_id]['premium_subscription_count']

	@property
	def large(self): #slightly different naming format since it returns a boolean, large if more than 250 members
		return Session.settings_ready['guilds'][self.guild_id]['large']

	@property
	def threads(self):
		return Session.settings_ready['guilds'][self.guild_id]['threads']

	@property
	def explicit_content_filter(self): #https://discord.com/developers/docs/resources/guild#guild-object-explicit-content-filter-level
		return Session.settings_ready['guilds'][self.guild_id]['explicit_content_filter']

	@property
	def splash_hash(self): #not sure what this is for
		return Session.settings_ready['guilds'][self.guild_id]['splash']

	@property
	def member_count(self):
		return Session.settings_ready['guilds'][self.guild_id]['member_count']

	@property
	def description(self):
		return Session.settings_ready['guilds'][self.guild_id]['description']

	@property
	def vanity_url_code(self):
		return Session.settings_ready['guilds'][self.guild_id]['vanity_url_code']

	@property
	def preferred_locale(self):
		return Session.settings_ready['guilds'][self.guild_id]['preferred_locale']

	def update_channel_data(self, channel_id, channel_data): #can also be used to update categories
		Session.settings_ready['guilds'][self.guild_id]['channels'][channel_id].update(channel_data)

	def set_channel_data(self, channel_id, channel_data): #can also be used to update categories
		Session.settings_ready['guilds'][self.guild_id]['channels'][channel_id] = channel_data

	def remove_channel_data(self, channel_id):
		Session.settings_ready['guilds'][self.guild_id]['channels'].pop(channel_id, None)

	@property
	def channels_and_categories(self): #returns all categories and all channels, all the data about that, wall of data so it can be a bit overwhelming, useful if you want to check how many channels your server has since fosscord counts categories as channels
		return Session.settings_ready['guilds'][self.guild_id]['channels']

	@property
	def all_channel_and_category_i_ds(self): #all of them, even ones you've been removed from
		return list(self.channels_and_categories)

	@property
	def channel_and_category_i_ds(self):
		return [channel_id for channel_id in self.channels_and_categories if 'removed' not in self.channels_and_categories[channel_id]]

	@property
	def categories(self): #all data about guild categories, can be overwhelming
		all_categories = {}
		for i in self.channels_and_categories: #https://discord.com/developers/docs/resources/channel#channel-object-channel-types
			if self.channels_and_categories[i]['type'] in ('guild_category', 4):
				all_categories[i] = self.channels_and_categories[i]
		return all_categories

	@property
	def category_i_ds(self):
		return list(self.categories)

	def category(self, category_id):
		return self.categories[category_id]

	@property
	def channels(self): #all data about all guild channels, can be overwhelming
		all_channels = {}
		for i in self.channels_and_categories: #https://discord.com/developers/docs/resources/channel#channel-object-channel-types
			if self.channels_and_categories[i]['type'] not in ('guild_category', 4):
				all_channels[i] = self.channels_and_categories[i]
		return all_channels

	@property
	def channel_ids(self):
		return list(self.channels)

	def channel(self, channel_id):
		return self.channels[channel_id]

	@property
	def me(self): #my roles, nick, etc in a guild
		return Session.settings_ready['guilds'][self.guild_id]['my_data']

	@property
	def application_command_count(self):
		return Session.settings_ready['guilds'][self.guild_id].get('application_command_count')

	@property
	def max_members(self):
		return Session.settings_ready['guilds'][self.guild_id]['max_members']
	
	@property
	def stages(self):
		return Session.settings_ready['guilds'][self.guild_id]['stage_instances']

	@property
	def stickers(self):
		return Session.settings_ready['guilds'][self.guild_id]['stickers']

###specific relationship
class Relationship(Session): #not the same organization as class guild
	__slots__ = ['user_id']
	def __init__(self, user_id):
		self.user_id = user_id

	@property
	def data(self): #usernames and discriminators are no longer provided in this data
		return Session.settings_ready['relationships'][self.user_id]

###specific DM
class DM(Session):
	__slots__ = ['DMID']
	def __init__(self, DMID):
		self.DMID = DMID

	@property
	def data(self):
		return Session.settings_ready['private_channels'][self.DMID]

	def update_data(self, data):
		Session.settings_ready['private_channels'][self.DMID].update(data)

	@property
	def recipients(self): #returns everyone in that DM except you
		return self.data['recipient_ids']

###specific User Guild Settings; keep in mind that user guild settings also includes some group dm notification settings stuff
class UserGuildSetting(Session):
	__slots__ = ['guild_id']
	def __init__(self, guild_id):
		self.guild_id = guild_id

	@property
	def data(self):
		if len(Session.settings_ready['user_guild_settings']['entries']) == 0:
			return None
		for i in range(len(Session.settings_ready['user_guild_settings']['entries'])):
			if Session.settings_ready['user_guild_settings']['entries'][i]['guild_id'] == self.guild_id:
				return Session.settings_ready['user_guild_settings']['entries'][i]
		return None