from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .player_handler import get_player
from .game_handler import get_world_data
from ..model.player_model import PlayerDB
from .game_handler import Item


async def get_store_list(event: GroupMessageEvent) -> [dict[str, Item], str]:
    tmp = get_world_data().get_shop_item()
    player = await get_player(event)
    money = player.query_item('金币')
    return tmp, convert_shop_item_to_str(tmp, money)


def convert_shop_item_to_str(tmp, money) -> str:
    ans = f"商品列表：  当前点数{money}\n0: 我不买了\n"
    i = 1
    for item in tmp:
        ans += f"{i}: {item.name}: {item.cost}点\n"
        i += 1
    return ans


async def buy_item_handle(event, itemname, itemcost, itemcnt) -> str:
    player:PlayerDB = await get_player(event)
    dif = itemcnt * itemcost - player.query_item("金币")
    if dif > 0:
        return f"你买不起这么贵的商品，还差{dif}点，点数可以打工获得"
    player.add_item(itemname, itemcnt)
    player.cost_item('金币', dif)
    await player.update(bag=player.bag,collection=player.collection).apply()
    return f"从老板那里获得了{itemname} x{itemcnt}"
