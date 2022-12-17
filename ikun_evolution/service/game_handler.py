import math
import tarfile
import unittest

from services.log import logger
import json5
import os

from ..stream import Stream


class Map:
    name = '未定义地图'  # 地图名称
    enemy_list = []  # 地图拥有的敌人和概率
    item_list = []  # 地图拥有的道具
    owned_map = []  # 子地图
    require_level = 1  # 地图需要的探索等级
    require_honor = {}  # 地图需要的特别称号
    require_buff = {}  # 地图需要的特别buff
    require_item = {}  # 地图需要的特别物品
    cost = {}  # 地图的消耗
    public = True  # 是否直接可达
    description = "无"

    def get_max_enemy_level(self):
        return max(self.enemy_list, key=lambda l: l["lv"])["lv"]


class Item:
    name = '未定义物品'  # 地图名称
    description = "未填写"
    cost = None  # 如果填写cost 就会被商店出售
    lv = 0
    usable = False
    equip_type = None

    def simple_name(self):
        return f"{self.name}(Lv.{self.lv})"


class Compose:
    name = '未定义合成表'
    lv: 1
    type = '熔炼'
    consume = []
    produce = []


class Mission:
    name = None  # 名称
    type = None  # 类型 主线or支线
    type2: str = "一次"  # 能做几次以及类似特性
    hide_reward: bool = False
    des = '未定义任务描述'
    tar = '未定义任务目标'
    check = {}
    hint = '未定义任务提示'
    reward_str = '未定义任务奖励'
    reward: dict[str, int] = {}
    finish_str = None  # 任务完成后说的话
    next = '下一个任务'


class Monster:
    name: str
    lv: int
    atk: int
    hp: int
    defe: int
    ach: str  # 打败他获得的成就，只能获得一次
    spd: int
    des: str  # 怪物描述
    baselv: int  # 填表时填1级怪 会因为怪物等级不是1级失真 baselv设为5就可以填5级数据了
    skill: list[str]
    sp_skill: list[str]  # 体质 没法被吃掉
    hint: str  # 攻略
    # mod_skill: list[str]  # 补正技能（来自地图 活动等）没法被吃掉


class Skill:
    name: str  # 技能名字
    min: int  # 技能最低等级，获得技能时就在这个等级
    max: int  # 最高等级
    des: str  # 技能描述，玩家用查询就可以看到
    exp: int  # 升满级所需要的exp
    eatable: bool  # 可不可以被主角吃掉，极少数技能无法被吃掉
    emoji: str  # 技能的图标
    sp: bool  # 是否是体质技能

    def lv_to_exp(self, lv: float) -> float:
        total_lv = self.max - self.min
        lv -= self.min
        return lv * lv * self.exp / total_lv / total_lv

    # 输入当前技能等级 与 吃掉怪物的技能等级 输出 吃掉怪物后的技能等级（小数视为升级进度）
    def skill_lv_up(self, lv: float, exp: float) -> float:
        # 技能等级与吞食次数的关系可以粗略参考 技能配置.json5
        total_lv = self.max - self.min
        if total_lv == 0:
            return 1
        if self.exp == 0:
            self.exp = 1

        def exp_to_lv(exp: float) -> float:
            return math.sqrt(exp * total_lv * total_lv / self.exp) + self.min

        exp = (exp - self.min) / total_lv + 1
        exp = 1 if exp <= 1 else exp
        new_lv = exp_to_lv(self.lv_to_exp(lv) + exp)
        new_lv = self.max if new_lv >= self.max else new_lv
        if total_lv <= 5:  # 这种技能升级缓慢 2位小数无法准确标示精确粒度
            return round(new_lv, 3)
        return round(new_lv, 2)

    # 获取到下一级还需要多少经验值
    def get_next_lv_exp(self, lv: float) -> float:
        if lv >= self.max:
            return 0
        next_lv = int(lv) + 1
        return round(self.lv_to_exp(next_lv) - self.lv_to_exp(lv), 2)

    # 获取到满级还需要多少经验值
    def get_max_lv_exp(self, lv: float) -> float:
        if lv >= self.max:
            return 0
        next_lv = self.max
        return round(self.lv_to_exp(next_lv) - self.lv_to_exp(lv), 2)

    def format_1_line_detail(self, lv: float):
        if self.sp:
            return f"{self.emoji}{self.name}\n"
        if self.exp == 0:
            return f"{self.emoji}{self.name} 🈵\n"
        tmp = '▁▂▃▄▅▆▇█🈵'
        diff = self.max - self.min
        if diff <= 0:
            percent = '🈵'
        else:
            percent = tmp[int(self.lv_to_exp(lv) * 8) // self.exp]
        return f"{self.emoji}{self.name} lv{lv}/{self.max}{percent}\n"


class Help:
    type: str  # 种类 目前有图片型 消息型2种
    question: str  # 问题
    ans = ""  # 回答 str or list[str]
    name: str  # 消息名称
    pos: int  # 帮助在栏目中的位置


class WorldInfo:
    mapList: dict[str, Map]
    itemList: dict[str, Item]
    forgeList: list[Compose]
    missionList: dict[str, Mission]
    enemyList: dict[str, Monster]
    skillList: dict[str, Skill]
    helpList: dict[int, Help]

    def get_item(self, name) -> Item:
        return self.itemList.get(name)

    def get_map(self, name) -> Map:
        return self.mapList.get(name)

    def get_shop_item(self):  # 如果填写cost 就会被商店出售
        return Stream(self.itemList.items()).map(lambda i: i[1]).filter(lambda i: i.cost).to_list()

    def get_forge_list(self) -> list[Compose]:
        return self.forgeList

    def get_forge(self, name: str):
        return Stream(self.forgeList).filter(lambda f: f.name == name).find_first()

    def get_mission_list(self) -> dict[str, Mission]:
        return self.missionList

    def get_mission(self, name) -> Mission:
        return self.missionList.get(name)

    def get_enemy(self, name) -> Monster:
        return self.enemyList.get(name)

    def get_skill(self, name) -> Skill:
        return self.skillList.get(name)

    def get_help_question(self) -> list[str]:
        return [f"{q.pos}. {q.question}" for q in self.helpList.values()]

    def get_help_answer(self, pos):
        return self.helpList.get(pos)


world_data: WorldInfo


def get_world_data() -> WorldInfo:
    return world_data


######### Extract all files from src_dir to des_dir
def extract_tar_files(src_dir, des_dir):
    files = os.listdir(src_dir)
    for file in files:
        dir_tmp = os.path.join(src_dir, file)
        if not os.path.isdir(dir_tmp):  ##是文件，非文件夹
            # 解压特定文件
            if dir_tmp.endswith("gamedata"):
                # f = zipfile.ZipFile(dir_tmp, mode="r")
                f = tarfile.open(dir_tmp)
                names = f.getnames()
                for name in names:
                    f.extract(name, path=des_dir)
                return
        else:
            extract_tar_files(dir_tmp, des_dir)
    return 0


async def load_world_data() -> None:
    global world_data
    world_data = WorldInfo()
    logger.info(f'【只因进化录】资源载入中')
    path = os.path.dirname(__file__) + '/../gamedata/json/'
    path2 = os.path.dirname(__file__) + '/../gamedata/'
    files = os.listdir(path)
    extract_tar_files(path2, path)
    for file in files:
        try:
            with open(f'{path}{file}', "r", encoding="utf-8") as f:
                if file == '地图.json5':
                    world_data.mapList = parse_map(json5.load(f))
                    logger.info(f'【只因进化录】地图载入完成，共{len(world_data.mapList)}张地图')
                if file == '物品.json5':
                    world_data.itemList = parse_item(json5.load(f))
                    logger.info(f'【只因进化录】物品载入完成，共{len(world_data.itemList)}个物品')
                if file == '制作表.json5':
                    world_data.forgeList = parse_compose(json5.load(f))
                    logger.info(f'【只因进化录】制作表载入完成，共{len(world_data.forgeList)}个配方')
                if file == '任务.json5':
                    world_data.missionList = parse_mission(json5.load(f))
                    logger.info(f'【只因进化录】任务载入完成，共{len(world_data.missionList)}个任务')
                if file == '敌人.json5':
                    world_data.enemyList = parse_enemy(json5.load(f))
                    logger.info(f'【只因进化录】敌人载入完成，共{len(world_data.enemyList)}个敌人')
                if file == '技能配置.json5':
                    world_data.skillList = parse_skill(json5.load(f))
                    logger.info(f'【只因进化录】技能载入完成，共{len(world_data.skillList)}个技能')
                if file == "帮助.json5":
                    world_data.helpList = parse_help(json5.load(f))
                    logger.info(f'【只因进化录】帮助载入完成，共{len(world_data.helpList)}条帮助')
        except Exception as e:
            logger.error(str(e))
            logger.error("读取失败，请修改后使用重载配置命令重新加载！")

    # 校验制作表内的道具是否在物品栏内 稍微有点废资源 问题不大 制作功能暂时关闭了
    # for j in world_data.forgeList:
    #     for i in j.consume:
    #         if get_world_data().get_item(i["name"]) is None:
    #             logger.warning(f"制作表内出现未知道具:{i['name']}")
    #     for i in j.produce:
    #         if get_world_data().get_item(i["name"]) is None:
    #             logger.warning(f"制作表内出现未知道具:{i['name']}")


def parse_map(map_json):
    map_dict = {}
    for key, value in map_json.items():
        mp = Map()
        mp.name = key
        mp.require_level = value["require_level"]
        mp.owned_map = value.get("owned") or []  # 可为空 下同
        mp.enemy_list = value.get("enemy_list", [])
        mp.public = value["public"]
        mp.require_honor = value.get("require_honor", {})
        mp.require_buff = value.get("require_buff", {})
        mp.require_item = value.get("require_item", {})
        mp.item_list = value.get("item_list", {})
        mp.description = value.get("description", None)
        mp.cost = value.get("cost", {})
        map_dict[key] = mp

        if not isinstance(mp.owned_map, list):
            logger.warning(f"地图类型疑似错误：{mp.owned_map}")
        if not isinstance(mp.enemy_list, list):
            logger.warning(f"地图类型疑似错误：{mp.enemy_list}")
    return map_dict


def parse_item(item_json):
    item_dict = {}
    for key, value in item_json.items():
        item = Item()
        item.name = key
        item.description = value["des"]
        item.lv = value["lv"]
        item.usable = value.get("usable")
        item.cost = value.get("cost")
        item.equip_type = value.get('equip_type')
        item.is_book = value.get('is_book')
        item_dict[key] = item

    return item_dict


def parse_compose(compose_json):
    compose_list = []
    for v in compose_json:
        comp = Compose()
        comp.name = v["name"]
        comp.lv = v["lv"]
        comp.type = v.get("type", "熔炼")
        comp.consume = v["consume"]
        comp.produce = v["produce"]
        compose_list.append(comp)

    return compose_list


def parse_mission(mission_json):
    mission_dict = {}
    for v in mission_json:
        mission = Mission()
        mission.name = v["name"]
        mission.type = v["type"]
        if not mission.type in ["主线", "支线", "世界任务"]:
            logger.warning(f"未知任务类型{mission.type}")
        mission.type2 = v.get("type2", "不可领取")  # 多半是某个任务链的后续任务，会在完成前面的任务时自动领取
        mission.des = v["des"]
        mission.tar = v["tar"]
        mission.hint = v["hint"]
        mission.reward = v.get("reward", {})
        mission.reward_str = v.get("reward_str", "未知")
        mission.next = v.get("next")
        mission.check = v["check"]
        mission.hide_reward = v.get("hide_reward")
        mission.finish_str = v.get("finish_str")
        mission_dict[mission.name] = mission

    return mission_dict


def parse_enemy(enemy_json):
    enemy_dict = {}
    for v in enemy_json:
        monster = Monster()
        monster.name = v["name"]
        monster.atk = int(v["atk"])
        monster.defe = int(v["def"])
        monster.spd = int(v["spd"])
        monster.hp = int(v["hp"])
        monster.skill = v["skill"]
        monster.baselv = v.get("baselv", 1)
        monster.des = v.get("des", "作者很懒，还没有为它添加描述")
        monster.sp_skill = v.get("sp", [])
        monster.ach = v.get("ach", None)
        monster.hint = v.get("hint", None)
        enemy_dict[monster.name] = monster

    return enemy_dict


def parse_skill(skill_json):
    skill_dict = {}
    for v in skill_json:
        skill = Skill()
        skill.name = v["name"]
        skill.min = int(v.get("min", 0))
        skill.max = int(v.get("max", 0))
        skill.exp = int(v.get("exp", 0))
        skill.des = v["des"]
        skill.eatable = v.get("eatable", True)
        skill.emoji = v.get("emoji", "❔")
        skill.sp = v.get("sp", False)
        skill_dict[skill.name] = skill

    return skill_dict


def parse_help(help_json):
    help_dict = {}
    i = 1
    for v in help_json:
        help: Help = Help()
        help.type = v["type"]
        help.question = v["question"]
        help.ans = v["ans"]
        help.name = v.get("name", "系统帮助")
        help.pos = v.get("pos", i)
        help_dict[i] = help
        i += 1
    return help_dict


# 跑不起来的测试，气死了
class TestCases(unittest.TestCase):
    def testA(self):
        print("pass")
        self.assertEqual("A", "A")
