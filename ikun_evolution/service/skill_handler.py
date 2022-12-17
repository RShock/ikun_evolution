import math

from nonebot.adapters.onebot.v11 import GroupMessageEvent

from .game_handler import get_world_data, Skill
from ..model.player_model import PlayerDB
from ..utils import get_uid, fill_list


async def get_skill_list(event: GroupMessageEvent):
    player: PlayerDB = await PlayerDB.get_player_by_uid(get_uid(event))
    skill: dict[str, float] = player.skill
    sp_skill: dict[str, float] = player.sp_skill
    # equip: list[str] = player.equip_skill
    max_equip: int = player.system_lv

    # new_equip_str = [f"{eq[0]} 等级{eq[1]}\n" for eq in new_equip]
    world_data = get_world_data()
    skill_str = ''.join(world_data.get_skill(name).format_1_line_detail(lv) for name, lv in skill.items())
    sp_skill_str = ''.join(world_data.get_skill(name).format_1_line_detail(lv) for name, lv in sp_skill.items())

    return [
        (f"超级吞噬系统", "请选择选项：\n1.装备技能\n2.卸除已有技能\n其他.退出技能管理"),
        (f"{player.name}当前装备的技能", equip_to_str(player)),
        ("最大允许装备技能数", str(max_equip)),
        ("技能池", f"{skill_str}"),
        ("血继限界", f"{sp_skill_str}"),
        ("超级吞噬系统", "系统提示，对于不懂的技能·物品均可使用'查询 xx'询问系统。\n可用指令：【装备技能】【查看技能】【移除技能】")
    ]


async def equip_skill(event: GroupMessageEvent, skill_name: str, pos: int):
    # 先检查玩家是否有这个技能
    player: PlayerDB = await PlayerDB.get_player_by_uid(get_uid(event))
    if not (skill_name := player.query_skill_fuzzy(skill_name)):
        return "你还没有这个技能，无法装备"
    # 获取已经装备的技能，因为等级在skill中记录了，所以equip所以是没等级的list而不是skill一样的dict
    equip: list[str] = player.equip_skill
    # 获取总共允许的技能数
    count = player.system_lv
    if pos > count:
        return f"你现在只有{count}个技能槽哦"
    equip = fill_list(equip, count, None)
    # 然后获得已经装备的技能，根据情况分为以下3种
    # 1. 玩家已经装备了A 又装备A在其他位置 这是【换位】
    if skill_name in equip:
        index = equip.index(skill_name)
        equip[index], equip[pos] = equip[pos], equip[index]
        player.equip_skill = equip
        msg = f"交换了{'空闲' if equip[index] is None else equip[index]}与{skill_name}的位置，已装技能：{equip_to_simple_str(player)}"
    # 2. 玩家没有装备A 现在装备A 但是装备的位置已经有B了 这是【替换】
    elif equip[pos] is not None:
        tmp = equip[pos]
        equip[pos] = skill_name
        player.equip_skill = equip
        msg = f"装备了{skill_name}，替换下去了{tmp}，已装技能：{equip_to_simple_str(player)}"
    # 3. 玩家没有装备A 现在装备A 这是普通装备
    else:
        equip[pos] = skill_name
        player.equip_skill = equip
        msg = f"装备了{skill_name}，已装技能：{equip_to_simple_str(player)}"
    await player.update(equip_skill=equip).apply()
    return msg


async def get_equip_skill_list(event: GroupMessageEvent, msg: str):
    player: PlayerDB = await PlayerDB.get_player_by_uid(get_uid(event))
    skill_str = equip_to_str(player)

    return [("超级吞噬系统", msg), ("超级吞噬系统", skill_str)]


def equip_to_str(player: PlayerDB):
    new_equip = [(eq, int(player.skill.get(eq)) if eq is not None else None) for eq in player.equip_skill]
    tmp = ""
    for i in range(player.system_lv):
        if i >= len(new_equip) or new_equip[i][0] is None:
            tmp += f"{i + 1}: (空闲)\n"
        else:
            tmp += f"{i + 1}: {new_equip[i][0]} lv.{new_equip[i][1]}\n"
    return tmp


async def check_skill_exist(event, skill_name):
    player: PlayerDB = await PlayerDB.get_player_by_uid(get_uid(event))
    if skill_name == '吞天者':
        return False, "血继限界是角色天生具备的，不需要装备！"
    if name := player.query_skill_fuzzy(skill_name):
        return True, name
    return False, f"找不到【{skill_name}】这个技能，无法装备"


async def unequip_skill(event, skill_name) -> str:
    player: PlayerDB = await PlayerDB.get_player_by_uid(get_uid(event))

    if skill_name.isdigit():
        i = int(skill_name) - 1
        if i < 0 or i >= player.system_lv:
            return f"输入的数字应当在0-{player.system_lv}之间，已装技能：{equip_to_simple_str(player)}"
    else:
        if skill_name not in player.equip_skill:
            return "你还没有装备这个技能"
        i = player.equip_skill.index(skill_name)

    player.equip_skill[i] = None
    await player.update(equip_skill=player.equip_skill).apply()
    return f"卸除技能完成，已装技能：{equip_to_simple_str(player)}"


def equip_to_simple_str(player: PlayerDB) -> str:
    new_equip = [(eq, int(player.skill.get(eq)) if eq is not None else None) for eq in player.equip_skill]
    tmp = ""
    for i in range(player.system_lv):
        if i >= len(new_equip) or new_equip[i][0] is None:
            tmp += f"(空闲) "
        else:
            tmp += f"{new_equip[i][0]}{new_equip[i][1]} "
    return tmp


def test() -> str:
    log = "防御成长 当前等级 1\n"
    lv = 1
    skill: Skill = get_world_data().get_skill("防御成长")
    for i in range(90):
        lv = skill.skill_lv_up(lv, 5)
        log += f"打母猴{i}次 升级lv.{lv}\n"
    # lv=1
    # for i in range(10):
    #     lv = skill.skill_lv_up(lv, 30)
    #     log += f"打母猴{i}次 升级lv.{lv}\n"
    return log
