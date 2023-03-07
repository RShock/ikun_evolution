import time

from nonebot import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from ..model.gino_db import db
from ..service.adv_handler import get_user_status
from ..model.player_model import PlayerDB
from ..utils import get_uid


async def register_new_player(event: GroupMessageEvent, name: str, head_choose: str) -> str:
    player = await PlayerDB.get_player_by_name(name)
    if player:
        return "这个名字已经有人用过啦！"

    player_count = await PlayerDB.register(get_uid(event), event.group_id, name, head_choose)

    if player_count:
        return f"{name}加入了只因进化录的世界！当前赛季为S1起源赛季，你是第{player_count}只因哦\n" \
               f"输入【领取任务】指令开始你的新手引导吧！"
    else:
        return "未知错误..."


async def get_player(event) -> PlayerDB:
    player = await PlayerDB.get_player_by_uid(get_uid(event))
    return player


async def get_user_status_str(event) -> str:
    player, status, pos_list = await get_user_status(event)
    return f"{player.name} lv{player.system_lv}{status}\n" \
           f"所有掌握的技能：\n" \
           f"{player.show_skill()}\n" \
           f"背包：\n" \
           f"{player.show_bag()}"


async def handle_set_stay(event, lv: int) -> str:
    player = await PlayerDB.get_player_by_uid(get_uid(event))
    if lv <= 0:
        if "stay" in player.buff:
            del player.buff["stay"]
            await player.update(buff=player.buff).apply()
        return "已经解除驻留功能"

    player.buff["stay"] = lv + 1
    s = f"驻留功能已开启，角色遇到lv.{lv}的怪物后不再前往下一区域"
    await player.update(buff=player.buff).apply()
    return s


async def handle_show_bag(event) -> str:
    player = await PlayerDB.get_player_by_uid(get_uid(event))
    return player.show_bag()


async def reward_all() -> str:
    # todo 性能优化+ 限制只给对应赛季发放
    players: list[PlayerDB] = await PlayerDB.get_all()
    try:
        async with db.transaction():
            for player in players:
                player.add_item("小沙漏", 1)
                await player.update(bag=player.bag, collection=player.collection).apply()
    except Exception as e:
        logger.info(f"全服发放奖励出错 {type(e)}: {e}")
        return "全服发放奖励出错"
    return "全服发放奖励 小沙漏*1 成功"


async def query_times(event) -> int:
    player = await PlayerDB.get_player_by_uid(get_uid(event))
    return player.times


async def change_name(event, name) -> str:
    if len(name) > 10:
        return "名字不能超过10个字符"
    if len(name) == 0:
        return "名字太短了！"
    player = await PlayerDB.get_player_by_uid(get_uid(event))
    await player.update(name=name).apply()
    return f"{name},名称修改成功！"


async def auto_sign(player: PlayerDB) -> str:
    # 自动签到逻辑
    now_day = time.strftime('%Y-%m-%d')
    if player.buff.get("sign_day", "") != now_day:
        player.add_item("小沙漏", 1)
        player.buff["sign_day"] = now_day
        await player.update(bag=player.bag, collection=player.collection, buff=player.buff).apply()
        return "今日签到已完成，获得小沙漏一个喵"
    return None
