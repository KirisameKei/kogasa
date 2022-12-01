import asyncio
import datetime
import json
import os
import subprocess
import traceback

import discord
import jaconv
import requests

import commands

os.chdir(os.path.dirname(os.path.abspath(__file__)))
client2 = discord.Client(intents=discord.Intents.all())

where_from = os.getenv("where_from")
error_notice_webhook_url = os.getenv("error_notice_webhook")
is_client2_in_vc = False
message_list = []

def unexpected_error(msg=None):
    """
    予期せぬエラーが起きたときの対処
    エラーメッセージ全文と発生時刻を通知"""

    try:
        if msg is not None:
            content = (
                f"{msg.author}\n"
                f"{msg.content}\n"
                f"{msg.channel.name}\n"
            )
        else:
            content = ""
    except:
        unexpected_error()
        return

    now = datetime.datetime.now().strftime("%H:%M") #今何時？
    error_msg = f"```\n{traceback.format_exc()}```" #エラーメッセージ全文
    error_content = {
        "content": "<@523303776120209408>", #けいにメンション
        "avatar_url": "https://cdn.discordapp.com/attachments/644880761081561111/703088291066675261/warning.png",
        "embeds": [ #エラー内容・発生時間まとめ
            {
                "title": "エラーが発生しました",
                "description": content + error_msg,
                "color": 0xff0000,
                "footer": {
                    "text": now
                }
            }
        ]
    }
    requests.post(error_notice_webhook_url, json.dumps(error_content), headers={"Content-Type": "application/json"}) #エラーメッセをウェブフックに投稿


@client2.event
async def on_ready():
    try:
        login_notice_ch = client2.get_channel(595072339545292804)
        with open("./datas/version.txt", mode="r", encoding="utf-8") as f:
            version = f.read()
        await login_notice_ch.send(f"{client2.user.name}がログインしました(from: {where_from})\n{os.path.basename(__file__)}により起動\nversion: {version}")

    except:
        unexpected_error()


@client2.event
async def on_message(message):
    if message.content == "$bot_stop":
        if message.guild is None:
            await message.channel.send("このコマンドはけいの実験サーバでのみ使用可能です")
            return
        kei_ex_guild = client2.get_guild(585998962050203672)
        if message.guild != kei_ex_guild:
            await message.channel.send("このコマンドはけいの実験サーバでのみ使用可能です")
            return
        can_bot_stop_role = kei_ex_guild.get_role(707570554462273537)
        if not can_bot_stop_role in message.author.roles:
            await message.channel.send("何様のつもり？")
            doM_role = message.guild.get_role(616212704818102275)
            await message.author.add_roles(doM_role)
            return

        await client2.close()
        now = datetime.datetime.now().strftime(r"%Y年%m月%d日　%H:%M")
        stop_msg = f"{message.author.mention}により{client2.user.name}が停止させられました"
        main_content = {
            "username": "BOT STOP",
            "avatar_url": "https://cdn.discordapp.com/attachments/644880761081561111/703088291066675261/warning.png",
            "content": "<@523303776120209408>",
            "embeds": [
                {
                    "title": "botが停止させられました",
                    "description": stop_msg,
                    "color": 0xff0000,
                    "footer": {
                        "text": now
                    }
                }
            ]
        }
        requests.post(error_notice_webhook_url, json.dumps(main_content), headers={"Content-Type": "application/json"}) #エラーメッセをウェブフックに投稿
        return

    if client2.user in message.mentions:
        await message.channel.send(f"{where_from}\n{os.path.basename(__file__)}")

    try:
        if message.guild is None:
            return

        if message.content.startswith("#") or message.content.startswith("//") or \
            (message.clean_content.startswith("/*") and message.clean_content.endswith("*/")):
            return

        command = None
        if message.guild is not None:
            with open("./datas/custom_prefix.json", mode="r", encoding="utf-8") as f:
                custom_frefix_dict = json.load(f)
            try:
                prefix = custom_frefix_dict[f"{message.guild.id}"]
            except KeyError:
                if not message.guild is None:
                    custom_frefix_dict[f"{message.guild.id}"] = "$"
                    custom_frefix_json = json.dumps(custom_frefix_dict, indent=4, ensure_ascii=False)
                    with open("./datas/custom_prefix.json", mode="w", encoding="utf-8") as f:
                        f.write(custom_frefix_json)
                prefix = "$"

        if message.content.startswith(prefix):
            prefix_length = len(prefix)
            command = message.content[prefix_length:]
            if command[0] == " ":
                command = command[1:]

        if message.content.startswith(prefix):
            if command == "join":
                is_connect_vc_sucessed = await commands.join_vc(message)
                if is_connect_vc_sucessed:
                    global is_client2_in_vc
                    if not is_client2_in_vc:
                        is_client2_in_vc = True
                        await play_voice(client2)

            elif command == "disconnect" or command == "dc":
                await commands.disconnect_vc(message)

            elif command.startswith("learn_global "):
                await commands.learn_global(message, command)

            elif command.startswith("learn "):
                await commands.learn_local(message, command)

            elif command.startswith("forget_global "):
                await commands.forget_global(message, command)

            elif command.startswith("forget "):
                await commands.forget_local(message, command)

            elif command.startswith("set_voice"):
                await commands.set_voice(message, command)

            elif command == "msg_dict":
                await commands.msg_dict(message)

            elif command.startswith("prefix "):
                await commands.change_prefix(message)

            elif command == "glist":
                await commands.glist(message, client2)

            elif command == "help":
                if prefix != "$":
                    await commands.help(message, client2)
    
            elif command.startswith("leave_guild "):
                await commands.leave_guild(message, client2, command)

            return #コマンド系は音声読み上げの方に流さない

        if message.content.startswith("$help"): #カスタムプレフィックスを忘れた人の救済用
            await commands.help(message, client2)
            return #コマンド系は音声読み上げの方に流さない

        if not is_client2_in_vc:
            return

        if message.author.bot:
            return

        if message.content.startswith(prefix):
            return

        with open("./datas/read_ch.json", mode="r", encoding="utf-8") as f:
            read_ch_dict = json.load(f)

        if not f"{message.channel.id}" in read_ch_dict.keys():
            return

        msg = message.clean_content.lower()

        if "http" in msg:
            return

        with open("./datas/msg_dictionary.json", mode="r", encoding="utf-8") as f:
            guild_msg_dict = json.load(f)

        try:
            msg_dict = guild_msg_dict[f"{message.guild.id}"]
        except KeyError:
            pass
        else:
            for tango in msg_dict.keys():
                if tango in msg:
                    msg = msg.replace(tango, msg_dict[tango])

        with open("./datas/msg_dictionary_global.json", mode="r", encoding="utf-8") as f:
            msg_dict = json.load(f)
        for tango in msg_dict.keys():
            if tango in msg:
                msg = msg.replace(tango, msg_dict[tango])

        if len(msg) > 35:
            msg = msg[0:35] + "以下略"

        with open("./datas/voice.json", mode="r", encoding="utf-8") as f:
            voice_dict = json.load(f)

        if "\n" in msg:
            msg = msg.replace("\n","")
        if "w" in msg:
            msg = msg.replace("w","わら")
        if "ｗ" in msg:
            msg = msg.replace("ｗ","わら")

        msg = jaconv.alphabet2kana(msg)

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
                voice = "mei_normal.htsvoice"

            try:
                speed = user_setting["r"]
            except KeyError:
                speed = "1.0"

            try:
                high = user_setting["fm"]
            except KeyError:
                high = "0.0"

        if os.path.isfile("/home/kirisamekei/read/voices/mei_normal.htsvoice"): #リモートなら
            cmd = f"-m /home/kirisamekei/read/voices/{voice} -r {speed} -fm {high}"
        else: #ローカルなら
            cmd = f"-m C:\\Users\\hayab\\OneDrive\\bots_and_python\\discord\\client bot\\new-kogasa\\voices\\{voice} -r {speed} -fm {high}"

        global message_list
        message_list.append(
            [
                message.channel.id,
                cmd,
                msg
            ]
        )

    except:
        unexpected_error(msg=message)


@client2.event
async def on_guild_join(guild):
    try:
        with open("./datas/ban_server.json", mode="r", encoding="utf-8") as f:
            ban_server_list = json.load(f)

        for ban_server in ban_server_list:
            if guild.id == ban_server[0]:
                await guild.leave()
                return

        for ch in guild.text_channels:
            description = (
                f"初めましての方は初めまして、そうでない方はまたお会いしましたね。KirisameKei(mcid: kei_3104)制作の{client2.user.name}です。\n"
                f"このbotを{guild.name}に導入していただきありがとうございます。\n"
                "皆様にお願いしたいことがあります。このbotに極度に負荷をかけるような行為をしないでください。\n"
                "バグ・不具合・要望等ありましたらけい#3104のDMか以下で紹介するサーバにお願いします。\n"
                "[けいのうぇぶさいと](https://www.kei-3104.com)から私に匿名のメッセージを送れます。\n"
                "デフォルトプレフィックスは「$」、$helpでコマンドの一覧を見ることができます。\n"
                "最後に[私のサーバ](https://discord.gg/nrvMKBT)を宣伝・紹介させてください。"
                "このbotについてもっと知りたい、けいの活動に興味がある、理由は何でも構いません。ぜひ見ていってください。"
                "このサーバで本botのサポートも行っております"
            )
            self_introduction_embed = discord.Embed(title="よろしくお願いします！", description=description, color=0x00ffff)
            kei = client2.get_user(523303776120209408)
            self_introduction_embed.set_footer(text="←KirisameKei(作者)", icon_url=kei.avatar_url_as(format="png"))

            try:
                await ch.send(embed=self_introduction_embed)
                break
            except discord.errors.Forbidden:
                pass

        guild_join_embed = discord.Embed(
            title="╋",
            description=f"{client2.user.name}が{guild.name}に参加しました",
            color=0xfffffe
        )
        guild_join_embed.set_author(name=client2.user.name,icon_url=client2.user.avatar_url_as(format="png"))
        guild_join_embed.set_footer(text=guild.name, icon_url=guild.icon_url_as(format="png"))
        join_leave_notice_ch = client2.get_channel(709307324170240079)
        await join_leave_notice_ch.send(embed=guild_join_embed)

    except:
        unexpected_error()


@client2.event
async def on_guild_remove(guild):
    try:
        guild_remove_embed = discord.Embed(
            title="━",
            description=f"{client2.user.name}が{guild.name}から退出しました",
            color=0xff0000
        )
        guild_remove_embed.set_author(name=client2.user.name, icon_url=client2.user.avatar_url_as(format="png"))
        guild_remove_embed.set_footer(text=guild.name, icon_url=guild.icon_url_as(format="png"))
        join_leave_notice_ch = client2.get_channel(709307324170240079)
        await join_leave_notice_ch.send(embed=guild_remove_embed)

    except:
        unexpected_error()


@client2.event
async def on_voice_state_update(member, before, after):
    try:
        global is_client2_in_vc
        if before.channel is None:
            return

        if member.id == client2.user.id:
            if after.channel is None:
                if len(client2.voice_clients) == 0:
                    is_client2_in_vc = False

                with open("./datas/read_ch.json", mode="r", encoding="utf-8") as f:
                    read_ch_dict = json.load(f)

                for read_ch in read_ch_dict:
                    if before.channel.id == read_ch_dict[read_ch]:
                        del read_ch_dict[read_ch]
                        break

                read_ch_json = json.dumps(read_ch_dict, indent=4)
                with open("./datas/read_ch.json", mode="w", encoding="utf-8") as f:
                    f.write(read_ch_json)

        if len(before.channel.members) == 1:
            if before.channel.members[0].id == client2.user.id:
                await member.guild.voice_client.disconnect()
                with open("./datas/read_ch.json", mode="r", encoding="utf-8") as f:
                    read_ch_dict = json.load(f)

                for read_ch in read_ch_dict:
                    if before.channel.id == read_ch_dict[read_ch]:
                        await client2.get_channel(int(read_ch)).send("誰もいなくなったので読み上げを終了します")
                        if len(client2.voice_clients) == 0:
                            is_client2_in_vc = False
                        break

    except:
        unexpected_error()


async def play_voice(client2):
    try:
        global is_client2_in_vc
        global message_list
        while is_client2_in_vc:
            try:
                channel = client2.get_channel(message_list[0][0])
            except IndexError:
                await asyncio.sleep(1)
                continue

            if not channel.guild.voice_client.is_playing():
                try:
                    with open("input.txt", mode="w", encoding="utf-8") as f:
                        f.write(message_list[0][2])

                    if os.path.isdir("/var/lib/mecab/dic/open-jtalk/naist-jdic"):
                        cmd = f"open_jtalk -x /var/lib/mecab/dic/open-jtalk/naist-jdic {message_list[0][1]} -ow output.wav input.txt"
                    else:
                        cmd = f"open_jtalk -x C:\\open_jtalk\\bin\\dic {message_list[0][1]} -ow output.wav input.txt"
                        print(cmd)

                    subprocess.run(cmd, shell=True)
                except UnicodeEncodeError:
                    await asyncio.sleep(1)
                    continue

                if os.path.isfile("/usr/bin/ffmpeg"):
                    path = "/usr/bin/ffmpeg"
                else:
                    #path = "C:\\Program Files\\ffmpeg-20200306-cfd9a65-win64-static\\ffmpeg-20200306-cfd9a65-win64-static\\bin\\ffmpeg.exe"
                    path = "ffmpeg"
                source = discord.FFmpegPCMAudio(executable=path, source="output.wav")
                channel.guild.voice_client.play(source)

                del message_list[0]

    except:
        unexpected_error()



client2.run(os.getenv("discord_bot_token_2"))