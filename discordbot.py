from cmath import log
from distutils.sysconfig import PREFIX
import discord
from dotenv import load_dotenv
import os
load_dotenv()
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from discord.ext import commands
from pytz import timezone
from discord.ext import tasks
import time

PREFIX = os.environ['PREFIX']
TOKEN = os.environ['TOKEN']

def getNwInfoStr(data):
    return "거점명: " + data['area'] + "\n최대인원: " + data['num'] + "\n단계: " + data['stage'] + "\n채널: "+ data['ter'] + "-1"

bot = commands.Bot(command_prefix = '!',intents=discord.Intents.all())

nw_data = pd.read_csv('./bdo_nw_data.csv',encoding='cp949')
today_nws = nw_data[nw_data['date']=="일요일"].astype(str)
today_nw = nw_data
wd = {0:'월요일', 1:'화요일', 2:'수요일',3:'목요일',4:'금요일',5:'토요일', 6:'일요일'}

#bot on ready
@bot.event
async def on_ready():
    print("Bot is ready")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("v0.5b"))

channel = 0
full_num = 0
crnt_num = 0
np_tdnw = 0
cur_wd = -1
pre_wd = -1
role_attend = 0
is_roleChecked = False
is_init = False

"""
def roleCheck(ctx):
    roleA = discord.utils.get(ctx.guild.role, name="아카라이브") in ctx.author.roles
    roleV = discord.utils.get(ctx.guild.role, name="VESPER") in ctx.author.roles
    if roleA | roleV:
        return False
    else: return True
"""
crnt_usr = pd.DataFrame(columns=['name','guild','id'])
crnt_usr.head(10)
@bot.command()

async def init(ctx):
    if not ctx.author.top_role.permissions.administrator:
        await ctx.channel.send(str(ctx.author.mention + "권한이 없습니다."))
        return
    
    global wd ,today_nw, today_nws, full_num, np_tdnw, crnt_num, crnt_usr, is_roleChecked, role_attend, is_init, channel
    if is_init:
       await ctx.channel.send(str(ctx.author.mention + "이미 초기화를 했습니다."))
       return 
    
    if not is_roleChecked:
        for i in range(len(ctx.guild.roles)):
            print(ctx.guild.roles[i].name)
            if(ctx.guild.roles[i].name == "참여자"):
                role_attend = ctx.guild.roles[i]
                is_roleChecked = True
                break
        
        if not is_roleChecked:   
            await ctx.channel.send(str(ctx.author.mention + "참여자 역할이 서버에 존재하지 않습니다."))
            return
    
    is_init = True
    await ctx.channel.send(str(ctx.author.mention + "초기화 완료."))
    channel = ctx.channel
    await channel.send(f"{channel.name} 에서 갱신합니다.")
    await ctx.message.delete()
    
            
#send today nord war list (1stage)
@bot.command()
async def setTd(ctx):
    global wd ,today_nw, today_nws, full_num, np_tdnw, crnt_num, crnt_usr, is_roleChecked, role_attend, is_init
    
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    
    if not is_roleChecked:
        await ctx.channel.send(str(ctx.author.mention + "참여자 역할이 설정되지 않았습니다."))
        return
    
    if not ctx.author.top_role.permissions.administrator:
        await ctx.channel.send(str(ctx.author.mention + "권한이 없습니다."))
        return
    
    if datetime.now(timezone('Asia/Seoul')).weekday() == 5:
        await ctx.channel.send("오늘은 거점전이 진행되지 않습니다.")
        return
    
    crnt_usr = pd.DataFrame(columns=['name','guild','id'])
    full_num = 0
    np_tdnw = 0
    crnt_num = 0
    today_nw = 0
    today_nws = nw_data[nw_data['date']==wd[datetime.now(timezone('Asia/Seoul')).weekday()]].astype(str)
    
    attends = role_attend.members
    
    for usr in attends:
        await usr.remove_roles(role_attend)
        
    
    print(f"updated Today: {wd[datetime.now(timezone('Asia/Seoul')).weekday()]} ")
    s = [""]
    for i in range(0, today_nws['area'].count()):
        s.append("["+str(i+1)+"]\n")
        s.append(getNwInfoStr(today_nws.iloc[i]) + "\n--------------")
    d = '```'+'\n'.join(s)+'```'
    embed = discord.Embed(title = '금일 거점 진행 지역 리스트', description =d)
    await ctx.channel.send(embed=embed)
    await ctx.message.delete()

@bot.command()
async def setNw(ctx, arg=None):
    global today_nw,today_nws, full_num, np_tdnw, is_init
    
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    
    if not ctx.author.top_role.permissions.administrator:
        await ctx.channel.send(str(ctx.author.mention + " 권한이 없습니다."))
        return;
    
    if datetime.now(timezone('Asia/Seoul')).weekday() == 5:
        await ctx.channel.send("오늘은 거점전이 진행되지 않습니다.")
        return;
    
    if today_nws['date'].iloc[0] != wd[datetime.now(timezone('Asia/Seoul')).weekday()]:     
        await ctx.channel.send("오늘의 거점전이 갱신되지 않았습니다. !setTd를 입력하세요")
        return;
    
    if arg == None:
        await ctx.channel.send("거점명을 입력하세요")
        return;
    
    if not int(arg) > 0:
        await ctx.channel.send(f"ERR")
        return
    
    ag = int(arg) - 1
    today_nws = today_nws.reset_index(inplace=False, drop=True)
    today_nw = today_nws.loc[today_nws.index == ag]
    td_area = today_nw.iloc[0]["area"]
    await ctx.channel.send(content = "@everyone"+f" {td_area}이(가) 오늘의 거점전으로 설정되었습니다", allowed_mentions = discord.AllowedMentions(everyone = True))
    np_tdnw = today_nw.to_numpy()
    full_num = int(np_tdnw[0][2])
    
    s = [""]
    s.append(getNwInfoStr(today_nw.iloc[0]))
    d = '```'+'\n'.join(s)+'```'
    embed = discord.Embed(title = '금일 거점 지역', description =d)
    await ctx.channel.send(embed=embed)
    await ctx.message.delete()
    
@bot.command()
async def 신청(ctx):
    
    global crnt_num, crnt_usr, full_num, is_init, role_attend
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    val1 = '[' not in ctx.author.display_name
    val2 = ']' not in ctx.author.display_name

    val = val1 & val2

    if val:
        await ctx.channel.send(str("잘못된 이름형식입니다. [길드]가문명 으로 서버닉네임을 변경해주세요"))
        return
    
    if (full_num == 0):
        await ctx.channel.send(str(ctx.author.mention + " 금일 거점이 설정되지 않았습니다."))
        return
    
    if (crnt_num == full_num) :
        await ctx.channel.send(str(ctx.author.mention + " 만원!"))
        return
    
    
    usr_name = str(ctx.author.display_name)
    usr_gld = str(ctx.author.display_name)
    usr_name = usr_name.replace(' ', '')
    usr_name = usr_name[usr_name.find(']')+1:]
    usr_gld = usr_gld[usr_gld.find('[')+1:usr_gld.find(']')]
    
    if(crnt_usr['name']==usr_name).any():
        await ctx.channel.send(str(ctx.author.mention + " 이미 참가한 유저입니다"))
        return
    
    print(f"{ctx.author.id}_{usr_name} +  이(가) 참여했습니다.")
    crnt_usr.loc[crnt_num] = [usr_name, usr_gld, ctx.author.id]
    crnt_num = crnt_num+1
    
    await ctx.author.add_roles(role_attend)
    await ctx.channel.send(str(ctx.author.mention + f" 감사! {crnt_num}/{full_num}"))
    await ctx.message.delete()

@bot.command()
async def 참여(ctx):
    global crnt_num, crnt_usr, full_num, is_init, role_attend
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    val1 = '[' not in ctx.author.display_name
    val2 = ']' not in ctx.author.display_name

    val = val1 & val2

    if val:
        await ctx.channel.send(str("잘못된 이름형식입니다. [길드]가문명 으로 서버닉네임을 변경해주세요"))
        return
    
    if (full_num == 0):
        await ctx.channel.send(str(ctx.author.mention + " 금일 거점이 설정되지 않았습니다."))
        return
    
    if (crnt_num == full_num) :
        await ctx.channel.send(str(ctx.author.mention + " 만원!"))
        return
    
    usr_name = str(ctx.author.display_name)
    usr_gld = str(ctx.author.display_name)
    usr_name = usr_name.replace(' ', '')
    usr_name = usr_name[usr_name.find(']')+1:]
    usr_gld = usr_gld[usr_gld.find('[')+1:usr_gld.find(']')]
    
    if(crnt_usr['name']==usr_name).any():
        await ctx.channel.send(str(ctx.author.mention + " 이미 참가한 유저입니다"))
        return
    
    print(f"{ctx.author.id}_{usr_name} +  이(가) 참여했습니다.")
    crnt_usr.loc[crnt_num] = [usr_name, usr_gld, ctx.author.id]
    crnt_num = crnt_num+1
    
    await ctx.author.add_roles(role_attend)
    await ctx.channel.send(str(ctx.author.mention + f" 감사! {crnt_num}/{full_num}"))
    await ctx.message.delete()

@bot.command()
async def 참가(ctx):
    global crnt_num, crnt_usr, full_num, is_init, role_attend
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    val1 = '[' not in ctx.author.display_name
    val2 = ']' not in ctx.author.display_name

    val = val1 & val2

    if val:
        await ctx.channel.send(str("잘못된 이름형식입니다. [길드]가문명 으로 서버닉네임을 변경해주세요"))
        return
    
    if (full_num == 0):
        await ctx.channel.send(str(ctx.author.mention + " 금일 거점이 설정되지 않았습니다."))
        return
    
    if (crnt_num == full_num) :
        await ctx.channel.send(str(ctx.author.mention + " 만원!"))
        return
    
    usr_name = str(ctx.author.display_name)
    usr_gld = str(ctx.author.display_name)
    usr_name = usr_name.replace(' ', '')
    usr_name = usr_name[usr_name.find(']')+1:]
    usr_gld = usr_gld[usr_gld.find('[')+1:usr_gld.find(']')]
    
    if(crnt_usr['name']==usr_name).any():
        await ctx.channel.send(str(ctx.author.mention + " 이미 참가한 유저입니다"))
        return
    
    print(f"{ctx.author.id}_{usr_name} +  이(가) 참여했습니다.")
    crnt_usr.loc[crnt_num] = [usr_name, usr_gld, ctx.author.id]
    crnt_num = crnt_num+1
    
    await ctx.author.add_roles(role_attend)
    await ctx.channel.send(str(ctx.author.mention + f" 감사! {crnt_num}/{full_num}"))
    await ctx.message.delete()

@bot.command()
async def 취소(ctx):
    
    global crnt_num, crnt_usr, full_num, is_init

    
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    
    if (full_num == 0):
        await ctx.channel.send(str(ctx.author.mention + " 금일 거점이 설정되지 않았습니다."))
        return
    
    if crnt_num == 0:
        await ctx.channel.send("리스트가 비어있습니다")
        return

    usr_name = str(ctx.author.display_name)
    usr_name = usr_name.replace(' ', '')
    usr_name = usr_name[usr_name.find(']')+1:]
    usr_n = crnt_usr[crnt_usr['name'] == usr_name].first_valid_index()

    if(len(crnt_usr['name'].str.contains(usr_name)[crnt_usr['name'].str.contains(usr_name)==True]) == 0):
        await ctx.channel.send(str(ctx.author.mention + " 참가하지 않은 유저입니다"))
        return
    
    crnt_usr.drop(usr_n, axis=0, inplace=True)
    crnt_usr.reset_index(inplace=True, drop=True)
    crnt_num = crnt_num-1
    await ctx.author.remove_roles(role_attend)
    await ctx.channel.send(str(ctx.author.mention + f" 잘가시지~ {crnt_num}/{full_num}"))
    await ctx.message.delete()

@bot.command()
async def 참가자(ctx):

    global crnt_usr,crnt_num,full_num, is_init
    
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    output = crnt_usr.to_numpy()
    output = np.sort(output[:,0])
    
    s = [f'                    {crnt_num}/{full_num}                    ']
    for data in output:
        s.append(data)
    d = '```'+'\n'.join(s)+'```'
    embed = discord.Embed(title = '현재 참가자 리스트', description =d)
    await ctx.channel.send(embed=embed)
    await ctx.message.delete()
    
@bot.command()
async def 참여자(ctx):

    global crnt_usr,crnt_num,full_num, is_init
    
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    output = crnt_usr.to_numpy()
    output = np.sort(output[:,0])
    
    s = [f'                    {crnt_num}/{full_num}                    ']
    for data in output:
        s.append(data)
    d = '```'+'\n'.join(s)+'```'
    embed = discord.Embed(title = '현재 참가자 리스트', description =d)
    await ctx.channel.send(embed=embed)
    await ctx.message.delete()

@bot.command()
async def 리스트(ctx):

    global crnt_usr,crnt_num,full_num, is_init
    
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    output = crnt_usr.to_numpy()
    output = np.sort(output[:,0])
    
    s = [f'                    {crnt_num}/{full_num}                    ']
    for data in output:
        s.append(data)
    d = '```'+'\n'.join(s)+'```'
    embed = discord.Embed(title = '현재 참가자 리스트', description =d)
    await ctx.channel.send(embed=embed)
    await ctx.message.delete()

@bot.command()
async def 정보(ctx):

    global today_nw, full_num, is_init
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    if full_num == 0:
        await ctx.channel.send("금일 거점이 설정되지 않았습니다")
        return
    
    s = [""]
    s.append(getNwInfoStr(today_nw.iloc[0]))
    d = '```'+'\n'.join(s)+'```'
    embed = discord.Embed(title = '금일 거점 지역', description =d)
    await ctx.channel.send(embed=embed)
    await ctx.message.delete()

@bot.command()
async def 명령어(ctx):
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return
    
    s = [""]
    s.append("///////관리자용///////")
    s.append("!setTd : 오늘자 거점전 초기화")
    s.append("!setNw 번호 : 오늘자 거점 지역 지정")
    s.append("/////////////////////")
    s.append("!신청, !참여, !참가 : 오늘자 거점 참여 신청")
    s.append("!취소 : 오늘자 거점 참여 취소")
    s.append("!참가자, !참여자, !리스트 : 오늘자 거점 참여자 목록")
    s.append("!드루와 : 보이스채널 미참가자 멘션")
    s.append("!정보 : 오늘자 거점 정보")
    
    d = '```'+'\n'.join(s)+'```'
    embed = discord.Embed(title = '명령어 목록', description =d)
    await ctx.channel.send(embed=embed)
    await ctx.message.delete()

@bot.command()
async def 드루와(ctx):
    vch = 0
    not_in = []
    global crnt_usr
    for server in bot.guilds:
        for ch in server.channels:
            if str(ch.type) == 'voice':
                vch = ch
                break

    for i in range(0, len(crnt_usr)):
        is_found = False
        tp_name = crnt_usr["name"].loc[i]
        tp_id = crnt_usr["id"].loc[i]

        for member in vch.members:
            m_name = str(member.nick)
            m_name = m_name.replace(' ', '')
            m_name = m_name[m_name.find(']')+1:]

            if tp_name == m_name:
                is_found = True
                break
            
        if not is_found:
            tp_usr = ctx.guild.get_member(tp_id)
            not_in.append(tp_usr.mention)
            
    if len(not_in) != 0:
        await ctx.channel.send(content="보이스 들어와요! \n".join(not_in)+"보이스 들어와요! \n",allowed_mentions = discord.AllowedMentions(users= True))
    else:
        await ctx.channel.send(ctx.author.mention+" 전원 착석!")
    await ctx.message.delete()
    
    
    
@bot.command()
async def sayHere(ctx):
    global channel
    if not ctx.author.top_role.permissions.administrator:
        await ctx.channel.send(str(ctx.author.mention + " 권한이 없습니다."))
        return
    
    if not is_init:
        await ctx.channel.send(str(ctx.author.mention + "!init으로 초기화 해주세요"))
        return

    channel = ctx.channel
    await channel.send(f"{channel.name} 에서 갱신합니다.")
    await ctx.message.delete()

@bot.command()
async def sayTest(ctx):
    global channel
    if not ctx.author.top_role.permissions.administrator:
        await ctx.channel.send(str(ctx.author.mention + " 권한이 없습니다."))
        return
    
    await channel.send(f"{channel.name} Test done")
    
@bot.command()
async def dev(ctx):
    global crnt_usr
    print(crnt_usr)

@tasks.loop(seconds=5)
async def every_day():
    global cur_wd, pre_wd, channel, wd ,today_nw, today_nws, full_num, np_tdnw, crnt_num, crnt_usr
    
    pre_wd = cur_wd
    cur_wd = datetime.now(timezone('Asia/Seoul')).weekday()
    
    if pre_wd !=  cur_wd:
        print(f"dayChanged : {datetime.now(timezone('Asia/Seoul'))}")
        if channel != 0:
            await channel.send(f"금일 거점전 자동 초기화 :  {datetime.now(timezone('Asia/Seoul'))}")

            crnt_usr = pd.DataFrame(columns=['name','guild','id'])
            full_num = 0
            np_tdnw = 0
            crnt_num = 0
            today_nw = 0
            today_nws = nw_data[nw_data['date']==wd[datetime.now(timezone('Asia/Seoul')).weekday()]].astype(str)
            print(f"updated Today: {wd[datetime.now(timezone('Asia/Seoul')).weekday()]} ")
            s = [""]
            for i in range(0, today_nws['area'].count()):
                s.append("["+str(i+1)+"]\n")
                s.append(getNwInfoStr(today_nws.iloc[i]) + "\n--------------")
            d = '```'+'\n'.join(s)+'```'
            embed = discord.Embed(title = '금일 1단 거점 진행 지역 리스트', description =d)
            
            attends = role_attend.members
            for usr in attends:
                await usr.remove_roles(role_attend)
            
            if(len(today_nws) == 1):
                today_nw = today_nws.iloc[0]
                tp_nwName = today_nw['area'].str
                await channel.send(content = "@everyone"+f" {tp_nwName} 이(가) 오늘의 거점전으로 자동 설정되었습니다", allowed_mentions = discord.AllowedMentions(everyone = True))
                np_tdnw = today_nw.to_numpy()
                full_num = int(np_tdnw[0][2])
    
                s = [""]
                s.append(getNwInfoStr(today_nw.iloc[0]))
                d = '```'+'\n'.join(s)+'```'
                embed = discord.Embed(title = '금일 거점 지역', description =d)
                await channel.send(embed=embed)
            
            await channel.send(embed=embed)
            
            time.sleep(1)
    
every_day.start() 

try:
    bot.run(TOKEN)
except discord.errors.LoginFailure as e:
    print("Improper token has been passed.")
