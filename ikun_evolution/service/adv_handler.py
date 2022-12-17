import datetime
import random
import re
import time
from datetime import datetime

from dateutil.relativedelta import relativedelta
from nonebot.adapters.onebot.v11 import GroupMessageEvent

from services import db
from .achievement_handler import add_achievement
from ..service.battle_handler import battle
from ..model.adv_model import ActionDB
from .game_handler import Map, get_world_data, Monster
from ..model.battle_log_model import BattleLogDB
from ..model.player_model import PlayerDB
from ..stream import Stream
from ..utils import add_item, get_uid


async def get_user_can_go(player: PlayerDB):
    names = []
    for key, game_map in get_world_data().mapList.items():
        if game_map.require_level > player.lv or not game_map.public:
            continue
        names.append(key)
    return names


async def get_user_status(event) -> [PlayerDB, list[str]]:
    player = await PlayerDB.get_player_by_uid(get_uid(event))
    status = await get_player_status(event)
    pos_list = await get_user_can_go(player)
    return player, status, pos_list


async def go_outside(event: GroupMessageEvent, pos: str) -> None:
    player: PlayerDB = await PlayerDB.get_player_by_uid(get_uid(event))
    other = {"atk": player.atk, "def": player.defe, "hp": player.hp, "spd": player.spd, "lv": player.lv,
             "skill": player.equip_skill, "sp": player.sp_skill, "base_lv": player.lv}
    t = datetime.now().strftime("%H:%M")
    action = await ActionDB.get_action_by_uid(get_uid(event))
    async with db.transaction():
        if action:
            await action.delete()
        await ActionDB.go_outside(get_uid(event), pos, other, f"🌄({t}){player.name}出发了！前去{pos}🔚")


async def get_player_status(event: GroupMessageEvent) -> str:
    action = await ActionDB.get_action_by_uid(get_uid(event))
    if action is not None and "go_home" not in action.other:
        return f"{action.action}"
    return "休息中"


async def query_status(event: GroupMessageEvent, pos: str) -> None:
    action = await ActionDB.get_action_by_uid(get_uid(event))


async def finish_action(event: GroupMessageEvent, checker) -> bool:
    action: ActionDB = await ActionDB.get_action_by_uid(get_uid(event))
    if not checker(action):
        return False
    # 把任务改成10天前触发的，这样就可以迅速完成了
    await action.update(start_time=action.start_time + relativedelta(days=-10),
                        update_time=action.update_time + relativedelta(days=-10)).apply()
    return True


async def query_last_log(event: GroupMessageEvent):
    action: ActionDB = await ActionDB.get_action_by_uid(get_uid(event))
    if not action:
        return ["你还在出发中"]
    return action.log.split("🔚")


# 计算从出发到现在已经经过了几步(一步为60min)  返回步数,到下一步所需时间
def cal_time(start_time, end_time=None) -> [int, float]:
    end_time = time.mktime(end_time.timetuple()) if end_time else time.time()

    # t = (end_time - time.mktime(start_time.timetuple())) // 2  # debug模式下30秒就有一个步骤
    t = (end_time - time.mktime(start_time.timetuple())) // 3600  # 计算经过了几个时间节点
    t2 = (end_time - time.mktime(start_time.timetuple())) % 3600 / 60  # 离下一个时间节点的时间

    return int(t), round(60 - t2, 1)


def check_access(i, player):
    tmp_map: Map = get_world_data().get_map(i["name"])
    # bag = json.load(player.bag)
    if tmp_map.require_level > player.lv:
        return False
    if tmp_map.require_item:
        for i in tmp_map.require_item.items():
            if player.query_item(i[0]) < i[1]:
                return False
    return True


# 根据角色当前的位置，结合其他信息，给出角色接下来要前去的位置。如果返回与当前位置相同的结果，视为停在原地没有移动
def get_random_pos(gmap: Map, player: PlayerDB):
    # 主逻辑
    tmp = Stream(gmap.owned_map).filter(lambda i: check_access(i, player)).to_list()
    if len(tmp) == 0:
        return gmap
    total = Stream(tmp).map(lambda t: t["weight"]).sum()
    total = total if total > 1 else 1  # 如果total大于1 一定会前往下一个区域 否则可能在原地徘徊
    ran = random.uniform(0, total)
    t: float = 0
    for m in tmp:
        t += m["weight"]
        if t >= ran:
            return get_world_data().get_map(m["name"])
    return gmap


def get_random_enemy(gmap: Map):
    if len(gmap.enemy_list) == 0:
        return None
    tmp = gmap.enemy_list
    total = Stream(tmp).map(lambda t: t["weight"]).sum()
    ran = random.uniform(0, total)
    t: float = 0
    for i in gmap.enemy_list:
        t += i["weight"]
        if t >= ran:
            enemy = get_world_data().get_enemy(i["name"])
            enemy.lv = i["lv"]
            return enemy
    return None


def get_item(gmap: Map):
    if len(gmap.item_list) == 0:
        return None, ""
    else:
        log = ""
        item_list = {}
        for i in gmap.item_list:
            log += f"找到了{i['name']} * {i['count']}\n"
            item_list[i['name']] = i['count']
        return item_list, log


def check_bag(cost, bag):
    for k, v in cost.items():
        if bag.get(k) is None:
            return False
        if bag.get(k) <= v:
            return False
    return True


def cost_bag(cost, bag):
    for k, v in cost.items():
        bag[k] -= v


async def cal_go_home(player: PlayerDB, adv: ActionDB):
    # 结算回家
    player.add_items(adv.item_get)
    await player.update(bag=player.bag, collection=player.collection).apply()
    adv.other["go_home"] = True
    await adv.update(other=adv.other).apply()


def get_skill_exp(our_skill: dict[str, float], enemy_skill: list[str]):
    log = ''
    total_compensate = 0.0
    for skill in enemy_skill:
        skill = re.findall(r'\D+', skill)[0]
        number = re.findall(r'\d+', skill)
        number = 1 if len(number) == 0 else int(number[0])
        tmp = our_skill.get(skill)
        tmp2 = get_world_data().get_skill(skill)

        if tmp is None:
            log += f'🆕习得了新技能{skill},初始等级{tmp2.min}\n'
            our_skill[skill] = tmp2.min
        elif tmp == tmp2.max:
            compensate = 0.08 / len(enemy_skill)
            total_compensate += compensate
            # log += f'🈵{skill}技能已经满级了，本该补偿{round(compensate, 3)}个小沙漏，但是为了控制进度不给了！\n'
            log += f'🈵{skill}技能已经满级了\n'
        else:
            lv = tmp2.skill_lv_up(tmp, number)
            log += f'⏫{skill}技能提升({tmp} → {lv})\n'
            our_skill[skill] = lv
    return our_skill, log, round(total_compensate, 2)

    pass


# 游戏采用懒更新 虽然玩家出发之后感觉每时每刻都在探索，但是实际上所有数据会在【玩家查询】的时刻再计算。
# 所以这个函数叫time_pass 他要计算出这段时间内发生了什么，代码非常非常的复杂，会修改多个数据库，他们被放在一个事务里，以确保一致性
async def adv_time_pass(event: GroupMessageEvent, force_go_home: bool = False) -> [str, bool]:
    # 获取所有需要的数据库（act,player）
    uid = get_uid(event)
    act: ActionDB = await ActionDB.get_action_by_uid(uid)
    if not act:
        return "你还没有出发呢！输入'出发'来出发吧", True
    player: PlayerDB = await PlayerDB.get_player_by_uid(uid)
    pos = get_world_data().get_map(act.position)

    if act.other.get("go_home", False):
        return act.log, True
    # 计算应该继续进行几个时间节点？
    tmp, _ = cal_time(act.start_time, act.update_time)
    already_move = min(10, tmp)  # 已经走的步数
    tmp, next_move_dif = cal_time(act.start_time)
    total_move = min(10, tmp)  # 从开始到现在的总步数
    times = total_move - already_move  # 相减即可获得这次需要更新几步

    log = act.log or ""
    defeated = None
    for i in range(20):  # 视为无限循环
        if i == 0 and already_move == 0:  # 刚出门的地方应该记下来
            add_item(player.arrived, act.position)

        if i >= times:
            break

        # 下一步去哪
        log, pos = find_next_step_pos(act, log, player, pos, not (already_move == 0 and i == 0))

        # 检查消耗
        if not check_bag(pos.cost, player.bag):
            log += f"😫没有以下物品：{pos.cost}，没法坚持下去了\n"
            break
        cost_bag(pos.cost, player.bag)  # 消耗的物品在探险时就已经消耗

        # 检查收获
        monster: Monster = get_random_enemy(pos)
        if monster is not None:
            log += f"⚠野生的{monster.name}(lv.{monster.lv})出现了！\n"
            result, battle_log = battle(act.other, player, monster)
            player.times = player.times + 1
            player.record_monster_meet(monster.name)
            # 记录战斗日志
            logdb = await BattleLogDB.record_battle(uid=get_uid(event),
                                                    our_name=player.name,
                                                    enemy_name=monster.name,
                                                    our_lv=act.other["lv"],
                                                    enemy_lv=monster.lv,
                                                    log={"log": battle_log},
                                                    battle_times=player.times)
            if result == '我方胜利':
                log += f"✌战斗胜利，战斗日志ID:{logdb.id}\n"
                # 战胜了就要拿东西
                if monster.lv >= act.other["lv"]:
                    log += f"🚩战胜强者，等级{act.other['lv']} → {act.other['lv'] + 1}\n"
                    act.other["lv"] = act.other["lv"] + 1
                if monster.ach is not None:
                    if result := await add_achievement(event, monster.ach, player.times):
                        log += f"🔚🏆获得成就【{result.name}】,你是第{result.order}只获得的因！\n"
                player.skill, tmp_log, compensate = get_skill_exp(player.skill, monster.skill)
                log += tmp_log
                player.record_monster_killed(monster.name)
                # player.add_item("小沙漏", compensate)
            else:
                log += f"💀战斗失败💀战斗日志ID:{logdb.id}\n输入'查询 id'可以查看战斗日志\n"
                if monster.hint:
                    meet = player.monster_meet.get(monster.name, 0)
                    killed = player.monster_killed.get(monster.name, 0)
                    d = meet - killed
                    if d < 3:
                        log += f"你已经被{monster.name}打死{d}次了，如果超过3次，就可以通过查询指令查询击败它的攻略\n"
                    if d >= 3:
                        log += f"分析成功，输入”查询{monster.name}可获取击杀攻略“\n"
                else:
                    log += f"这只怪物没有攻略，请自行挑战吧\n"
                defeated = i
                break

        item, _log = get_item(pos)
        log += _log
        if item is not None:
            player.add_items(item)
        log += "🔚"  # 特殊标志用来标记这条消息发送完毕，该换下一条消息了

    async with db.transaction():
        # 计算完毕 增加获得的对应物品 记一下日志
        await act.update(item_get=act.item_get, log=log, position=pos.name,
                         update_time=datetime.now(), other=act.other).apply()
        # 再去掉背包里的相关物品 更新exp和图鉴
        await player.update(bag=player.bag, arrived=player.arrived, skill=player.skill,
                            monster_killed=player.monster_killed, collection=player.collection,
                            times=player.times, monster_meet=player.monster_meet).apply()

        if defeated is not None:
            tmp = times - defeated - 1
            log += f"在你死亡后经过了{tmp}个时间点，作为补偿你获得了{tmp / 10}个沙漏🔚"
            player.add_item("小沙漏", tmp / 10)
            await cal_go_home(player, act)
            return log, True

        if total_move >= 10:  # 时间到了，该返回了
            log += f"☯诅咒的力量发作了。\n你回到了1级（无论如何，探索结束都会回到1级）🔚"
            await cal_go_home(player, act)
            return log, True

        if force_go_home:
            # 根据时间补沙漏
            perk = round((60 - next_move_dif) // 10 * 0.01, 2)
            log += f"强行返回，已经挂机的{round(60 - next_move_dif)}分钟转换为{perk}个小沙漏🔚"
            player.add_item("小沙漏", perk)
            await cal_go_home(player, act)
            return log, True

    return log + f"下一个步骤还要等{next_move_dif}分钟，至多还可挂机{10 - total_move}个步骤，要强行返回的话请输入【强行返回】，要加速完成可使用沙漏", False


def find_next_step_pos(act, log, player, pos, can_stay):
    new_pos = pos
    # 检查去了哪里
    if len(pos.owned_map) == 0 and not act.other.get("is_end", False):
        log += f"🏁已经来到了区域的终点\n"
        act.other["is_end"] = True
    if len(pos.owned_map) >= 1:
        new_pos: Map = get_random_pos(pos, player)
        if bool(new_pos.enemy_list) and new_pos.get_max_enemy_level() >= player.buff.get("stay", 999) and can_stay:
            new_pos = pos  # 下一个地区怪物等级太高，启用驻留
            log += f"⚓驻留中...\n"
            act.other["stay"] = True
        elif new_pos != pos:
            log += f"🐥来到了{new_pos.name}...\n"
        elif act.other.get("stay", False):
            log += f"⚓驻留中...\n"
        else:
            log += f"😵没有找到去下一层的路\n"
    add_item(player.arrived, new_pos.name)
    return log, new_pos


async def should_speed_up_cost(event):
    act = await ActionDB.get_action_by_uid(get_uid(event))
    a, next_move_dif = cal_time(act.start_time)
    total_move = min(10, a)
    if total_move < 10:
        cost = 1 - total_move / 10
        return round(cost - 0.1 + next_move_dif / 600, 2)
    return 0
