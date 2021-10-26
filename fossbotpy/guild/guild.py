from ..RESTapiwrap import *
from ..utils.permissions import PERMS, Permissions
from ..utils.contextproperties import ContextProperties

import time
import base64

try:
	from urllib.parse import quote
except ImportError:
	from urllib import quote

class Guild(object):
	__slots__ = ['fosscord', 's', 'log']
	def __init__(self, fosscord, s, log): #s is the requests session object
		self.fosscord = fosscord
		self.s = s
		self.log = log

	'''
	invite codes / server info
	'''
	#get guild info from invite code
	def getInfoFromInviteCode(self, inviteCode, with_counts, with_expiration, fromJoinGuildNav):
		url = self.fosscord+"invites/"+inviteCode
		if (with_counts!=None or with_expiration!=None or fromJoinGuildNav):
			url += "?"
			data = {}
			if fromJoinGuildNav:
				data["inputValue"] = inviteCode
			if with_counts != None:
				data["with_counts"] = with_counts
			if with_expiration != None:
				data["with_expiration"] = with_expiration
			url += "&".join( "%s=%s" % (k, quote(repr(data[k]).lower())) for k in data)
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	#just the join guild endpoint, default location mimics joining a guild from the ([+]Add a Server) button
	def joinGuildRaw(self, inviteCode, guild_id=None, channel_id=None, channel_type=None, location="join guild"):
		url = self.fosscord+"invites/"+inviteCode
		if location in ("accept invite page", "join guild"):
			return Wrapper.sendRequest(self.s, 'post', url, {}, headerModifications={"update":{"X-Context-Properties":ContextProperties.get(location, guild_id=guild_id, channel_id=channel_id, channel_type=channel_type)}}, log=self.log)
		elif location == "markdown":
			return Wrapper.sendRequest(self.s, 'post', url, {}, headerModifications={"update":{"X-Context-Properties":ContextProperties.get("markdown")}}, log=self.log)

	def joinGuild(self, inviteCode, location, wait):
		location = location.lower()
		if location in ("accept invite page", "join guild"):
			guildData = self.getInfoFromInviteCode(inviteCode, with_counts=True, with_expiration=True, fromJoinGuildNav=(location.lower()=="join guild")).json()
			if wait: time.sleep(wait)
			return self.joinGuildRaw(inviteCode, guildData["guild"]["id"], guildData["channel"]["id"], guildData["channel"]["type"], location)
		elif location == "markdown":
			return self.joinGuildRaw(inviteCode, location="markdown")

	def previewGuild(self, guildID, sessionID):
		url = self.fosscord+"guilds/"+guildID+"/members/@me?lurker=true"
		if sessionID != None:
			url += "&session_id="+sessionID
		return Wrapper.sendRequest(self.s, 'put', url, headerModifications={"update":{"X-Context-Properties":"e30="}}, log=self.log)

	def leaveGuild(self, guildID, lurking):
		url = self.fosscord+"users/@me/guilds/"+guildID
		body = {"lurking": lurking}
		return Wrapper.sendRequest(self.s, 'delete', url, body, log=self.log)

	def createInvite(self, channelID, max_age_seconds, max_uses, grantTempMembership, checkInvite, targetType): #has to be a channel thats in a guild. also checkInvite and targetType are basically useless.
		url = self.fosscord+"channels/"+channelID+"/invites"
		if max_age_seconds == False:
			max_age_seconds = 0
		if max_uses == False:
			max_uses = 0
		body = {"max_age": max_age_seconds, "max_uses": max_uses, "temporary": grantTempMembership}
		if checkInvite != "":
			body["validate"] = checkInvite
		if targetType != "":
			body["target_type"] = targetType
		return Wrapper.sendRequest(self.s, 'post', url, body, headerModifications={"update":{"X-Context-Properties":ContextProperties.get("guild header")}}, log=self.log)

	def deleteInvite(self, inviteCode):
		url = self.fosscord+'invites/'+inviteCode
		return Wrapper.sendRequest(self.s, 'delete', url, log=self.log)

	def getGuildInvites(self, guildID):
		url = self.fosscord+'guilds/'+guildID+'/invites'
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getChannelInvites(self, channelID):
		url = self.fosscord+'channels/'+channelID+'/invites'
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getGuilds(self, with_counts):
		url = self.fosscord+"users/@me/guilds"
		if with_counts != None:
			url += "?with_counts="+repr(with_counts).lower()
		headerMods = {"update":{"X-Track":self.s.headers.get("X-Super-Properties")}, "remove":["X-Super-Properties"]}
		return Wrapper.sendRequest(self.s, 'get', url, headerModifications=headerMods, log=self.log)

	def getGuildChannels(self, guildID):
		url = self.fosscord+'guilds/'+guildID+'/channels'
		headerMods = {"update":{"X-Track":self.s.headers.get("X-Super-Properties")}, "remove":["X-Super-Properties"]}
		return Wrapper.sendRequest(self.s, 'get', url, headerModifications=headerMods, log=self.log)

	def getDiscoverableGuilds(self, offset, limit):
		url = self.fosscord+"discoverable-guilds?offset="+repr(offset)+"&limit="+repr(limit)
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getGuildRegions(self, guildID):
		url = self.fosscord+'guilds/'+guildID+'/regions'
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	'''
	server moderation and management
	'''
	#create a guild
	def createGuild(self, name, icon, channels, systemChannelID, template):
		url = self.fosscord+"guilds"
		body = {"name": name, "icon":icon, "channels":channels, "system_channel_id":systemChannelID, "guild_template_code":template}
		if icon != None:
			with open(icon, "rb") as image:
				encodedImage = base64.b64encode(image.read()).decode('utf-8')
				body["icon"] = "data:image/png;base64,"+encodedImage
		return Wrapper.sendRequest(self.s, 'post', url, body, log=self.log)

	#delete a guild (assuming you are the owner)
	def deleteGuild(self, guildID):
		url = self.fosscord+"guilds/%s/delete" % (guildID)
		body = {}
		return Wrapper.sendRequest(self.s, 'post', url, body, log=self.log)

	#kick a user
	def kick(self, guildID, userID, reason):
		url = self.fosscord+"guilds/%s/members/%s?reason=%s" % (guildID, userID, quote(reason))
		headerMods = {"update":{"X-Audit-Log-Reason":reason}} if reason=="" else {}
		return Wrapper.sendRequest(self.s, 'delete', url, headerModifications=headerMods, log=self.log)

	#ban a user
	def ban(self, guildID, userID, deleteMessagesDays, reason):
		url = self.fosscord+"guilds/%s/bans/%s" % (guildID, userID)
		body = {"delete_message_days": str(deleteMessagesDays), "reason": reason}
		headerMods = {"update":{"X-Audit-Log-Reason":reason}} if reason=="" else {}
		return Wrapper.sendRequest(self.s, 'put', url, body, headerModifications=headerMods, log=self.log)

	def revokeBan(self, guildID, userID):
		url = self.fosscord+"guilds/"+guildID+"/bans/"+userID
		return Wrapper.sendRequest(self.s, 'delete', url, log=self.log)

	#lookup a user in a guild. thx Echocage for finding this api endpoint
	'''
	removed as this is a bot-only request. Use bot.gateway.checkGuildMembers instead.

	def getGuildMember(self, guildID, userID):
		url = self.fosscord+"guilds/%s/members/%s" % (guildID, userID)
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)
	'''

	def getRoleMemberCounts(self, guildID):
		url = self.fosscord+"guilds/"+guildID+"/roles/member-counts"
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getGuildIntegrations(self, guildID, include_applications):
		url = self.fosscord+"guilds/"+guildID+"/integrations"
		if include_applications != None:
			url += "?include_applications="+repr(include_applications).lower()
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getGuildTemplates(self, guildID):
		url = self.fosscord+"guilds/"+guildID+"/templates"
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getRoleMemberIDs(self, guildID, roleID):
		url = self.fosscord+"guilds/"+guildID+"/roles/"+roleID+"/member-ids"
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def addMembersToRole(self, guildID, roleID, memberIDs):
		if isinstance(memberIDs, str):
			memberIDs = [memberIDs]
		url = self.fosscord+"guilds/"+guildID+"/roles/"+roleID+"/members"
		body = {"member_ids":memberIDs}
		return Wrapper.sendRequest(self.s, 'patch', url, body, log=self.log)

	def setMemberRoles(self, guildID, memberID, roleIDs):
		if isinstance(roleIDs, str):
			roleIDs = [roleIDs]
		url = self.fosscord+"guilds/"+guildID+"/members/"+memberID
		body = {"roles": roleIDs}
		return Wrapper.sendRequest(self.s, 'patch', url, body, log=self.log)

	'''
	other stuff
	'''

	#get member verification data
	def getMemberVerificationData(self, guildID, with_guild, invite_code):
		url = self.fosscord+"guilds/"+guildID+"/member-verification?with_guild="+str(with_guild).lower()
		if invite_code != None:
			url += "&invite_code="+invite_code
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def agreeGuildRules(self, guildID, form_fields, version):
		url = self.fosscord+"guilds/"+guildID+"/requests/@me"
		form_fields[0]['response'] = True
		body = {"version":version, "form_fields":form_fields}
		return Wrapper.sendRequest(self.s, 'put', url, body, log=self.log)

	### threads
	#create thread
	def createThread(self, channelID, name, messageID, public, archiveAfter):
		url = self.fosscord+"channels/"+channelID
		if messageID:
			url += "/messages/"+messageID
		url += "/threads"
		choice = archiveAfter.lower()
		if choice == '1 hour':
			archiveAfterSeconds = 60
		elif choice in ('24 hour', '24 hours', '1 day'):
			archiveAfterSeconds = 1440
		elif choice in ('3 day', '3 days'):
			archiveAfterSeconds = 4320
		elif choice in ('1 week', '7 day', '7 days'):
			archiveAfterSeconds = 10080
		threadType = 11 if public else 12
		body = {"name": name, "type": threadType, "auto_archive_duration": archiveAfterSeconds}
		return Wrapper.sendRequest(self.s, 'post', url, body, log=self.log)
	#leave thread
	def leaveThread(self, threadID, location):
		url = self.fosscord+"channels/"+threadID+"/thread-members/@me?location="+quote(location)
		return Wrapper.sendRequest(self.s, 'delete', url, log=self.log)
	#join thread
	def joinThread(self, threadID, location):
		url = self.fosscord+"channels/"+threadID+"/thread-members/@me?location="+quote(location)
		return Wrapper.sendRequest(self.s, 'post', url, log=self.log)
	#archive thread
	def archiveThread(self, threadID, lock):
		url = self.fosscord+"channels/"+threadID
		body = {"archived": True, "locked": lock}
		return Wrapper.sendRequest(self.s, 'patch', url, body, log=self.log)
	#unarchive thread
	def unarchiveThread(self, threadID, lock):
		url = self.fosscord+"channels/"+threadID
		body = {"archived": False, "locked": lock}
		return Wrapper.sendRequest(self.s, 'patch', url, body, log=self.log)

	'''
	other
	'''
	#lookup school
	def lookupSchool(self, email, allowMultipleGuilds, useVerificationCode):
		url = self.fosscord+"guilds/automations/email-domain-lookup"
		body = {"email":email,"allow_multiple_guilds":allowMultipleGuilds}
		if useVerificationCode != None:
			body["use_verification_code"] = useVerificationCode
		return Wrapper.sendRequest(self.s, 'post', url, body, log=self.log)

	#https://fosscord.com/channels/hubID/mainChannelID
	def schoolHubWaitlistSignup(self, email, school):
		url = self.fosscord+"hub-waitlist/signup"
		body = {"email":email,"school":school}
		return Wrapper.sendRequest(self.s, 'post', url, body, log=self.log)

	def schoolHubSignup(self, email, hubID):
		url = self.fosscord+'guilds/automations/email-domain-lookup'
		body = {"email":email,"guild_id":hubID,"allow_multiple_guilds":True,"use_verification_code":True}
		return Wrapper.sendRequest(self.s, 'post', url, body, log=self.log)

	def verifySchoolHubSignup(self, hubID, email, code):
		url = self.fosscord+'guilds/automations/email-domain-lookup/verify-code'
		body = {"code":code,"guild_id":hubID,"email":email}
		return Wrapper.sendRequest(self.s, 'post', url, body, log=self.log)

	def getSchoolHubGuilds(self, hubID): #note, the "entity_id" returned in each entry is the guildID
		url = self.fosscord+'channels/'+hubID+'/directory-entries' #ik it says channels, but it's the hubID/"guildID".
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getSchoolHubDirectoryCounts(self, hubID): #this only returns the # of guilds/groups in each directory/category. This doesn't even return the category names
		url = self.fosscord+'channels/'+hubID+'/directory-entries/counts'
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def joinGuildFromSchoolHub(self, hubID, guildID):
		url = self.fosscord+'guilds/'+guildID+'/members/@me?lurker=false&directory_channel_id='+hubID
		headerMods = {"update":{"X-Context-Properties":ContextProperties.get("school hub guild")}}
		return Wrapper.sendRequest(self.s, 'put', url, headerModifications=headerMods, log=self.log)

	def searchSchoolHub(self, hubID, query):
		url = self.fosscord+'channels/'+hubID+'/directory-entries/search?query='+query
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getMySchoolHubGuilds(self, hubID): #or guilds you own that can potentially be added to the hub
		url = self.fosscord+'channels/'+hubID+'/directory-entries/list'
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def setSchoolHubGuildDetails(self, hubID, guildID, description, directoryID): #directoryID (int) is not a snowflake
		url = self.fosscord+'channels/'+hubID+'/directory-entry/'+guildID
		body = {"description":description,"primary_category_id":directoryID}
		return Wrapper.sendRequest(self.s, 'post', url, body, log=self.log)

	def getLiveStages(self, extra):
		url = self.fosscord+'stage-instances'
		if extra:
			url += '/extra'
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	#the only time this is observed in the client is in a guild
	def getChannel(self, channelID):
		url = self.fosscord+'channels/'+channelID
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)

	def getGuildActivitiesConfig(self, guildID):
		url = self.fosscord+'activities/guilds/'+guildID+'/config'
		return Wrapper.sendRequest(self.s, 'get', url, log=self.log)
