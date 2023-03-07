import re
import time
from asyncio import sleep
from .model.gino_db import init

import nonebot
from nonebot import Driver, logger
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, Bot, ActionFailed
from nonebot.exception import FinishedException
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, ArgPlainText, ArgStr
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State

from services import db_context
from .service import game_handler, player_handler, skill_handler, battle_handler, adv_handler
from .service.adv_handler import get_user_status, adv_time_pass, go_outside
from .service.battle_handler import query_battle_log, foo
from .service.forge_handler import get_forge_list, handle_forge, get_forge_num
from .service.game_handler import load_world_data, WorldInfo, Compose
from .service.look_handler import handle_look_all
from .service.mission_handler import get_available_mission, handle_receive_mission, get_submitable_mission, \
    handle_submit_mission, handle_look_mission, handle_del_mission, get_short_submitable_mission
from .service.player_handler import register_new_player, get_player, get_user_status_str, handle_set_stay, \
    handle_show_bag
from .model.player_model import PlayerDB
from .service.shop_handler import get_store_list, buy_item_handle
from .service.skill_handler import get_skill_list, check_skill_exist, get_equip_skill_list, unequip_skill
from .service.use_handler import get_usable_item, use_item_handler
from .utils import get_image, send_group_msg, send_group_msg2, send_group_msg_pic, send_group_msg_pic2, send_img
from .service.help_handler import handle_help, get_msg

__zx_plugin_name__ = "只因进化录"
__plugin_usage__ = """
usage：
    加入只因进化录：注册
    只因帮助 2：查看各种功能
""".strip()
__plugin_des__ = "开局一只因，技能全靠吞"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = ["加入只因进化录"]
__plugin_version__ = 1.0
__plugin_author__ = "XiaoR"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": True,
    "cmd": ["加入只因进化录"],
}
__plugin_configs__ = {
}

register = on_command("加入只因进化录", aliases={"注册只因进化录"}, priority=5, block=True)
set_out = on_command("探索", aliases={"出发"}, priority=5, block=True)
go_home = on_command("返回", aliases={"归来", "回家", "只因返回"}, priority=5, block=True)
force_go_home = on_command("强行返回", aliases={"强制返回"}, priority=5, block=True)
use_item = on_command("只因使用", aliases={"使用", "使用物品"}, priority=5, block=False)
receive_mission = on_command("领取任务", aliases={"接取任务"}, priority=5, block=True)
submit_mission = on_command("提交任务", aliases={"任务完成", "提价任务", "交任务", "任务提交", "完成任务"}, priority=5, block=True)
look_mission = on_command("查看任务", aliases={"我的任务", "查询任务"}, priority=5, block=True)
del_mission = on_command("删除任务", priority=5, block=True)
skill_manager = on_command("技能管理", priority=5, block=False)
equip_skill = on_command("装备技能", aliases={"装备技能", "技能装备", "装备", "只因装备"}, priority=5, block=False)
look_skill = on_command("查看技能", aliases={"查询技能", "我的技能", "技能查看", "查询技能", "只因技能"}, priority=5, block=False)
remove_skill = on_command("移除技能", aliases={"卸载技能", "卸除技能", "删除技能","移除","卸载"}, priority=5, block=False)
query = on_command("查询", aliases={"只因查询", "查看", "只因查看"}, priority=5, block=True)
ikun_help = on_command("只因帮助", aliases={"帮助"}, priority=5, block=True)
stay = on_command("驻留", aliases={"滞留", "驻足", "停留", "驻守"}, priority=5, block=True)
reload_config = on_command("重载配置", priority=5, block=False, permission=SUPERUSER)
show_bag = on_command("只因背包", aliases={"查询背包", "背包"}, priority=5, block=True)
rename = on_command("只因改名", priority=5, block=False)
# 模拟战斗 测试用。[[绝对]]不要把这个功能开放給玩家
sim_battle = on_command("模拟战斗", aliases={"战斗模拟"}, priority=5, block=True, permission=SUPERUSER)
# 给所有人发放1个沙漏(已经被签到代替了，这个功能最好不要使用，因为游戏只能玩一个月，发一次少半天)
reward = on_command("发放奖励", aliases={"发放资源"}, priority=5, block=True, permission=SUPERUSER)
# 下面属于历史残留指令 没有用
my_status = on_command("只因状态", priority=5, block=True, permission=SUPERUSER)
game_store = on_command("只因商店", aliases={"只因进化录商店"}, priority=5, block=True, permission=SUPERUSER)
# equip_item = on_command("装备", priority=5, block=True, permission=SUPERUSER)
test = on_command("测试", priority=5, block=True, permission=SUPERUSER)
forge = on_command("制作", priority=5, block=True, permission=SUPERUSER)

driver: Driver = nonebot.get_driver()


@driver.on_startup
async def events_read():
    await load_world_data()
    await init()


# 注册部分
@register.handle()
async def handle_first_register(event: GroupMessageEvent):
    player = await get_player(event)
    if player:
        await register.finish(f"你已经有账号:{player.name} 了哦")
    user_name = (
        event.sender.card if event.sender.card else event.sender.nickname
    )
    await register.finish(await register_new_player(event, user_name, "原版"))


# 出发历险
@set_out.handle()
async def _(state: T_State, event: GroupMessageEvent, arg: Message = CommandArg(), matcher=Matcher()):
    player = await get_player(event)
    if not player:
        await set_out.finish("你还没有账号，请先输入'加入只因进化录'创建账号！")
    result = await player_handler.auto_sign(player)
    if result:
        await set_out.send(result)

    msg = arg.extract_plain_text().strip()
    item, tmp = await get_usable_item(event)
    state["item"] = item

    player, status, pos_list = await get_user_status(event)
    state["pos_list"] = pos_list
    state["player"] = player
    if status != "休息中":
        await set_out.finish(f"你{status}，不能再出发了")
    if msg != "":
        matcher.set_arg("pos", Message(msg))
        return
    await set_out.send(user_status_to_str(pos_list))


@set_out.got("pos")
async def _(event: GroupMessageEvent, state: T_State, num: str = ArgStr("pos")):
    num = num.strip()
    if not num.isdigit():
        await set_out.finish("输入的格式不对，请输入数字")
    num = int(num)
    if num == 0:
        return
    if num > len(state["pos_list"]) or num < 0:
        await set_out.finish("输入的数字范围不对")
    pos = state["pos_list"][num - 1]
    await go_outside(event, pos)
    await set_out.send(f"{state['player'].name}去{pos}了！")


@my_status.handle()
async def _(event: GroupMessageEvent):
    player = await get_player(event)
    if not player:
        await my_status.finish("你还没有账号，请先输入'加入只因进化录'创建账号！")
    await my_status.finish(await get_user_status_str(event))


def user_status_to_str(pos_list: list[str]):
    tmp = ""
    for i, s in enumerate(pos_list):
        tmp += f"{i + 1}: {s}\n"
    return f"""你要去哪里?(输入数字):
0: 我不去了
{tmp}"""


@go_home.handle()
async def handle_go_home(bot: Bot, event: GroupMessageEvent, state: T_State):
    player = await get_player(event)
    if not player:
        await go_home.finish("你还没有账号，请先输入'加入只因进化录'创建账号！")

    result = await player_handler.auto_sign(player)
    if result:
        await set_out.send(result)
    log, flg = await adv_time_pass(event)
    state["player_name"] = player.name
    log_str = [("探索简报", s) for s in log.split("🔚")]
    await super_send(bot, go_home, event, log_str, "消息被风控，可等待一段时间后输入【返回】")


@force_go_home.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    log, flg = await adv_time_pass(event, force_go_home=True)
    log_str = [("探索简报", s) for s in log.split("🔚")]
    try:
        await send_group_msg2(bot, event, log_str)
    except Exception as e:
        await force_go_home.send("消息被风控，尝试10s后重发。如果依然失败，可等待一段时间后输入【查询上次】")
        import time
        time.sleep(10)
        await send_group_msg2(bot, event, log_str)
    if not flg:
        await force_go_home.finish()


@game_store.handle()
async def _(event: GroupMessageEvent, state: T_State):
    tmp, tmpstr = await get_store_list(event)
    await game_store.send(tmpstr)
    state["tmp"] = tmp


@game_store.got("choose", "需要买什么呢？(输入数字编号)")
async def _(state: T_State, p: str = ArgStr("choose")):
    p = p.strip()
    if not p.isdigit():
        await game_store.finish("输入的格式不对，请输入数字")
    p = int(p)
    if p == 0:
        await game_store.finish("你离开了商店")
    if p > len(state["tmp"]) or p < 0:
        await game_store.finish("输入的数字范围不对")
    state["item"] = state["tmp"][p - 1]


@game_store.got("choose2", f"要买几个呢？(输入数量)")
async def _(event: GroupMessageEvent, state: T_State, num: str = ArgStr("choose2")):
    num = num.strip()
    if not num.isdigit():
        await game_store.finish("输入的格式不对，请输入数字")
    num = int(num)
    if num < 0:
        await game_store.finish("输入的格式不对，请输入正数")
    if num == 0:
        await game_store.finish("你离开了商店")

    await game_store.finish(await buy_item_handle(event, state["item"].name, state["item"].cost, num))


@use_item.handle()
async def _(event: GroupMessageEvent, state: T_State, arg: Message = CommandArg(), matcher=Matcher()):
    msg = arg.extract_plain_text().strip()
    item, tmp = await get_usable_item(event)
    state["item"] = item

    if msg != "":
        matcher.set_arg("choose", Message(arg))
        return
    if len(item) == 0:
        await use_item.finish("没有可使用的物品")
    await use_item.send(tmp)


@use_item.got("choose")
async def _(bot: Bot, event: GroupMessageEvent, state: T_State, num: str = ArgStr("choose")):
    num = num.strip()
    if not num.isdigit():
        await use_item.finish("输入的格式不对，请输入数字")
    num = int(num)
    if num == 0:
        await use_item.finish()
    if num < 0 or num > len(state["item"]):
        await use_item.finish("输入的数字不在选定范围内")
    msg = await use_item_handler(event, itemname=state["item"][num - 1][0], itemcnt=1)
    await use_item.send(msg)
    if "完成了探索" in msg:
        await handle_go_home(bot, event, state)


@forge.handle()
async def _(event: GroupMessageEvent, state: T_State):
    item, tmp = await get_forge_list(event)
    state["item"] = item
    await forge.send(tmp)


@forge.got("choose", "需要制作什么呢？(输入数字编号)")
async def _(event: GroupMessageEvent, state: T_State, num: str = ArgStr("choose")):
    num = num.strip()
    if not num.isdigit():
        await forge.finish("输入的格式不对，请输入数字")
    num = int(num)
    if num == 0:
        await forge.finish("好的")
    if num < 0 or num > len(state["item"]):
        await forge.finish("输入的数字不在选定范围内")
    can_forge_num = await get_forge_num(event, state["item"][num - 1])
    if can_forge_num <= 0:
        await forge.finish("你的素材不够制作")
    if can_forge_num == 1:
        await forge.finish(await handle_forge(event, state["item"][num - 1], 1))
    await forge.send(f"看起来最多可以做{can_forge_num}个")
    state["tar"] = state["item"][num - 1]
    state["tarnum"] = can_forge_num


@forge.got("choose2", "需要制作几个呢？(输入数字)")
async def _(event: GroupMessageEvent, state: T_State, num: str = ArgStr("choose2")):
    num = num.strip()
    if not num.isdigit():
        await forge.finish("输入的格式不对，请输入数字")
    num = int(num)
    can_forge_num: int = state["tarnum"]
    tar: Compose = state["tar"]
    if num == 0:
        await forge.finish("你不做了")
    if num > can_forge_num:
        await forge.send(f"没法做那么多！帮你做{can_forge_num}个吧！")
        num = can_forge_num
    await forge.finish(await handle_forge(event, tar, num))


#
# @equip_item.handle()
# async def _(event: GroupMessageEvent, state: T_State):
#     tmp, tmpstr = await get_equip_list(event)
#     if len(tmp) == 0:
#         await equip_item.finish('你没有可用的装备')
#     await equip_item.send(tmpstr)
#     state['tmp'] = tmp
#
#
# @equip_item.got("choose", prompt="请输入要装备物品的编号")
# async def _(event: GroupMessageEvent, state: T_State, num: str = ArgPlainText("choose")):
#     if not num.isdigit():
#         await equip_item.finish("输入的格式不对，请输入数字")
#     num = int(num)
#     if num == 0:
#         return
#     if num < 0 or num > len(state["tmp"]):
#         await equip_item.finish("输入的数字不在选定范围内")
#     await equip_item.finish(await handle_equip(event, state["tmp"][num - 1]))


@test.handle()
async def _(event: GroupMessageEvent, bot: Bot, arg: Message = CommandArg()):
    # await foo()
    await test.send("")
    return


@receive_mission.handle()
async def _(event: GroupMessageEvent, state: T_State, matcher: Matcher):
    ms, ms_str = await get_available_mission(event)
    ms_received = await get_short_submitable_mission(event)
    if len(ms) == 0:
        await receive_mission.finish(ms_received + "没有可领取的任务，可以尝试【查看任务】")
    if len(ms) == 1:
        matcher.set_arg("choose", Message("1"))
    else:
        await receive_mission.send(ms_received + ms_str)
    state["tmp"] = ms


@receive_mission.got("choose")
async def _(bot: Bot, event: GroupMessageEvent, state: T_State, num: str = ArgPlainText("choose")):
    num = num.strip()
    if not num.isdigit():
        await receive_mission.finish("输入的格式不对，请输入数字")
    num = int(num)
    if num == 0:
        return
    if num < 0 or num > len(state["tmp"]):
        await receive_mission.finish("输入的数字不在选定范围内")
    await send_group_msg2(bot, event, await handle_receive_mission(event, state["tmp"][num - 1]))


@submit_mission.handle()
async def _(event: GroupMessageEvent, state: T_State, matcher: Matcher):
    ms, msstr, flg = await get_submitable_mission(event)
    if len(ms) == 0:
        await submit_mission.finish("没有可提交的任务")
    if not flg:
        await submit_mission.finish(msstr)
    if len(ms) == 1:
        matcher.set_arg("choose", Message("1"))
    else:
        await submit_mission.send(msstr)
    state["tmp"] = ms


@submit_mission.got("choose")
async def _(bot: Bot, event: GroupMessageEvent, state: T_State, num: str = ArgPlainText("choose")):
    num = num.strip()
    if not num.isdigit():
        await submit_mission.finish("输入的格式不对，请输入数字")
    num = int(num)
    if num == 0:
        return
    if num < 0 or num > len(state["tmp"]):
        await submit_mission.finish("输入的数字不在选定范围内")
    result = await handle_submit_mission(event, state["tmp"][num - 1])
    if type(result) == str:
        await submit_mission.finish(result)
    await send_group_msg2(bot, event, result)


@look_mission.handle()
async def _(event: GroupMessageEvent, state: T_State, matcher: Matcher):
    ms, msstr, flg = await get_submitable_mission(event)
    if len(ms) == 0:
        await look_mission.finish("没有可查看的任务")
    if len(ms) == 1:
        matcher.set_arg("choose", Message("1"))
    else:
        await look_mission.send(msstr)
    state["tmp"] = ms


@look_mission.got("choose")
async def _(event: GroupMessageEvent, bot: Bot, state: T_State, num: str = ArgPlainText("choose")):
    num = num.strip()
    if not num.isdigit():
        await look_mission.finish("输入的格式不对，请输入数字")
    num = int(num)
    if num == 0:
        return
    if num < 0 or num > len(state["tmp"]):
        await look_mission.finish("输入的数字不在选定范围内")
    await send_group_msg2(bot, event, await handle_look_mission(state["tmp"][num - 1]))


@del_mission.handle()
async def del_mission_handle(event: GroupMessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    if len(msg) < 1:
        await del_mission.finish("参数不完全，请输入删除任务 真实编号 注意，该指令非常危险！")
    id = int(msg[0])
    await del_mission.send(await handle_del_mission(event, id))


@skill_manager.handle()
async def skill_manager_handle(bot: Bot, event: GroupMessageEvent, matcher: Matcher,
                               args: Message = CommandArg()):
    await skill_manager.finish("这个功能已经被关闭了！请使用【查看技能】【装备技能】代替吧")
    msg: list[str] = args.extract_plain_text().strip().split(" ")
    data = dict(enumerate(msg))
    if data.get(0):
        matcher.set_arg("choose", Message(data[0]))
    else:
        await send_group_msg2(bot, event, await get_skill_list(event))


@skill_manager.got("choose")
async def skill_manager_step2(state: T_State, num: str = ArgPlainText("choose")):
    if not num.isdigit():
        await skill_manager.finish("已退出技能管理")
    num = int(num)
    if num == 0:
        await skill_manager.finish()
    if num < 0 or num > 4:
        await skill_manager.finish("输入的数字不在选定范围内")
    state["choose"] = num
    if num == 1:
        await skill_manager.send("请输入你需要装备的技能名")
        return
    if num == 2:
        await skill_manager.send("请输入你需要卸除的技能名")
        return
    await skill_manager.reject("请输入正确选项")


@skill_manager.got("choose2")
async def skill_manager_step3(event: GroupMessageEvent, bot: Bot, state: T_State,
                              choose: str = ArgPlainText("choose2")):
    state["choose2"] = choose
    if state["choose"] == 1:
        result, msg = await check_skill_exist(event, choose)
        if not result:
            await skill_manager.finish(msg)
        state["name"] = msg
        await send_group_msg2(bot, event, await get_equip_skill_list(event, "请选择你要装备的技能位置"))

    if state["choose"] == 2:
        await skill_manager.finish(await unequip_skill(event, choose))


@skill_manager.got("choose3")
async def skill_manager_step3(event: GroupMessageEvent, state: T_State,
                              choose: str = ArgPlainText("choose3")):
    choose = int(choose)
    await skill_manager.finish(await skill_handler.equip_skill(event, state["choose2"], choose - 1))


@ikun_help.handle()
async def show_help_menu(bot: Bot, event: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    player = await get_player(event)
    if not player:
        await set_out.finish("你还没有账号，请先输入'加入只因进化录'创建账号！")
    tmp: list[str] = args.extract_plain_text().strip().split(" ")
    if len(tmp) == 1 and tmp[0] != "":
        matcher.set_arg("choose", args)
        return
    msg = get_msg()
    # 4. 什么是地图热度？
    await send_group_msg2(bot, event, msg)


@ikun_help.got("choose")
async def show_help_menu_step2(event: GroupMessageEvent, bot: Bot, num: str = ArgPlainText("choose")):
    await handle_help(num, ikun_help, bot, event)


@reload_config.handle()
async def reload():
    await game_handler.load_world_data()
    await reload_config.finish("重载完毕，请注意控制台有无错误")


# todo 无论查询技能 物品 地图信息 怪物 战斗日志 都可以用这个指令
@query.handle()
async def _(matcher: Matcher, bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    plain_text = args.extract_plain_text().strip()
    # 查数字一律认为是在查战斗日志
    if plain_text.isdigit():
        await super_send(bot, query, event, await query_battle_log(plain_text), "查询失败，消息被风控，正在尝试重发")
        await query.finish()
    if plain_text == '战斗次数':
        await query.finish(f"战斗了{await player_handler.query_times(event)}次", at_sender=True)
    if plain_text:
        matcher.set_arg("name", args)


@query.got("name", prompt="请输入查询名词的部分名称")
async def query_step2(bot: Bot, event: GroupMessageEvent, state: T_State, item_name: str = ArgPlainText("name")):
    msg, flg, item = await handle_look_all(event, item_name)
    if flg:
        await super_send(bot, query, event, msg, "查询失败，消息被风控，正在尝试重发")
        await query.finish()
    else:
        state["item"] = item
        await query.send(msg)


@query.got("choose")
async def query_step3(bot: Bot, state: T_State, event: GroupMessageEvent, num: str = ArgPlainText("choose")):
    num = num.strip()
    if not num.isdigit():
        await query.finish("输入的格式不对，请输入数字")
    num = int(num)
    if num < 0 or num >= len(state["item"]):  # 因为没有0号选项所以num后面是>= 与其他地方不同
        await query.finish("输入的数字不在选定范围内")
    msg = (await handle_look_all(event, state["item"][num]))[0]
    await super_send(bot, query, event, msg, "查询失败，消息被风控，正在尝试重发")


@stay.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    num = args.extract_plain_text().strip()
    if not num.isdigit():  # 不是数字可能是别人在说胡话（
        return
    await query.finish(await handle_set_stay(event, int(num)))


@show_bag.handle()
async def _(event: GroupMessageEvent):
    await show_bag.finish(await handle_show_bag(event))


@equip_skill.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg(), matcher=Matcher()):
    msg = arg.extract_plain_text().strip().split(" ")
    if len(msg) == 1 and msg[0] != '':
        # 有的人喜欢不带空格 那就帮他！（e.g. 装备技能 尖角1  装备技能1尖角）
        rr: list[str] = re.split('(\\d+)', msg[0])
        if len(rr) >= 2 and rr[1].isdigit():
            msg = rr[0:2] if rr[0] != '' else rr[1:3]
        else:
            matcher.set_arg("name", Message(msg[0]))
            return

    if len(msg) == 2:
        if msg[0].isdigit() and not msg[1].isdigit():
            msg[0], msg[1] = msg[1], msg[0]
        await equip_skill.finish(await skill_handler.equip_skill(event, msg[0], int(msg[1]) - 1))


@equip_skill.got("name", "你要装备什么技能？（纯汉字）")
async def equip_step2(bot: Bot, state: T_State, event: GroupMessageEvent, name: str = ArgPlainText("name")):
    result, msg = await skill_handler.check_skill_exist(event, name)
    if not result:
        await equip_skill.finish(msg)
    state["name"] = msg
    await send_group_msg2(bot, event, await skill_handler.get_equip_skill_list(event, f"要把{msg}装备在哪里？"))


@equip_skill.got("pos")
async def equip_step3(state: T_State, event: GroupMessageEvent, pos: str = ArgPlainText("pos")):
    await equip_skill.finish(await skill_handler.equip_skill(event, state["name"], int(pos) - 1) +
                             f"\n提示: 可直接输入 装备技能{state['name']}{pos} ，加快操作速度")


@look_skill.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip()
    if msg != "":  # 查询技能和查看技能是2个不同的功能 如果玩家混淆了 可能会在查看技能后面加上技能名词 这时候查看技能就不再处理这件事 交给查询技能
        return
    await send_group_msg2(bot, event, (await get_skill_list(event))[1:])


@remove_skill.handle()
async def _(arg: Message = CommandArg(), matcher=Matcher()):
    msg = arg.extract_plain_text().strip().split(" ")
    if len(msg) >= 1 and msg[0] != '':
        logger.info(str(msg), len(msg))
        matcher.set_arg("name", Message(msg[0]))


@remove_skill.got("name", prompt="你想移除的技能名字(汉字),或技能的位置(数字):")
async def remove_skill2(event: GroupMessageEvent, name: str = ArgPlainText("name")):
    await remove_skill.finish(await skill_handler.unequip_skill(event, name))


@reward.handle()
async def handle_reward():
    await reward.finish(await player_handler.reward_all())


@rename.handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    plain_text = args.extract_plain_text()  # 首次发送命令时跟随的参数，例：/天气 上海，则args为上海
    if plain_text:
        matcher.set_arg("name", args)  # 如果用户发送了参数则直接赋值


@rename.got("name", prompt="你要叫什么名字呢？")
async def handle_rename(event: GroupMessageEvent, name: str = ArgPlainText("name")):
    await rename.finish(await player_handler.change_name(event, name))


@sim_battle.handle()
async def _(bot: Bot, event: GroupMessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split(" ")
    log = await battle_handler.sim_battle(event, msg[0], msg[1], msg[2])
    await send_group_msg2(bot, event, [("最高权限-模拟战斗", log)])


# 支持风控检查的超级发送函数
async def super_send(bot, bot2, event, msg, failmsg, name='', to_pic=False):
    if to_pic:
        if list == type(msg):
            if type(msg[0]) == str:
                await send_group_msg_pic(bot2, name, msg)
                return
            await send_group_msg_pic2(bot2, msg)
            return
        await send_img(bot2, msg)
        return
    try:
        if list == type(msg):
            if len(msg) == 0:
                await bot2.finish("发送消息为空")
            if type(msg[0]) == str:
                await send_group_msg(bot, event, name, msg)
            else:
                await send_group_msg2(bot, event, msg)
        else:
            await bot2.finish(msg)
    except Exception as e:
        if not isinstance(e, FinishedException):
            logger.warning("检查到风控！")
            await bot2.send(failmsg)
            await super_send(bot, bot2, event, msg, failmsg, name, True)
# @register.got("yn")
# async def handle_register_yn(matcher: Matcher, yn: str = ArgStr("yn")):
#     if yn != "是":
#         await register.finish("重新注册吧！")
#     await register.send(Message.template("{}{}{}{}{}").format(get_image("head", "阿桃", "gif"),
#                                                               get_image("head", "走地鸡", "gif"),
#                                                               get_image("head", "墨镜鸡", "gif"),
#                                                               get_image("head", "原版", "gif"),
#                                                               "选择你的形象(1/2/3/4)"))

#
# @register.got("choose")
# async def handle_register_sex(event: GroupMessageEvent, state: T_State, choose: str = ArgStr("choose")):
#     if not choose.isdigit():
#         await register.reject("请输入正确数字")
#     choose = int(choose)
#     head_name_list = ["阿桃", "走地鸡", "墨镜鸡", "原版"]
#     if 1 <= choose <= 4:
#         await register.finish(await register_new_player(event, state["name"], head_name_list[choose - 1]))
#     else:
#         await register.reject("请输入正确数字")
