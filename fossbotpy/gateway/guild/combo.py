#points to commands that help request info/actions using the gateway
#note, no need for importing GuildParse because resp is a Resp object (resp.parsed... does the trick)
#also, no need for importing GuildRequest because gatewayobj has that (self.gatewayobj.request... does the trick)

import time
import copy
import re
from ...utils.permissions import PERMS, Permissions
from ...logger import *

class GuildCombo(object):
	__slots__ = ['gatewayobj']
	def __init__(self, gatewayobj):
		self.gatewayobj = gatewayobj

	#fetch_members helper function
	def reformat_member(self, memberdata, keep=[]): #memberdata comes in as a dict and leaves as a tuple (user_id, memberdatareformatted). This is done to easily prevent duplicates in the member list when fetching.
		all_properties = ['pending', 'deaf', 'hoisted_role', 'presence', 'joined_at', 'public_flags', 'username', 'avatar', 'discriminator', 'premium_since', 'roles', 'is_pending', 'mute', 'nick', 'bot']
		if keep == None:
			remove = all_properties
		elif keep == "all":
			remove = []
		elif isinstance(keep, list) or isinstance(keep, tuple):
			remove = list(set(all_properties) - set(keep))
		elif isinstance(keep, str):
			remove = [i for i in all_properties if i!=keep]
		memberproperties = copy.deepcopy(memberdata['member']) if 'member' in memberdata else copy.deepcopy(memberdata)
		userdata = memberproperties.pop('user', {})
		user_id = userdata.pop('id', {})
		memberproperties.update(userdata)
		#filtering/removing
		if 'pending' in remove and 'pending' in memberproperties:
			del memberproperties['pending']
		if 'deaf' in remove and 'deaf' in memberproperties:
			del memberproperties['deaf']
		if 'hoisted_role' in remove and 'hoisted_role' in memberproperties:
			del memberproperties['hoisted_role']
		if 'presence' in remove and 'presence' in memberproperties:
			del memberproperties['presence']
		if 'joined_at' in remove and 'joined_at' in memberproperties:
			del memberproperties['joined_at']
		if 'public_flags' in remove and 'public_flags' in memberproperties:
			del memberproperties['public_flags']
		if 'username' in remove and 'username' in memberproperties:
			del memberproperties['username']
		if 'avatar' in remove and 'avatar' in memberproperties:
			del memberproperties['avatar']
		if 'discriminator' in remove and 'discriminator' in memberproperties:
			del memberproperties['discriminator']
		if 'premium_since' in remove and 'premium_since' in memberproperties:
			del memberproperties['premium_since']
		if 'roles' in remove and 'roles' in memberproperties:
			del memberproperties['roles']
		if 'is_pending' in remove and 'is_pending' in memberproperties:
			del memberproperties['is_pending']
		if 'mute' in remove and 'mute' in memberproperties:
			del memberproperties['mute']
		if 'nick' in remove and 'nick' in memberproperties:
			del memberproperties['nick']
		if 'bot' in remove and 'bot' in memberproperties:
			del memberproperties['bot']
		return user_id, memberproperties

	#fetch_members helper function
	def range_corrector(self, ranges): #just adds [0,99] at the beginning
		if [0,99] not in ranges:
			ranges.insert(0, [0,99])
		return ranges

	#fetch_members helper function
	def get_index(self, guild_id):
		return self.gatewayobj.member_fetching_status[guild_id][1]

	#fetch_members helper function
	def get_ranges(self, index, multiplier, member_count):
		initial_num = int(index*multiplier)
		ranges_list = [[initial_num, initial_num+99]]
		if member_count > initial_num+99:
			ranges_list.append([initial_num+100, initial_num+199])
		return self.range_corrector(ranges_list)

	#fetch_members helper function
	def update_current(self, guild_id):
		if not self.gatewayobj.finished_member_fetching(guild_id): #yep still gotta check for this
			self.gatewayobj.member_fetching_status[guild_id][1] = self.gatewayobj.member_fetching_status[guild_id][0]+1

	#fetch_members helper function
	def update_previous(self, guild_id):
		if not self.gatewayobj.finished_member_fetching(guild_id):
			self.gatewayobj.member_fetching_status[guild_id][0] = self.gatewayobj.member_fetching_status[guild_id][1]

	#todo: make channel_id optional (make a helper method to find the "optimal" channel). Also...maybe rewrite fetch_members to simply code a bit??
	def fetch_members(self, resp, guild_id, channel_id, method, keep, consider_updates, start_index, stop_index, reset, wait): #process is a little simpler than it looks. Keep in mind that there's no actual api endpoint to get members so this is a bit hacky. However, the method used below mimics how the official client loads the member list.
		if self.gatewayobj.READY:
			if self.gatewayobj.member_fetching_status.get(guild_id) == None: #request for lazy request
				self.gatewayobj.member_fetching_status[guild_id] = [start_index, start_index] #format is [previous index, current index]. This format is useful for the wait parameter.
				if not self.gatewayobj.session.guild(guild_id).has_members or reset:
					self.gatewayobj.session.guild(guild_id).reset_members() #reset
				if len(self.gatewayobj.member_fetching_status["first"]) == 0:
					self.gatewayobj.member_fetching_status["first"] = [guild_id]
					self.gatewayobj.request.lazy_guild(guild_id, {channel_id: [[0,99]]}, typing=True, threads=False, activities=True, members=[])
				else:
					self.gatewayobj.request.lazy_guild(guild_id, {channel_id: [[0,99]]}, typing=True, activities=True)
			if self.gatewayobj.member_fetching_status.get(guild_id) != None and not self.gatewayobj.finished_member_fetching(guild_id): #proceed with lazy requests
				index = self.get_index(guild_id) #index always has the current value
				end_fetching = False
				#find multiplier (this dictates the way the member list requested for)
				if method == "overlap": multiplier = 100
				elif method == "no overlap": multiplier = 200
				elif isinstance(method, int): multiplier = method
				elif isinstance(method, list) or isinstance(method, tuple): 
					if index<len(method):
						multiplier = method[index]
					else:
						end_fetching = True #ends fetching right after resp parsed
				ranges = self.get_ranges(index, multiplier, self.gatewayobj.session.guild(guild_id).member_count) if not end_fetching else [[0],[0]]
				#0th lazy request (separated from the rest because this happens "first")
				if index == start_index and not self.gatewayobj.session.guild(guild_id).unavailable:
					self.update_current(guild_id) #current = previous+1
					if wait!=None: time.sleep(wait)
					self.gatewayobj.request.lazy_guild(guild_id, {channel_id: ranges})
				if resp.event.guild_member_list:
					parsed = resp.parsed.guild_member_list_update()
					if parsed['guild_id'] == guild_id and ('SYNC' in parsed['types'] or 'UPDATE' in parsed['types']):
						end_fetching = False
						for ind,i in enumerate(parsed['types']):
							if i == 'SYNC':
								if len(parsed['updates'][ind]) == 0 and parsed['locations'][ind] in ranges[1:]: #checks if theres nothing in the SYNC data
									end_fetching = True
									break
								for item in parsed['updates'][ind]:
									if 'member' in item:
										member_id, member_properties = self.reformat_member(item, keep=keep)
										self.gatewayobj.session.guild(guild_id).update_one_member(member_id, member_properties)
										Logger.log('[gateway] [fetch_members] <SYNC> updated member '+member_id, None, self.gatewayobj.log)
								if not self.gatewayobj.finished_member_fetching(guild_id) and (index-self.gatewayobj.member_fetching_status[guild_id][0])==1:
									if wait!=None: time.sleep(wait)
									self.update_previous(guild_id) #previous = current
							elif i == 'UPDATE' and consider_updates: #this really only becomes useful for large guilds (because fetching members can take a quite some time for those guilds)
								for key in parsed['updates'][ind]:
									if key == 'member':
										member_id, member_properties = self.reformat_member(parsed['updates'][ind][key], keep=keep)
										self.gatewayobj.session.guild(guild_id).update_one_member(member_id, member_properties)
										Logger.log('[gateway] [fetch_members] <UPDATE> updated member '+member_id, None, self.gatewayobj.log)
							elif i == 'INVALIDATE':
								if parsed['locations'][ind] in ranges or parsed['member_count'] == 0:
									end_fetching = True
									break
						num_fetched = len(self.gatewayobj.session.guild(guild_id).members)
						rounded_up_fetched = num_fetched-(num_fetched%-100) #https://stackoverflow.com/a/14092788/14776493
						if ranges==[[0],[0]] or index>=stop_index or rounded_up_fetched>=self.gatewayobj.session.guild(guild_id).member_count or end_fetching or ranges[1][0]+100>self.gatewayobj.session.guild(guild_id).member_count: #putting whats most likely to happen first
							self.gatewayobj.member_fetching_status[guild_id] = "done"
							self.gatewayobj.remove_command(
							    {
							        "function": self.fetch_members,
							        "params": {
							            "guild_id": guild_id,
							            "channel_id": channel_id,
							            "method": method,
							            "keep": keep,
							            "consider_updates": consider_updates,
							            "start_index": start_index,
							            "stop_index": stop_index,
							            "reset": reset,
							            "wait": wait
							        },
							    }
							) #it's alright if you get a "not found in _after_message_hooks" error log. That's not an error for this situation.
						elif not self.gatewayobj.finished_member_fetching(guild_id) and index==self.gatewayobj.member_fetching_status[guild_id][0]:
							self.update_current(guild_id) #current = previous + 1
							self.gatewayobj.request.lazy_guild(guild_id, {channel_id: ranges})


	#helper method for subscribe_to_guild_events
	def find_visible_channels(self, guild_id, types, find_first):
		channel_ids = []
		if types == "all":
			types = ['guild_text', 'dm', 'guild_voice', 'group_dm', 'guild_category', 'guild_news', 'guild_store', 'guild_news_thread', 'guild_public_thread', 'guild_private_thread', 'guild_stage_voice']
		s = self.gatewayobj.session
		channels = s.guild(guild_id).channels
		for channel in channels.values():
			if channel['type'] in types:
				permissions = Permissions.calculate_permissions(s.user['id'], guild_id, s.guild(guild_id).owner, s.guild(guild_id).roles, s.guild(guild_id).me['roles'], channel["permission_overwrites"])
				if Permissions.check_permissions(permissions, PERMS.VIEW_CHANNEL):
					if find_first:
						return [channel['id']]
					else:
						channel_ids.append(channel['id'])
		return channel_ids

	def subscribe_to_guild_events(self, only_large, wait):
		if self.gatewayobj.READY:
			s = self.gatewayobj.session
			guild_ids = s.guild_ids
			first = {"channel_ranges":{}, "typing":True, "threads":True, "activities":True, "members":[], "thread_member_lists":[]}
			rest = {"channel_ranges":{}, "typing":True, "activities":True, "threads":True}
			for guild_id in guild_ids:
				#skip if needed (only_large checking)
				if only_large and not (s.guild(guild_id).unavailable or s.guild(guild_id).large):
					continue
				#op 14 field construction
				op14fields = {"guild_id":guild_id}
				if guild_id == guild_ids[0]:
					op14fields.update(first)
					if not s.guild(guild_id).unavailable:
						find_channel = self.find_visible_channels(guild_id, types="all", find_first=True)
						if find_channel:
							op14fields["channel_ranges"] = {find_channel[0]: [[0,99]]}
				else:
					op14fields.update(rest)
					if not s.guild(guild_id).unavailable:
						find_channel = self.find_visible_channels(guild_id, types="all", find_first=True)
						if find_channel:
							op14fields["channel_ranges"] = {find_channel[0]: [[0,99]]}
				#sending the request
				if wait: time.sleep(wait)
				self.gatewayobj.member_fetching_status["first"].append(guild_id)
				self.gatewayobj.request.lazy_guild(**op14fields)

	#helper for search_guild_members
	def handle_guild_member_searches(self, resp, guild_ids, save_as_query, is_query_overridden, user_ids, keep): #hm what happens if all user_ids are found? well good news: "not_found" value is just []
		if resp.event.guild_members_chunk:
			chunk = resp.parsed.auto()
			g_id = chunk["guild_id"]
			match = False
			if g_id in guild_ids:
				if user_ids and "not_found" in chunk:
					match = True
					for member in chunk["members"]:
						member_id, member_properties = self.reformat_member(member, keep=keep)
						self.gatewayobj.guild_member_searches[g_id]["ids"].add(member_id)
						self.gatewayobj.session.guild(g_id).update_one_member(member_id, member_properties)
				elif not user_ids:
					if is_query_overridden:
						match = True #no checks
						for member in chunk["members"]:
							member_id, member_properties = self.reformat_member(member, keep=keep)
							self.gatewayobj.guild_member_searches[g_id]["queries"][save_as_query].add(member_id)
							self.gatewayobj.session.guild(g_id).update_one_member(member_id, member_properties)
					else: #check results
						if all([(re.sub(' +', ' ', k["user"]["username"].lower()).startswith(save_as_query) or re.sub(' +', ' ', k["nick"].lower()).startswith(save_as_query)) if k.get('nick') else re.sub(' +', ' ', k["user"]["username"].lower()).startswith(save_as_query) for k in chunk["members"]]): #search user/nick, ignore case, replace consecutive spaces with 1 space
							match = True
							for member in chunk["members"]:
								member_id, member_properties = self.reformat_member(member, keep=keep)
								self.gatewayobj.guild_member_searches[g_id]["queries"][save_as_query].add(member_id)
								self.gatewayobj.session.guild(g_id).update_one_member(member_id, member_properties)
				if chunk["chunk_index"] == chunk["chunk_count"]-1 and g_id==guild_ids[-1]: #if at end
					if match:
						self.gatewayobj.remove_command(
							{
								"function": self.handle_guild_member_searches,
								"params": {
									"guild_ids": guild_ids,
									"save_as_query": save_as_query,
									"is_query_overridden": is_query_overridden,
									"user_ids": user_ids, 
									"keep": keep
								},
							}
						)

	def search_guild_members(self, guild_ids, query, save_as_query_override, limit, presences, user_ids, keep):
		if self.gatewayobj.READY:
			save_as_query = query.lower() if save_as_query_override==None else save_as_query_override.lower()
			#create a spot to put the data in bot.gateway.guild_member_searches
			if user_ids: #user_id storage
				for i in guild_ids:
					if i not in self.gatewayobj.guild_member_searches:
						self.gatewayobj.guild_member_searches[i] = {"ids":set()}
					if "ids" not in self.gatewayobj.guild_member_searches[i]:
						self.gatewayobj.guild_member_searches[i]["ids"] = set()
			else: #query storage (save_as_query)
				for k in guild_ids:
					if k not in self.gatewayobj.guild_member_searches:
						self.gatewayobj.guild_member_searches[k] = {"queries":{}}
					if "queries" not in self.gatewayobj.guild_member_searches[k]:
						self.gatewayobj.guild_member_searches[k]["queries"] = {}
					if save_as_query not in self.gatewayobj.guild_member_searches[k]["queries"]:
						self.gatewayobj.guild_member_searches[k]["queries"][save_as_query] = set()
			self.gatewayobj.command(
				{
					"function": self.handle_guild_member_searches,
					"priority": 0,
					"params": {
						"guild_ids": guild_ids,
						"save_as_query": save_as_query,
						"is_query_overridden": save_as_query_override != None,
						"user_ids": user_ids,
						"keep": keep,
					},
				}
			)
			self.gatewayobj.request.search_guild_members(guild_ids, query, limit, presences, user_ids)
