from ..model.player_model import PlayerDB
from .game_handler import get_world_data
from .player_handler import get_player
from ..stream import Stream


async def get_equip_list(event) -> tuple[list[str], str]:
    player = await get_player(event)
    tmp = Stream(player.get_bag().keys()).filter(lambda i: get_world_data().get_item(i).equip_type).to_list()
    tmp_str = '可装备物品列表:\n0: 我不装备了\n'
    i = 1
    for s in tmp:
        tmp_str += f"{i}: {s}\n"
        i = i + 1
    return tmp, tmp_str


async def handle_equip(event, name) -> str:
    player: PlayerDB = await get_player(event)
    item = get_world_data().get_item(name)
    old_item = player.get_equip(item.equip_type)
    if old_item is None:
        player.wear(item.equip_type, item.name)
        await player.update(bag=player.bag, equip=player.equip).apply()
        return f"装备上了{item.simple_name()}"
    else:
        player.unwear(item.equip_type, old_item)
        player.wear(item.equip_type, item.name)
        await player.update(bag=player.bag, equip=player.equip).apply()
        return f"脱下了{old_item},装备上了{item.simple_name()}"
