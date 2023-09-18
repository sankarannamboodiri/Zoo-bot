import discord
from discord.ext import commands
from discord import app_commands
import time
import os
from discord.utils import get
from typing import Optional
from discord import ui
import aiohttp
import discord
import io
from configparser import ConfigParser

file =  'config.ini'
config = ConfigParser()
config.read(file)

reaction_dict = dict()
for i in list (config['reaction_role']):
    reaction_dict[i] = config['reaction_role'][i]

target_message_id = int(config['message_id']['id'])


intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.target_message_id = target_message_id


@bot.event
async def on_ready():
  print("Bot is ready.")
  try:
    synced = await bot.tree.sync()
    print("Slash commands synced")
  except Exception as e:
    print(e)


@bot.event
async def on_raw_reaction_add(payload):
  if payload.message_id != bot.target_message_id:
    return

  guild = bot.get_guild(payload.guild_id)

  if payload.emoji.name in reaction_dict:
    role = discord.utils.get(guild.roles, name=reaction_dict[payload.emoji.name])
    member = await guild.fetch_member(payload.user_id)
    await member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload):
  if payload.message_id != bot.target_message_id:
    return
  guild = bot.get_guild(payload.guild_id)
  member = await guild.fetch_member(payload.user_id)

  if payload.emoji.name in reaction_dict:
    role = discord.utils.get(guild.roles, name=reaction_dict[payload.emoji.name])
    await member.remove_roles(role)


@bot.event
async def on_member_join(member):
  role = get(member.guild.roles, name=config['default_role']['role'])
  await member.add_roles(role)


@bot.tree.command(name="poll_maker")
@app_commands.describe(poll_title = "Enter the poll title", options="Enter options separated by '|'",ping_roles="Select a role which you want to ping (can only be used if you have ping permissions)")
async def say(interaction:discord.Interaction, poll_title:str, options:str, ping_roles: Optional[discord.Role] = None):
    try:
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        options = options.split("|")
        final_string = ""
        for i in range(len(options)):
            final_string = final_string + emojis[i]+ '\a'+ options[i] +"\n\n"

        embed = discord.Embed(title = poll_title , description=final_string, color=0xFFFFFF)
        member = interaction.user

        if (member.guild_permissions.mention_everyone) and ping_roles:
            await interaction.response.send_message(f"{ping_roles.mention}",embed=embed,allowed_mentions=discord.AllowedMentions.all())
        else:
            await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for i in range(len(options)):
                await message.add_reaction(emojis[i])
    except:
        embed = discord.Embed(title = "Error", description="Something went wrong", color=0xFFFFFF)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
class AnnouncementModal(discord.ui.Modal, title="Type in your announcement"):
    def __init__(self, ping,channel_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ping = ping
        self.channel_id = channel_id
    fb_title = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Title",
        required=True,
        placeholder="Announcement title"
    )

    message = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="Message",
        required=True,
        #max_length=500,
        placeholder="Give your message"
    )

    vc_channel_url = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="VC Channel's url",
        required=False,
        placeholder="VC url"
    )

    image_url = discord.ui.TextInput(
        style=discord.TextStyle.short,
        label="Image url",
        required=False,
        placeholder="Image url"
    )


    async def on_submit(self, interaction: discord.Interaction):
        
        channel = bot.get_channel(self.channel_id)

        embed = discord.Embed(title=self.fb_title.value,
                              description=self.message.value,
                              color=0xFFFFFF)
        
        embed.set_image(url="https://cdn.discordapp.com/attachments/560753089179680768/594957849797460177/Epic_gif-1.gif") 
        if self.image_url.value != "":
          url = self.image_url.value
          async with aiohttp.ClientSession() as session: # creates session
            async with session.get(url) as resp: # gets image from url
                img = await resp.read() # reads image from response
                with io.BytesIO(img) as file: # converts to file-like object
                    if self.ping:
                        await channel.send(embed=embed,allowed_mentions=discord.AllowedMentions.all(), content=f"{self.ping.mention}",file=discord.File(file, "testimage.png"))
                    else:
                        await channel.send(embed=embed,allowed_mentions=discord.AllowedMentions.all(),file=discord.File(file, "testimage.png"))

        else:
          if self.ping:
            await channel.send(embed=embed,allowed_mentions=discord.AllowedMentions.all(), content=f"{self.ping.mention}")
          else:
            await channel.send(embed=embed,allowed_mentions=discord.AllowedMentions.all())

        if ((self.vc_channel_url.value)) != "":
          await channel.send(content=self.vc_channel_url)
        await interaction.response.send_message(f"Announcement posted", ephemeral=True)

@bot.tree.command(name="announce")
@app_commands.describe(ping_roles="Select a role which you want to ping")
async def feedback(interaction: discord.Interaction,ping_roles: Optional[discord.Role] = None):
    guild = bot.guilds
    channel_id = interaction.channel_id
    member = interaction.user
    try:
      if (member.guild_permissions.mention_everyone) and ping_roles:
        announcement_modal = AnnouncementModal(ping=ping_roles,channel_id=channel_id)
        await interaction.response.send_modal(announcement_modal)
      elif (member.guild_permissions.mention_everyone):
        announcement_modal = AnnouncementModal(ping=None,channel_id=channel_id)
        await interaction.response.send_modal(announcement_modal)
      else:
        embed = discord.Embed(title = "Permission denied", description="You dont have the permission to use this command", color=0xFFFFFF)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        embed = discord.Embed(title = "Error", description="Something went wrong", color=0xFFFFFF)
        await interaction.response.send_message(embed=embed, ephemeral=True)

class SendMessage(discord.ui.Modal, title="Type in your message"):
    def __init__(self, ping,channel_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ping = ping
        self.channel_id = channel_id

    message = discord.ui.TextInput(
        style=discord.TextStyle.long,
        label="Message",
        required=True,
        placeholder="Write your message"
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        channel = bot.get_channel(self.channel_id)
        if self.ping:
          await channel.send(content=f"{self.ping.mention}"+" "+self.message.value)
        else:
          await channel.send(content=self.message.value)
        await interaction.response.send_message(f"Message posted", ephemeral=True)

@bot.tree.command(name="send_message")
@app_commands.describe(ping_roles="Select a role which you want to ping")
async def send_message(interaction: discord.Interaction,ping_roles: Optional[discord.Role] = None):
    guild = bot.guilds
    channel_id = interaction.channel_id
    member = interaction.user
    try:
      if (member.guild_permissions.mention_everyone) and ping_roles:
        message_modal = SendMessage(ping=ping_roles,channel_id=channel_id)
        await interaction.response.send_modal(message_modal)
      elif (member.guild_permissions.mention_everyone):
        message_modal = SendMessage(ping=None,channel_id=channel_id)
        await interaction.response.send_modal(message_modal)
      else:
        embed = discord.Embed(title = "Permission denied", description="You dont have the permission to use this command", color=0xFFFFFF)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except:
        embed = discord.Embed(title = "Error", description="Something went wrong", color=0xFFFFFF)
        await interaction.response.send_message(embed=embed, ephemeral=True)

my_secret = os.environ['TOKEN']
bot.run(my_secret)
