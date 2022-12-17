from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .player_handler import get_player
from ..service import adv_handler
from ..service.adv_handler import finish_action, get_user_status
from .game_handler import get_world_data
from ..model.player_model import PlayerDB
from ..utils import get_act_str
from .game_handler import Item


async def get_usable_item(event: GroupMessageEvent) -> [dict[str, Item], str]:
    player: PlayerDB = await get_player(event)
    tmp = []
    tmp.append(("小沙漏", player.query_item("小沙漏")))
    for k, v in player.bag.items():
        if k != '小沙漏' and get_world_data().get_item(k).usable and v >= 1:
            tmp.append((k, v))
    return tmp, convert_usable_item_to_str(tmp)


def convert_usable_item_to_str(tmp) -> str:
    ans = "你要使用什么呢？\n0: 返回\n"
    i = 0
    for item in tmp:
        ans += f"{i + 1}: {item[0]} 数量 {item[1]}\n"
        i += 1
    return ans


async def use_item_handler(event, itemname, itemcnt) -> str:
    player, status, _ = await get_user_status(event)

    if itemname == '小沙漏':
        if player.buff.get('特殊任务中'):
            return '你正在特殊任务中，沙漏被禁用了'
        if status == '休息中':
            return '你还没出发呢！'
        cost = await adv_handler.should_speed_up_cost(event)
        if player.cost_item('小沙漏', cost):
            await player.update(bag=player.bag).apply()
        else:
            return f"需要{cost}个沙漏，你只有{player.query_item('小沙漏')}个"
        if await finish_action(event, lambda a: a.action != get_act_str('活动')):
            return f'用{cost}个沙漏完成了探索'
        else:
            return "故障，请通报管理员"
    if itemname == '大蟠桃':
        player.cost_item('大蟠桃', 1)
        await player.update(atk=player.atk + 20, defe=player.defe + 10, hp=player.hp + 100, lv=player.lv + 4,
                            bag=player.bag, spd=player.spd + 1).apply()
        return "吃下了猴王珍藏的桃子，你的等级居然永久提升了，实力劲增！(初始等级+4 攻+20 守+10 命+100 速+1）\n副作用：成长的基础等级+4，现在成长要在角色变成9级时才有原来5级的效果"
    # player.add_item(itemname, itemcnt)
    # await player.update(bag=player.bag, gold=player.gold + dif).apply()
    return f"未知错误，使用{itemname}失败"
