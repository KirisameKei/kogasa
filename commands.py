import asyncio
import json

import discord

async def join_vc(message):
    with open("./datas/read_ch.json", mode="r", encoding="utf-8") as f:
        read_ch_dict = json.load(f)

    if not message.guild.id == 585998962050203672: #けい鯖でないなら
        if len(read_ch_dict) >= 3:
            await message.channel.send("参加チャンネルの上限に達しています。")
            return False

    try:
        vc = message.author.voice.channel
    except AttributeError:
        await message.channel.send("VCに接続した状態でコマンドを実行してください")
        return False

    try:
        await vc.connect()
    except discord.errors.ClientException:
        for read_ch in read_ch_dict:
            if read_ch_dict[read_ch] == vc.id:
                await message.channel.send(f"既に参加しています。\n<#{read_ch}>を<#{read_ch_dict[read_ch]}>で読み上げます")
                return False

    read_ch_dict[f"{message.channel.id}"] = vc.id
    with open("./datas/read_ch.json", mode="w", encoding="utf-8") as f:
        read_ch_json = json.dumps(read_ch_dict, indent=4)
        f.write(read_ch_json)

    return True


async def disconnect_vc(message):
    try:
        await message.guild.voice_client.disconnect()
    except AttributeError:
        await message.channel.send("どこにも接続していません")


async def learn_global(message, command):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("このコマンドは影響が大きいため管理者権限のある人のみが使用できます")
        return

    try:
        tango = command.split()[1]
        yomi = command.split()[2]
    except IndexError:
        await message.channel.send("引数が不正です")
        return

    with open("./datas/msg_dictionary_global.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)

    flag = True
    try:
        before = msg_dict[tango.lower()]
    except KeyError:
        flag = False

    msg_dict[tango.lower()] = yomi
    with open("./datas/msg_dictionary_global.json", mode="w", encoding="utf-8") as f:
        msg_json = json.dumps(msg_dict, indent=4, ensure_ascii=False)
        f.write(msg_json)
    
    if flag:
        await message.channel.send(f"global {tango}:{before}を{yomi}で上書きしました")
    else:
        await message.channel.send(f"global {tango}を{yomi}で覚えました")


async def learn_local(message, command):
    try:
        tango = command.split()[1]
        yomi = command.split()[2]
    except IndexError:
        await message.channel.send("引数が不正です")
        return

    with open("./datas/msg_dictionary.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)

    try:
        local_msg_dict = msg_dict[f"{message.guild.id}"]
    except KeyError:
        msg_dict[f"{message.guild.id}"] = {}
        local_msg_dict = msg_dict[f"{message.guild.id}"]

    flag = True
    try:
        before = local_msg_dict[tango.lower()]
    except KeyError:
        flag = False

    local_msg_dict[tango.lower()] = yomi
    with open("./datas/msg_dictionary.json", mode="w", encoding="utf-8") as f:
        msg_json = json.dumps(msg_dict, indent=4, ensure_ascii=False)
        f.write(msg_json)
    
    if flag:
        await message.channel.send(f"{tango}:{before}を{yomi}で上書きしました")
    else:
        await message.channel.send(f"{tango}を{yomi}で覚えました")


async def forget_global(message, command):
    if not message.author.guild_permissions.administrator:
        await message.channel.send("このコマンドは影響が大きいため管理者権限のある人のみが使用できます")
        return

    try:
        tango = command.split()[1]
    except IndexError:
        await message.channel.send("引数が不正です")
        return

    with open("./datas/msg_dictionary_global.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)

    try:
        yomi = msg_dict.pop(tango)
    except KeyError:
        await message.channel.send(f"{tango}は辞書にありません")
        return

    with open("./datas/msg_dictionary_global.json", mode="w", encoding="utf-8") as f:
        msg_json = json.dumps(msg_dict, indent=4, ensure_ascii=False)
        f.write(msg_json)
    await message.channel.send(f"global {tango}={yomi}を忘れました")


async def forget_local(message, command):
    try:
        tango = command.split()[1]
    except IndexError:
        await message.channel.send("引数が不正です")
        return

    with open("./datas/msg_dictionary.json", mode="r", encoding="utf-8") as f:
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

    with open("./datas/msg_dictionary.json", mode="w", encoding="utf-8") as f:
        msg_json = json.dumps(msg_dict, indent=4, ensure_ascii=False)
        f.write(msg_json)
    await message.channel.send(f"{tango}={yomi}を忘れました")


async def set_voice(message, command):
    with open("./datas/voice.json", mode="r", encoding="utf-8") as f:
        voice_dict = json.load(f)

    try:
        user_setting = voice_dict[f"{message.author.id}"]
    except KeyError:
        voice_dict[f"{message.author.id}"] = {}
        user_setting = voice_dict[f"{message.author.id}"]

    if command == "$set_voice":
        user_setting["m"] = "mei_normal.htsvoice"
        voice = user_setting["m"]
        user_setting["r"] = "1.0"
        speed = user_setting["r"]
        user_setting["fm"] = "0.0"
        high = user_setting["fm"]

    else:
        setting_list = command.split()[1:]
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

    with open("./datas/voice.json", mode="w", encoding="utf-8") as f:
        voice_json = json.dumps(voice_dict, indent=4)
        f.write(voice_json)

    await message.channel.send(
        f"{message.author.name}さんの声を\n"
        f"声色: {voice}\n"
        f"速さ: {speed}\n"
        f"高さ: {high}\n"
        "で設定しました"
    )


async def msg_dict(message):
    with open("./datas/msg_dictionary_global.json", mode="r", encoding="utf-8") as f:
        msg_dict = json.load(f)
    msg_json_global = json.dumps(msg_dict, indent=4, ensure_ascii=False)

    with open("./datas/msg_dictionary.json", mode="r", encoding="utf-8") as f:
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


async def help(message, client2):
    """
    ヘルプ表示用関数"""

    with open("./datas/custom_prefix.json", mode="r", encoding="utf-8") as f:
        custom_prefix_dict = json.load(f)

    try:
        custom_prefix = custom_prefix_dict[f"{message.guild.id}"]
    except KeyError:
        custom_prefix = "$"

    help_embed = discord.Embed(
        title=f"{client2.user.name}のヘルプ",
        description=f"「$」は{message.guild.name}のプレフィックス( {custom_prefix} )に変換してください",
        color=0x0088ff
    )

    description = (
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
        "learn, forgetは良識ある使い方を心がけてください。\n"
        "特にglobalは全サーバに影響があります。\n"
    )
    help_embed.add_field(name="コマンド一覧", value=description, inline=False)
    description = (
        "$set_voice単体で声色、速さ、高さをデフォルト値に設定\n"
        "引数```\n"
        "声色: m=(男声, メイ普通, メイ怒り, メイ喜び, メイささやき, メイ悲しみ) defalt: メイ普通\n"
        "速さ: r=(0.3~2.0) defalt: 1.0\n"
        "高さ: fm=(-1.0~1.0) defalt: 0.0```"
        "ex) $set_voice m=メイ喜び fm=0.5 //声色をメイ喜び, 速さを1.0, 高さを0.5に設定"
    )
    help_embed.add_field(name="set_voiceコマンドの詳細", value=description, inline=False)
    await message.channel.send(embed=help_embed)


async def leave_guild(message, client2, command):
    """
    サーバから抜ける"""

    if not message.author.id == 523303776120209408:
        await message.channel.send("何様のつもり？")
        doM_role = message.guild.get_role(616212704818102275)
        await message.author.add_roles(doM_role)
        return

    try:
        guild_id = int(command.split()[1])
        reason = command.split()[2]
    except ValueError:
        await message.channel.send("intキャストできる形で入力してください")
        return
    except IndexError:
        await message.channel.send("サーバから抜ける理由を書いてください")
        return

    guild = client2.get_guild(guild_id)
    embed = discord.Embed(
        title="以下のサーバから抜け、サーバをブラックリスト登録しますか？",
        description="はい(離脱&ブラックリスト登録): 👍\nはい(離脱のみ): 👋\nいいえ(ミス): 👎",
        color=0xff0000
    )
    embed.set_author(name=guild.name, icon_url=guild.icon.url)
    embed.set_footer(text=guild.owner.name, icon_url=guild.owner.avatar.url)
    msg = await message.channel.send(embed=embed)
    await msg.add_reaction("👍")
    await msg.add_reaction("👋")
    await msg.add_reaction("👎")
    def check(reaction, user):
        return user == message.author and (str(reaction.emoji) == "👍" or str(reaction.emoji) == "👋" or str(reaction.emoji) == "👎")
    try:
        reply = await client2.wait_for("reaction_add", check=check, timeout=60)
    except asyncio.TimeoutError:
        await message.channel.send("タイムアウトしました。最初からやり直してください")
        return

    else:
        if str(reply[0].emoji) == "👎":
            await message.channel.send("キャンセルしました")
            return

        if guild.owner.id == 523303776120209408:
            await message.channel.send("あんた正気か？")
            return

        flag = False
        for ch in guild.text_channels:
            try:
                await ch.send(f"{client2.user.name}はこのサーバを抜けます\nReason: {reason}")
                flag = True
                break
            except discord.errors.Forbidden:
                pass

        if not flag:
            try:
                await guild.owner.send(f"{client2.user.name}は{guild.name}を抜けます\nReason: {reason}")
            except discord.errors.Forbidden:
                await message.channel.send(f"{guild.name}に通知できませんでした")

        await guild.leave()
        await message.channel.send(f"{guild.name}から退出しました")

        if str(reply[0].emoji) == "👋":
            return

        with open("./datas/ban_server.json", mode="r", encoding="utf-8") as f:
            ban_server_dict = json.load(f)

        ban_server_dict[f"{guild_id}"] = [guild.name, guild.owner.name, guild.owner.id]

        ban_server_json = json.dumps(ban_server_dict, indent=4, ensure_ascii=False)
        with open("./datas/ban_server.json", mode="w", encoding="utf-8") as f:
            f.write(ban_server_json)


async def change_prefix(message):
    """
    カスタムプレフィックスの変更"""

    if message.author.bot:
        return

    if not message.author.guild_permissions.administrator:
        await message.channel.send("このコマンドは管理者のみが使用できます")
        return

    prefix = message.content.split()[1]
    if "\\" in prefix:
        await message.channel.send("表示がややこしくなるためバックスラッシュを含むプレフィックスは使用できません")
        return
    elif message.mentions:
        await message.channel.send("メンションをプレフィックスに含むことはできません")
        return

    with open("./datas/custom_prefix.json", mode="r", encoding="utf-8") as f:
        custom_prefix_dict = json.load(f)

    custom_prefix_dict[f"{message.guild.id}"] = prefix

    custom_prefix_json = json.dumps(custom_prefix_dict, indent=4, ensure_ascii=False)
    with open("./datas/custom_prefix.json", mode="w", encoding="utf-8") as f:
        f.write(custom_prefix_json)

    await message.channel.send(f"{message.guild.name}でのプレフィックスを「{prefix}」に設定しました")


async def glist(message, client2):
    """
    bot参加鯖の一覧を表示"""

    if not message.guild.id == 585998962050203672:
        await message.channel.send("このコマンドはけいの実験サーバでのみ使用可能です")
        return

    text = ""
    for guild in client2.guilds:
        text += f"{guild.name}\n{guild.id}\n{guild.owner}\n\n"
    text += f"以上{len(client2.guilds)}鯖"
    await message.channel.send(embed=discord.Embed(title="参加鯖一覧", description=text))