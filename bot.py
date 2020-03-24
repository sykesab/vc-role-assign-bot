# bot.py
# VC Role Assign - Discord bot
# Author: Aaron Sykes

import discord
import os

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged in as {0}!'.format(self.user))
        print('Member of guild(s) {0}'.format(self.guilds))

        # Go through guilds/channels and check if there are members in channels
        #   without proper roles.
        for guild in self.guilds:
            print('Checking guild "{0}" for users in channels...'.format(guild.name))
            for channel in guild.voice_channels:
                print('\tChecking channel "{0}"'.format(channel.name))
                for member in channel.members:
                    if discord.utils.get(member.roles, name=channel.name) == None:
                        await self._add_user_to_role(guild, member, channel)

    async def on_voice_state_update(self, member, before, after):
        username = member.name
        guild = member.guild
        new_ch = after.channel
        old_ch = before.channel

        if new_ch != None and old_ch == None: # User has just joined a channel and wasn't in one prior.
            # Add user to voice channel role.
            await self._add_user_to_role(guild, member, new_ch)

        elif new_ch != None and old_ch != None : # User has just moved from one channel to another.
            # Swap the user's channel role from the old channel to the new one.
            await self._remove_user_from_role(guild, member, old_ch)
            await self._add_user_to_role(guild, member, new_ch)

        else: # User has just left a channel.
            # Remove voice channel role from user.
            await self._remove_user_from_role(guild, member, old_ch)

    ################ Just some helpers ################

    async def _create_role_if_not_exists(self, guild, member, channel):
        """Create the role for a voice channel if it doesn't exist."""
        vc_role = discord.utils.get(guild.roles, name=channel.name)
        if vc_role == None:
            vc_role = await guild.create_role(name=channel.name, mentionable=True, reason='User {0} joined voice channel {1} and role did not exist.'.format(member.name, channel.name))

        return vc_role

    async def _remove_role_if_channel_empty(self, role, member, channel):
        """Delete the role if no other users remain in the voice channel."""
        if not channel.members:
            await role.delete(reason='Last user ({0}) left voice channel {1}.'.format(member.name, channel.name))

    async def _add_user_to_role(self, guild, member, channel):
        """Add a user to a specific voice channel role."""
        print('Assigning user {0} channel role "{1}".'.format(member.name, channel.name))
        vc_role = await self._create_role_if_not_exists(guild, member, channel)
        await member.add_roles(vc_role, reason='User {0} entered voice channel {1}.'.format(member.name, channel), atomic=True)

    async def _remove_user_from_role(self, guild, member, channel):
        """Remove the channel role from the user."""
        print('Removing user {0} from channel role "{1}".'.format(member.name, channel.name))
        try:
            vc_role = discord.utils.get(member.roles, name=channel.name) # I hope this is never None
            await member.remove_roles(vc_role, reason='User {0} left voice channel {1}.'.format(member.name, channel.name))

            # Delete the role if no other users are in the voice channel.
            await self._remove_role_if_channel_empty(vc_role, member, channel)

        except AttributeError as err:
            print("ERROR: Tried to remove user from role that they didn't have or didn't exist. This may happen occasionally.")
            print("ERROR MESSAGE: {0}".format(err))


client = MyClient()
client.run(os.getenv('VC_ROLE_ASSIGN_TOKEN'))
