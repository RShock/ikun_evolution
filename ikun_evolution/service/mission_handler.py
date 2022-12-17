from nonebot.adapters.onebot.v11 import GroupMessageEvent

from services import db
from .achievement_handler import add_achievement
from ..service.adv_handler import get_player_status
from .game_handler import Mission
from .game_handler import get_world_data
from ..model.mission_model import MissionDB
from .player_handler import get_player
from ..model.player_model import PlayerDB
from ..stream import Stream
from ..utils import get_uid


async def get_available_mission(event) -> [list[Mission], str]:
    player: PlayerDB = await get_player(event)
    ms: dict[str, Mission] = get_world_data().get_mission_list()  # 所有任务列表
    am: list[str] = await MissionDB.get_all_received_mission(player.uid)  # 所有已经完成的且只能完成一次的任务的列表

    def checker(mission: Mission):
        if mission.name in am and mission.type2 == '一次' or mission.type2 == '不可领取':
            return False
        return True

    ms2: list[Mission] = Stream(ms.values()).filter(lambda m: checker(m)).to_list()
    tmp = '请选择要领取的任务:\n0: 我不做了\n'
    for i, j in enumerate(ms2):
        tmp += f'{i + 1}: {j.name}\n'
    return ms2, tmp


async def handle_receive_mission(event: GroupMessageEvent, mission: Mission):
    player: PlayerDB = await get_player(event)
    await MissionDB.receive_mission(player.name, get_uid(event), event.group_id, mission.name, mission.type,
                                    mission.type2)
    return [("超级吞噬系统", f"{player.name}成功领取任务：{mission.name}"),
            ("任务描述", mission.des),
            ("任务目标", mission.tar),
            ("任务提示", mission.hint),
            ("任务奖励", mission.reward_str)]


# 返回值 ms 任务列表 tmp 任务描述字符串 flg 领取了重复任务的故障检测
async def get_submitable_mission(event: GroupMessageEvent):
    ms = await MissionDB.get_all_in_progress_mission(get_uid(event))
    tmp = '请选择任务:\n0: 关闭\n'
    # 检查重复元素，防止有人卡bug多次领取任务
    collect = []
    for i, j in enumerate(ms):
        tmp += f'{i + 1}: {j.name}\n'
        collect.append(j.name)
    collect_set = set(collect)
    flg = True
    if len(collect) != len(collect_set):
        tmp += "警告，检测到重复领取相同任务，这可能是系统bug导致的。为了正常游戏体验，请使用删除任务指令删除多余的任务，" \
               "在此之前你将无法提交任务，下面是每个任务对应的‘真实编号’，请使用'删除任务 真实编号'指令清除多余任务，该操作危险，请正确操作。"
        flg = False
        for i, j in enumerate(ms):
            tmp += f'ID {j.id}: {j.name}\n'
    return ms, tmp, flg


async def get_short_submitable_mission(event: GroupMessageEvent):
    ms = await MissionDB.get_all_in_progress_mission(get_uid(event))
    return f"待完成的任务：{', '.join(m.name for m in ms)}\n"


def check_item(item, player):
    for i in item:
        if i["num"] > player.query_item(i["name"]):
            return False
    return True


# def check_equip(equip, player:PlayerDB):
#     for i in equip:
#         if not player.equip.get(i):
#             return False
#     return True


def check_skill(skill, player: PlayerDB):
    for i in skill:
        if i["num"] > player.query_skill(i["name"]):
            return False
    return True


# todo
def check_equip_skill_num(num, player):
    return len(player.equip_skill) >= int(num)


async def handle_submit_mission(event: GroupMessageEvent, ms: MissionDB):
    mission: Mission = get_world_data().get_mission(ms.name)
    player: PlayerDB = await get_player(event)
    # step1 根据时间更新任务事件的变化
    # 还没做
    # step2 检查任务类型
    if item := mission.check.get("check_item"):  # 具备型
        if check_item(item, player):
            return await handle_complete(event, mission, ms, player)
        else:
            return f"任务要求的物品你还没有完成！"

    if skill := mission.check.get("check_skill"):  # 吞食技能型
        if check_skill(skill, player):
            return await handle_complete(event, mission, ms, player)
        else:
            return f"任务要求的技能你还没有取得！"

    if status := mission.check.get("player_status"):  # 状态型
        if await get_player_status(event) == status:
            return await handle_complete(event, mission, ms, player)
        else:
            return f"你还不处于{status}状态哦\n"

    if arrived := mission.check.get("player_arrived"):  # 经历型
        for ar in arrived:
            if player.arrived.get(ar) is None:
                return f"你还没去过{ar}呢！\n"
        return await handle_complete(event, mission, ms, player)

    if require_item := mission.check.get("require_item"):  # 索取型
        if check_item(require_item, player):
            player.cost_items(require_item)
            return await handle_complete(event, mission, ms, player)
        else:
            return f"任务要求的物品你还没有完成！"

    if num := mission.check.get("check_equip_skill_num"):  # 检查装备了几个技能（这种东西真的能复用吗）
        if check_equip_skill_num(num, player):
            return await handle_complete(event, mission, ms, player)
        else:
            return f"你还没有装备上技能！"

    if monster_list := mission.check.get("monster_killed"):
        if t := check_killed(monster_list, player):
            return f"你还没有击杀{t}呢"
        else:
            return await handle_complete(event, mission, ms, player)
    # if equip := mission.check.get("check_equip"):  # 装备检查型
    #     if check_equip(equip, player):
    #         return await handle_complete(event, mission, ms, player)
    #     else:
    #         return f"任务要求的物品你还没有完成！"

    if mission.check.get("impossible"):
        return "这个任务无法完成"

    return "未知错误..."

    # step3 更新日志 反馈


async def handle_complete(event, mission: Mission, ms, player):
    async with db.transaction():
        ans = []
        if mission.finish_str:
            ans += mission.finish_str + '\n'
        await ms.update(status="已完成").apply()
        ans.append(("超级吞噬系统", f"任务【{mission.name}】完成\n"))
        if len(mission.reward) != 0:
            for i in mission.reward.items():
                if i[0] == '系统等级':
                    player.system_lv = player.system_lv + int(i[1])
                    ans.append(("任务奖励", f"系统等级提升，现在可以装备{player.system_lv}个技能了"))
                elif i[0].startswith('称号'):
                    # 称号系统会记录每个人获得的先后
                    arc = await add_achievement(event, i[0][3:], player.times)
                    ans.append(("解锁成就", f"获得{i[0]}，你是第{arc.order}只解锁该称号的因！"))
                else:
                    ans.append(("任务奖励", f"获得 {i[0]} x{i[1]}"))
                    player.add_item(i[0], int(i[1]))
            await player.update(bag=player.bag, collection=player.collection, system_lv=player.system_lv).apply()
        if next_str := mission.next:
            tmp = await handle_receive_mission(event, get_world_data().get_mission(next_str))
            ans += tmp
        return ans


async def handle_look_mission(ms: MissionDB):
    mission: Mission = get_world_data().get_mission(ms.name)
    return [("任务名称", mission.name), ("任务描述", mission.des), ("任务目标", mission.tar), ("任务提示", mission.hint)]


async def handle_del_mission(event: GroupMessageEvent, id: int):
    mission: MissionDB = await MissionDB.get_mission_by_id(id)
    if mission.uid != get_uid(event):
        return "这个任务不是你的！"
    if mission.status == '已完成':
        return "请勿删除已完成的任务"
    await mission.delete()
    return "删除成功..."


def check_killed(monsterlist: dict[str, int], player: PlayerDB):
    killed = player.monster_killed
    for mon, num in monsterlist.items():
        if killed.get(mon, 0) < num:
            return f"{mon}{num}次"

    return None
