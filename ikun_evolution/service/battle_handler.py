import math

from ..model.battle_log_model import BattleLogDB
from ..model.player_model import PlayerDB
from .game_handler import get_world_data, Monster
from ..utils import get_uid
from ..xiaor_battle_system.src.gameBoard import GameBoard
from ..xiaor_battle_system.src.logger import Logger
from ..xiaor_battle_system.src.msgManager import MsgManager
from ..xiaor_battle_system.src.pokemon import Pokemon
from ..xiaor_battle_system.src.tools.tools import get_container

container = get_container()
# 单例声明
logger = container[Logger] = Logger()
msgManager = container[MsgManager] = MsgManager(container[Logger])
gameBoard = container[GameBoard] = GameBoard(container[Logger], container[MsgManager])


# 调用战斗模块 不知道性能开销有多大...如果太大我再优化一下
def get_player_skill(player, param: list[str]):
    skill = []
    for name in param:
        if name is None:
            continue
        skill.append(name + str(math.floor(int(player.skill.get(name)))))
    return skill


def battle(data: dict, player: PlayerDB, enemy: Monster):
    msgManager.clean()
    logger.clean()
    pkm1 = container[Pokemon]
    pkm2 = container[Pokemon]

    # 升级就是双方各自乘以1.1倍的数据，和每升级可谓是毫无区别，但是想必会给玩家自己变强的错觉罢
    pkm1.name = player.name
    pkm1.MAX_HP = data["hp"]
    pkm1.ATK = data["atk"]
    pkm1.DEF = data["def"]
    pkm1.SPD = data["spd"]
    pkm1.lv = data["lv"]
    lv = data.get("base_lv", player.lv)
    pkm1.baselv = lv
    pkm1.fakebaselv = lv
    # 技能处理这里稍微复杂一点
    # 首先是玩家自带的技能
    pkm1.skillGroup = get_player_skill(player, data["skill"])
    # 然后是可能存在的地图技能（但是目前并不存在，不写了）
    # sp技能（也不存在，以后再写）
    if "游泳" not in data["skill"] and player.query_item("乌龟护符") >= 0.99:    # 本赛季没有装备系统，写个特判
        pkm1.skillGroup.append("游泳5")

    pkm2.name = enemy.name
    pkm2.MAX_HP = enemy.hp
    pkm2.ATK = enemy.atk
    pkm2.DEF = enemy.defe
    pkm2.SPD = enemy.spd
    pkm2.lv = enemy.lv
    pkm2.baselv = enemy.baselv
    pkm2.fakebaselv = 1
    pkm2.skillGroup = enemy.sp_skill + enemy.skill

    gameBoard.add_ally(pkm1)
    gameBoard.add_enemy(pkm2)
    gameBoard.init()
    result = gameBoard.battle()
    return result, logger.get_log()


async def query_battle_log(id: str):
    log: BattleLogDB = await BattleLogDB.query_by_id(int(id))
    if log is None:
        return '未查到该场战斗'
    times = log.battle_times if log.battle_times != 0 else '?'
    battle_log = log.log["log"].split("🔚")
    tmp = [("战报播放系统",
         f"{log.our_name}(等级{log.our_lv})的第{times}次战斗\n对手：{log.enemy_name}(等级{log.enemy_lv})\n")]
    for l in battle_log:
        tmp.append(("战斗详情", l))
    return tmp


# 查询一个角色战斗的次数
# 因为战斗日志表是脏表所以这个查询毫无意义，但是写了也不至于删掉
async def query_battle_times(uid):
    num: int = await BattleLogDB.query_log_count(uid)
    from nonebot.log import logger
    logger.info(f"{uid}我出征了{num}次")
    return num


async def foo():
    return
    players: list[PlayerDB] = await PlayerDB.get_all()
    for player in players:
        if "防御成长" in player.skill:
            lv = player.skill["防御成长"]
            if round(lv, 2) >= 1.2 * 1.2 * 6:
                player.skill["防御成长"] = 6
            else:
                lv = round(lv / 1.2 / 1.2, 2)
            player.skill["防御成长"] = lv
            await player.update(skill=player.skill).apply()


async def sim_battle(event, our_lv, enemy_lv, enemy_name):
    player = await PlayerDB.get_player_by_uid(get_uid(event))
    enemy = get_world_data().get_enemy(enemy_name)
    msgManager.clean()
    logger.clean()
    pkm1 = container[Pokemon]
    pkm2 = container[Pokemon]
    pkm1.name = player.name
    pkm1.MAX_HP = player.hp
    pkm1.ATK = player.atk
    pkm1.DEF = player.defe
    pkm1.SPD = player.spd
    pkm1.lv = int(our_lv)
    pkm1.baselv = player.lv
    pkm1.fakebaselv = player.lv
    # 技能处理这里稍微复杂一点
    # 首先是玩家自带的技能
    pkm1.skillGroup = get_player_skill(player, player.equip_skill)
    # 然后是可能存在的地图技能（但是目前并不存在，不写了）
    # sp技能（也不存在，以后再写）

    pkm2.name = enemy.name
    pkm2.MAX_HP = enemy.hp
    pkm2.ATK = enemy.atk
    pkm2.DEF = enemy.defe
    pkm2.SPD = enemy.spd
    pkm2.lv = int(enemy_lv)
    pkm2.baselv = enemy.baselv
    pkm2.fakebaselv = 1
    pkm2.skillGroup = enemy.sp_skill + enemy.skill

    gameBoard.add_ally(pkm1)
    gameBoard.add_enemy(pkm2)
    gameBoard.init()
    result = gameBoard.battle()
    return logger.get_log()
