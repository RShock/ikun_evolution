import math
import random

from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .game_handler import Item
from .game_handler import get_world_data, Compose
from .player_handler import get_player
from ..model.player_model import PlayerDB
from ..stream import Stream


def check(player: PlayerDB, t: Compose) -> bool:
    if player.lv < t.lv:
        return False
    for consume in t.consume:
        if not player.collection.get(consume["name"]):
            return False
    return True


async def get_forge_list(event: GroupMessageEvent) -> [dict[str, Item], str]:
    tmp = get_world_data().get_forge_list()
    player = await get_player(event)
    tmp = Stream(tmp).filter(lambda t: check(player, t)).to_list()
    return tmp, convert_shop_item_to_str(tmp)


def convert_shop_item_to_str(tmp: list[Compose]) -> str:
    ans = "制作列表：\n0: 我不做了 \n"
    i = 1
    for item in tmp:
        ans += f"{i}: {item.name}\n"
        i += 1
    return ans


async def get_forge_num(event, forge: Compose) -> int:
    player: PlayerDB = await get_player(event)
    mi = 999999
    for i in forge.consume:
        mi = min(player.query_item(i["name"]) // i["num"], mi)
    return mi


async def handle_forge(event, forge: Compose, times: int) -> str:
    player: PlayerDB = await get_player(event)
    exp = 0
    for i in forge.consume:
        player.cost_item(i["name"], i["num"] * times)
        if i["name"] == '金币':
            exp += i["num"] *times
    tmpstr = '制作中...\n'
    for i in forge.produce:
        num = i["num"]
        tmp = math.modf(num)
        total = 0
        for j in range(0, times):
            # 如果制作一次得到1.4个 那么40%得到2个 60%得到1个
            num = int(tmp[1])
            if tmp[0] > random.random():
                num += 1
            total += num
            tmpstr += f'{forge.type}了{num}个{i["name"]}\n'
        player.add_item(i["name"], total)
    await player.update(bag=player.bag, collection=player.collection,
                        forge_exp=player.forge_exp + exp).apply()
    return tmpstr
