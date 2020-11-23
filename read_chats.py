import asyncio
import datetime
import json
import os
import subprocess
import time
import traceback

import discord
import ffmpeg
import requests
from discord.ext import tasks

intents = discord.Intents.all()
client2 = discord.Client(intents=intents)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

where_from = os.getenv("where_from")

flag = False

def unexpected_error():
    """
    予期せぬエラーが起きたときの対処
    エラーメッセージ全文と発生時刻を通知"""

    now = datetime.datetime.now().strftime("%H:%M") #今何時？
    error_msg = f"```\n{traceback.format_exc()}```" #エラーメッセージ全文
    error_content = {
        "content": "<@523303776120209408>", #けいにメンション
        "avatar_url": "https://cdn.discordapp.com/attachments/644880761081561111/703088291066675261/warning.png",
        "embeds": [ #エラー内容・発生時間まとめ
            {
                "title": "エラーが発生しました",
                "description": error_msg,
                "color": 0xff0000,
                "footer": {
                    "text": now
                }
            }
        ]
    }
    error_notice_webhook_url = os.getenv("error_notice_webhook")
    requests.post(error_notice_webhook_url, json.dumps(error_content), headers={"Content-Type": "application/json"}) #エラーメッセをウェブフックに投稿


@client2.event
async def on_ready():
    with open("read_ch.json", mode="w", encoding="utf-8") as f:
        f.write(json.dumps({}, indent=4))
    ch = client2.get_channel(595072339545292804)
    await ch.send(f"{client2.user.name}がログインしました(from: {where_from})")


@client2.event
async def on_message(message):
    try:
        if client2.user in message.mentions:
            if not message.author.bot:
                await message.channel.send(where_from)

        if message.guild is None:
            if message.author.bot:
                return
            for i in range(5):
                await message.channel.send("DMに来るんじゃねぇバカたれが！")
            return
        if message.content == "$dc":
            try:
                await message.guild.voice_client.disconnect()
            except AttributeError:
                await message.channel.send("どこにも接続していません")

        elif message.content == "$join":
            with open("read_ch.json", mode="r", encoding="utf-8") as f:
                read_ch_dict = json.load(f)

            if len(read_ch_dict) >= 3:
                await message.channel.send("参加チャンネルの上限に達しています。")
                return

            try:
                vc = message.author.voice.channel
            except AttributeError:
                await message.channel.send("VCに接続した状態でコマンドを実行してください")
                return

            try:
                await vc.connect()
            except discord.errors.client2Exception:
                for read_ch in read_ch_dict:
                    if read_ch_dict[read_ch] == vc.id:
                        await message.channel.send(f"既に参加しています。\n<#{read_ch}>を<#{read_ch_dict[read_ch]}>で読み上げます")
                        return

            read_ch_dict[f"{message.channel.id}"] = vc.id
            with open("read_ch.json", mode="w") as f:
                read_ch_json = json.dumps(read_ch_dict, indent=4)
                f.write(read_ch_json)

            global flag
            if not flag:
                flag = True
                await play_voice(client2)

        elif message.content.startswith("$learn_global "):
            await learn_global(message)

        elif message.content.startswith("$learn "):
            await learn(message)

        elif message.content.startswith("$forget_global "):
            await forget_global(message)

        elif message.content.startswith("$forget "):
            await forget(message)

        elif message.content.startswith("$set_voice"):
            await set_voice(message)

        elif message.content == "$msg_dict":
            await msg_dict_func(message)

        elif message.content == "$help":
            await message.channel.send(
                "```\n"
                "$join             : 実行したチャンネルのメッセージを読み上げます\n"
                "$dc               : botをVCから切断します\n"
                "$learn_global A B : AをBとして読みます。管理者権限持ちのみ\n"
                "$learn A B        : AをBとして読みます。実行サーバ内でのみ有効\n"
                "$forget_global A  : Aを忘れます。管理者権限持ちのみ\n"
                "$forget A         : Aを忘れます。実行サーバ内でのみ有効\n"
                "$msg_dict         : 現在の辞書を表示します\n"
                "$set_voice        : 後述\n"
                "$help             : これを表示します```\n"
                "learn, forgetは良識ある使い方を心がけてください。"
                "特にglobalは全サーバに影響があります。\n\n"
                "$set_voice単体で声色、速さ、高さをデフォルト値に設定\n"
                "引数```\n"
                "声色: m=(男声, メイ普通, メイ怒り, メイ喜び, メイささやき, メイ悲しみ) defalt: メイ普通\n"
                "速さ: r=(0.3~2.0) defalt: 1.0\n"
                "高さ: fm=(-1.0~1.0) defalt: 0.0```"
                "ex) $set_voice m=メイ喜び fm=0.5 //声色をメイ喜び, 速さを1.0, 高さを0.5に設定"
            )

        else:
            with open("read_ch.json", mode="r") as f:
                read_ch_dict = json.load(f)

            if not f"{message.channel.id}" in read_ch_dict.keys():
                return

            if message.author.bot:
                return

            msg = message.clean_content.lower()

            if "http" in msg:
                return

            if "\n" in msg:
                msg = msg.replace("\n","")
            if "w" in msg:
                msg = msg.replace("w","わら")
            if "ｗ" in msg:
                msg = msg.replace("ｗ","わら")

            with open("msg_dictionary_global.json", mode="r", encoding="utf-8") as f:
                msg_dict = json.load(f)
            for tango in msg_dict.keys():
                if tango in msg:
                    msg = msg.replace(tango, msg_dict[tango])

            with open("msg_dictionary.json", mode="r", encoding="utf-8") as f:
                guild_msg_dict = json.load(f)
            msg_dict = guild_msg_dict[f"{message.guild.id}"]
            for tango in msg_dict.keys():
                if tango in msg:
                    msg = msg.replace(tango, msg_dict[tango])

            if len(msg) > 35:
                msg = msg[0:35] + "以下略"

            with open("voice.json", mode="r", encoding="utf-8") as f:
                voice_dict = json.load(f)

            try:
                user_setting = voice_dict[f"{message.author.id}"]
            except KeyError:
                voice = "mei_normal.htsvoice"
                speed = "1.0"
                high = "0.0"
            else:
                try:
                    voice = user_setting["m"]
                except KeyError:
                    user_setting["m"] = "mei_normal.htsvoice"
                    voice = user_setting["m"]

                try:
                    speed = user_setting["r"]
                except KeyError:
                    user_setting["r"] = "1.0"
                    speed = user_setting["r"]

                try:
                    high = user_setting["fm"]
                except KeyError:
                    user_setting["fm"] = "0.0"
                    high = user_setting["fm"]

            with open("message.json", mode="r", encoding="utf-8") as f:
                message_list = json.load(f)

            message_list.append(
                [
                    f"{message.channel.id}",
                    f"-m /home/kirisamekei/read/voices/{voice} -r {speed} -fm {high}",
                    msg
                ]
            )

            with open("message.json", mode="w", encoding="utf-8") as f:
                message_json = json.dumps(message_list, indent=4, ensure_ascii=False)
                f.write(message_json)

    except:
        unexpected_error()


@client2.event
async def on_voice_state_update(member, before, after):
    try:
        global flag
        if before.channel is None:
            return

        if member.id == client2.user.id:
            if after.channel is None:
                if len(client2.voice_clients) == 0:
                    flag = False
                with open("read_ch.json", mode="r", encoding="utf-8") as f:
                    read_ch_dict = json.load(f)
                for read_ch in read_ch_dict:
                    if before.channel.id == read_ch_dict[read_ch]:
                        del read_ch_dict[read_ch]
                        break
                with open("read_ch.json", mode="w", encoding="utf-8") as f:
                    read_ch_json = json.dumps(read_ch_dict, indent=4)
                    f.write(read_ch_json)

        if len(before.channel.members) == 1:
            if before.channel.members[0].id == client2.user.id:
                await member.guild.voice_client.disconnect()
                with open("read_ch.json", mode="r", encoding="utf-8") as f:
                    read_ch_dict = json.load(f)
                for read_ch in read_ch_dict:
                    if before.channel.id == read_ch_dict[read_ch]:
                        await client2.get_channel(int(read_ch)).send("誰もいなくなったので読み上げを終了します")
                        if len(client2.voice_clients) == 0:
                            flag = False
                        break

    except:
        unexpected_error()

    """
    if member.guild.id == 585998962050203672 and before.channel != after.channel:#けい鯖
    #if member.guild.id == 604945424922574848 and before.channel != after.channel:#いろは鯖
        if member.id == 594396830071259154:
            return
        #alert_channel = client2.get_channel(648533216734609421)#VC雑談(いろは鯖)
        #alert_channel = client2.get_channel(630606928455794698)#vc聞き専用
        alert_channel = client2.get_channel(700928302545764412)#開発垂れ流し聞き専用
        if before.channel is None: 
            await alert_channel.send(f"{member.name}が参加しました。")
        elif after.channel is None: 
            await alert_channel.send(f"{member.name}が退出しました。")"""


async def learn_global(message):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("このコマンドは影響が大きいため管理者権限のある人のみが使用できます")
        return

    try:
        tango = message.content.split()[1]
        yomi = message.content.split()[2]
    except IndexError:
        await message.channel.send("引数が不正です")
        return

    with open("msg_dictionary_global.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)

    try:
        flag = True
        before = msg_dict[tango.lower()]
    except KeyError:
        flag = False

    msg_dict[tango.lower()] = yomi
    with open("msg_dictionary_global.json", mode="w", encoding="utf-8") as f:
        msg_json = json.dumps(msg_dict, indent=4, ensure_ascii=False)
        f.write(msg_json)
    
    if flag:
        await message.channel.send(f"global {tango}:{before}を{yomi}で上書きしました")
    else:
        await message.channel.send(f"global {tango}を{yomi}で覚えました")


async def learn(message):
    try:
        tango = message.content.split()[1]
        yomi = message.content.split()[2]
    except IndexError:
        await message.channel.send("引数が不正です")
        return

    with open("msg_dictionary.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)

    try:
        local_msg_dict = msg_dict[f"{message.guild.id}"]
    except KeyError:
        msg_dict[f"{message.guild.id}"] = {}
        local_msg_dict = msg_dict[f"{message.guild.id}"]

    try:
        flag = True
        before = local_msg_dict[tango.lower()]
    except KeyError:
        flag = False

    local_msg_dict[tango.lower()] = yomi
    with open("msg_dictionary.json", mode="w", encoding="utf-8") as f:
        msg_json = json.dumps(msg_dict, indent=4, ensure_ascii=False)
        f.write(msg_json)
    
    if flag:
        await message.channel.send(f"{tango}:{before}を{yomi}で上書きしました")
    else:
        await message.channel.send(f"{tango}を{yomi}で覚えました")


async def forget_global(message):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("このコマンドは影響が大きいため管理者権限のある人のみが使用できます")
        return

    try:
        tango = message.content.split()[1]
    except IndexError:
        await message.channel.send("引数が不正です")
        return

    with open("msg_dictionary_global.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)

    try:
        yomi = msg_dict.pop(tango)
    except KeyError:
        await message.channel.send(f"{tango}は辞書にありません")
        return

    with open("msg_dictionary_global.json", mode="w", encoding="utf-8") as f:
        msg_json = json.dumps(msg_dict, indent=4, ensure_ascii=False)
        f.write(msg_json)
    await message.channel.send(f"global {tango}={yomi}を忘れました")


async def forget(message):
    try:
        tango = message.content.split()[1]
    except IndexError:
        await message.channel.send("引数が不正です")
        return

    with open("msg_dictionary.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)

    try:
        local_msg_dict = msg_dict[f"{message.guild.id}"]
    except KeyError:
        msg_dict[f"{message.guild.id}"] = {}
        local_msg_dict = msg_dict[f"{message.guild.id}"]

    try:
        yomi = local_msg_dict.pop(tango)
    except KeyError:
        await message.channel.send(f"{tango}は辞書にありません")
        return

    with open("msg_dictionary.json", mode="w", encoding="utf-8") as f:
        msg_json = json.dumps(msg_dict, indent=4, ensure_ascii=False)
        f.write(msg_json)
    await message.channel.send(f"{tango}={yomi}を忘れました")


async def set_voice(message):
    with open("voice.json", mode="r", encoding="utf-8") as f:
        voice_dict = json.load(f)

    try:
        user_setting = voice_dict[f"{message.author.id}"]
    except KeyError:
        voice_dict[f"{message.author.id}"] = {}
        user_setting = voice_dict[f"{message.author.id}"]

    if message.content == "$set_voice":
        user_setting["m"] = "mei_normal.htsvoice"
        voice = user_setting["m"]
        user_setting["r"] = "1.0"
        speed = user_setting["r"]
        user_setting["fm"] = "0.0"
        high = user_setting["fm"]

    else:
        setting_list = message.content.split()[1:]
        for setting in setting_list:
            if setting.startswith("m="):
                voice = setting.replace("m=", "")
                voice_data = [
                    "男声",
                    "メイ普通",
                    "メイ怒り",
                    "メイ喜び",
                    "メイささやき",
                    "メイ悲しみ"
                ]
                if voice in voice_data:
                    voice = voice.replace("男声", "man_nomal.htsvoice")\
                                .replace("メイ普通", "mei_normal.htsvoice")\
                                .replace("メイ怒り", "mei_angry.htsvoice")\
                                .replace("メイ喜び", "mei_happy.htsvoice")\
                                .replace("メイささやき", "mei_bashful.htsvoice")\
                                .replace("メイ悲しみ", "mei_sad.htsvoice")
                    user_setting["m"] = voice
                else:
                    hint = ", ".join(voice_data)
                    await message.channel.send(f"m(声色)```\n{hint}\ndefalt=メイ普通```")

            elif setting.startswith("r="):
                speed = setting.replace("r=", "")
                try:
                    speed = float(speed)
                except ValueError:
                    await message.channel.send(f"r(スピード)```\n0.3~2.0\ndefalt=1.0```")
                else:
                    speed = round(speed, 1)
                    if speed >= 0.3 and speed <= 2.0:
                        user_setting["r"] = f"{speed}"
                    else:
                        await message.channel.send(f"r(スピード)```\n0.3~2.0\ndefalt=1.0```")

            elif setting.startswith("fm="):
                high = setting.replace("fm=", "")
                try:
                    high = float(high)
                except ValueError:
                    await message.channel.send(f"fm(高さ)```\n-1.0~1.0\ndefalt=0.0```")
                else:
                    high = round(high, 1)
                    if high >= -1.0 and high <= 1.0:
                        user_setting["fm"] = f"{high}"
                    else:
                        await message.channel.send(f"fm(高さ)```\n-1.0~1.0\ndefalt=0.0```")

            else:
                await message.channel.send(
                    "引数```\n"
                    "声色: m=(男声, メイ普通, メイ怒り, メイ喜び, メイささやき, メイ悲しみ) defalt: メイ普通\n"
                    "速さ: r=(0.3~2.0) defalt: 1.0\n"
                    "高さ: fm=(-1.0~1.0) defalt: 0.0```"
                )

        try:
            voice = user_setting["m"]
        except KeyError:
            user_setting["m"] = "mei_normal.htsvoice"
            voice = user_setting["m"]

        try:
            speed = user_setting["r"]
        except KeyError:
            user_setting["r"] = "1.0"
            speed = user_setting["r"]

        try:
            high = user_setting["fm"]
        except KeyError:
            user_setting["fm"] = "0.0"
            high = user_setting["fm"]

    with open("voice.json", mode="w", encoding="utf-8") as f:
        voice_json = json.dumps(voice_dict, indent=4)
        f.write(voice_json)

    await message.channel.send(
        f"{message.author.name}さんの声を\n"
        f"声色: {voice}\n"
        f"速さ: {speed}\n"
        f"高さ: {high}\n"
        "で設定しました"
    )


async def msg_dict_func(message):
    with open("msg_dictionary_global.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)
    msg_json_global = json.dumps(msg_dict, indent=4, ensure_ascii=False)

    with open("msg_dictionary.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)
    try:
        msg_dict_local = msg_dict[f"{message.guild.id}"]
    except KeyError:
        msg_dict_local = {}
    msg_json_local = json.dumps(msg_dict_local, indent=4, ensure_ascii=False)
    await message.channel.send(
        f"global```json\n{msg_json_global}```\nlocal```json\n{msg_json_local}```"
        "globalとlocalで被っているものがある場合localが優先されます"
    )


async def play_voice(client2):
    try:
        global flag
        while flag:
            with open("message.json", mode="r", encoding="utf-8") as f:
                message_list = json.load(f)

            try:
                channel = client2.get_channel(int(message_list[0][0]))
            except IndexError:
                pass
            else:
                if not channel.guild.voice_client.is_playing():
                    try:
                        with open("input.txt", mode="w", encoding="utf-8") as f:
                            f.write(message_list[0][2])
                        cmd = f"open_jtalk -x /var/lib/mecab/dic/open-jtalk/naist-jdic {message_list[0][1]} -ow output.wav input.txt"
                        subprocess.run(cmd, shell=True)
                    except UnicodeEncodeError:
                        pass
                    else:
                        path = "/usr/bin/ffmpeg"
                        source = discord.FFmpegPCMAudio(executable=path, source="output.wav")
                        channel.guild.voice_client.play(source)

                        del message_list[0]

                        with open("message.json", mode="w", encoding="utf-8") as f:
                            message_json = json.dumps(message_list, indent=4, ensure_ascii=False)
                            f.write(message_json)

            await asyncio.sleep(1)

    except:
        unexpected_error()


client2.run(os.getenv("discord_bot_token_2"))