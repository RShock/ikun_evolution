from nonebot.adapters.onebot.v11 import Message

from .player_handler import get_player
from .game_handler import get_world_data
from ..model.mission_model import MissionDB
from ..stream import Stream
from ..utils import get_image


async def handle_look_all(event, name) -> [str, bool, list[str]]:
    player = await get_player(event)
    item_list = Stream(get_world_data().itemList.keys()).filter(lambda n: name in n).to_list()
    skill_list = Stream(get_world_data().skillList.keys()).filter(lambda n: name in n).to_list()
    monster_list = Stream(get_world_data().enemyList.keys()).filter(lambda n: name in n).to_list()
    mission_list = Stream(get_world_data().missionList.keys()).filter(lambda n: name in n).to_list()
    map_list = Stream(get_world_data().mapList.keys()).filter(lambda n: name in n).to_list()

    sum = len(item_list) + len(skill_list) + len(monster_list) + len(mission_list) + len(map_list)
    if sum == 0:
        return "未查到相关信息", True, None

    if (sum == 1 and len(item_list) == 1) or (len(item_list) > 0 and item_list[0] == name):
        return show_item_info(player, item_list[0]), True, None

    if (sum == 1 and len(skill_list) == 1) or (len(skill_list) > 0 and skill_list[0] == name):
        return show_skill_info(player, skill_list[0]), True, None

    if (sum == 1 and len(monster_list) == 1) or (len(monster_list) > 0 and monster_list[0] == name):
        return show_monster_info(player, monster_list[0]), True, None

    if (sum == 1 and len(mission_list) == 1) or (len(mission_list) > 0 and mission_list[0] == name):
        return await show_mission_info(player, mission_list[0]), True, None

    if (sum == 1 and len(map_list) == 1) or (len(map_list) > 0 and map_list[0] == name):
        return show_map_info(player, map_list[0]), True, None

    item_list = item_list + skill_list + monster_list + mission_list + map_list
    return convert_items_to_str_list(item_list), False, item_list


def convert_items_to_str_list(tmp: list[str]) -> str:
    ans = "想查哪个？\n"
    i = 0

    for item in tmp:
        ans += f"{i}: {item}\n"
        i += 1
    return ans


def show_item_info(player, name):
    item = get_world_data().get_item(name)
    return Message.template("{}\n{}\n{}\n获得数量 {}").format(name, item.description,
                                                          get_image("item", f"{name}.png"),
                                                          str(player.collection.get(name, "未获得")))


def show_skill_info(player, name):
    lv = player.skill.get(name)
    skill = get_world_data().get_skill(name)
    if lv is None:
        sp_skill = player.sp_skill.get(name)
        own = "未拥有" if sp_skill is None else f"已拥有"
    else:
        own = f"等级:{lv}"
    msg = f"""{skill.emoji}{name}  技能等级：[{skill.min}-{skill.max}]
描述：{skill.des}
当前{own}
升级总需经验：{skill.exp}"""
    # 性能开销略大的溯源搜索
    result = []
    for m in get_world_data().mapList.values():
        if player.query_arrived(m.name) == 0:
            continue
        total = sum(enemy["weight"] for enemy in m.enemy_list)
        for enemy in m.enemy_list:
            if enemy["weight"] * 2 < total:
                continue
            for sk in get_world_data().get_enemy(enemy["name"]).skill:
                if name in sk:
                    result.append(f"{enemy['name']}({m.name})")
    if bool(result):
        pos = ", ".join(result)
    else:
        pos = "去过一次才知道"

    if lv is not None:
        next_exp = skill.get_next_lv_exp(lv)
        max_exp = skill.get_max_lv_exp(lv)
        return msg + f"""
升级尚需经验：{next_exp}
满级尚需经验：{max_exp}
已知大概率掉落地点：{pos}"""
    return msg


def show_monster_info(player, name):
    monster = get_world_data().enemyList.get(name)
    meet = player.monster_meet.get(name, 0)
    killed = player.monster_killed.get(name, 0)
    skill = ",".join(monster.skill) if len(monster.skill) != 0 else "无"
    sp_skill = ",".join(monster.sp_skill) if len(monster.sp_skill) != 0 else "无"
    shuxing = f"{monster.baselv}级数值：攻{monster.atk} 防{monster.defe} 命{monster.hp} 速{monster.spd}"
    des = monster.des
    if meet == 0:
        skill = "未知"
        sp_skill = "未知"
        shuxing = "数值：未知"
        des = ""
    if killed == 0 and "反鉴定" in monster.sp_skill:
        skill = "鉴定被干扰！需要击杀怪物"
        sp_skill = "反鉴定，其他未知"
        shuxing = f"数值：未知"
        des = ""
    hint = ""
    if meet < killed:
        hint = "(老怪物遭遇次数在更新前没有统计)"
    if sp_skill == "无" or sp_skill == "未知":
        sp_txt = ""
    else:
        sp_txt = f"血继限界：{sp_skill}"
    d = meet - killed
    if monster.hint:
        if d >= 3:
            hint = "【系统提示】\n"+monster.hint
        else:
            hint = "【系统提示】\n如果你被其击败了3次，就可以看到攻略"
    return f"""{name}
技能：{skill}
{sp_txt}
{shuxing}
遭遇次数：{meet}
击杀次数：{killed}
{des}
{hint}"""


async def show_mission_info(player, name):
    mission = get_world_data().get_mission(name)
    db: MissionDB = await MissionDB.get_mission(player.uid, name)
    if db is None:
        return f"""任务名称：{name}
你还尚未接取过这个任务。"""
    return [("任务名称", name), ("任务描述", mission.des), ("任务目标", mission.tar), ("任务提示", mission.hint),
            ("任务奖励", mission.reward_str), ("完成状态", db.status)]


def show_map_info(player, name):
    m = get_world_data().get_map(name)
    arrived = player.query_arrived(name)
    if arrived == 0:
        return f"地图名称：{name}\n至少去过一次后，展示更多信息"
    sub_map = ", ".join(t["name"] for t in m.owned_map) if len(m.owned_map) != 0 else "无"
    creature = ", ".join(t["name"] for t in m.enemy_list) if len(m.enemy_list) != 0 else "无"
    item = ", ".join(t["name"] for t in m.item_list) if len(m.item_list) != 0 else "无"
    other_info = "" if m.public else f'包含生物：{creature}\n掉落物品：{item}'
    return f"""地图名称：{name}
起点：{"是" if m.public else "否"}
{m.description if m.description else ""}
停留次数：{arrived}
通向哪里：{sub_map}
{other_info}"""
