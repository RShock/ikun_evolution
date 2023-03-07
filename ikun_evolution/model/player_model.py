from ..stream import Stream
from ..utils import add_item, add_items
from .gino_db import db
from datetime import datetime
from services.log import logger


class PlayerDB(db.Model):
    __tablename__ = "ikun_player"

    id: int = db.Column(db.Integer(), primary_key=True)
    # 角色ID
    uid: str = db.Column(db.String(), nullable=False)
    # 角色名字
    name: str = db.Column(db.String(), nullable=False)
    # 攻击力
    atk: str = db.Column(db.Integer(), nullable=False)
    # 防御力
    defe: str = db.Column(db.Integer(), nullable=False)
    # 生命值
    hp: str = db.Column(db.Integer(), nullable=False)
    # 速度
    spd: str = db.Column(db.Integer(), nullable=False)
    # 头像
    head: str = db.Column(db.String(), nullable=False)
    # 探险等级（每去过一个地方，等级就会+1）
    adv_lv: int = db.Column(db.Integer(), nullable=False)
    # 系统等级（影响可同时装备的技能数量）
    system_lv: int = db.Column(db.Integer(), default=1)
    # 角色等级
    lv: int = db.Column(db.Integer(), nullable=False)
    # 已装备技能
    equip_skill: list[str] = db.Column(db.JSON(), nullable=False, default=[])
    # 技能
    skill = db.Column(db.JSON(), nullable=False, default={})
    # 体质
    sp_skill = db.Column(db.JSON(), nullable=False, default={})
    # 背包
    bag: dict[str, int] = db.Column(db.JSON(), nullable=False, default={'IKUN图册': 1})
    # buff
    buff = db.Column(db.JSON(), nullable=False, default={})
    # 箱子
    box = db.Column(db.JSON(), nullable=False, default={})
    # 击杀怪物的次数（起名是历史问题）
    monster_killed = db.Column(db.JSON(), nullable=False, default={})
    # 遇见怪物的次数
    monster_meet = db.Column(db.JSON(), nullable=False, default={})
    # 游历地点收集
    arrived = db.Column(db.JSON(), nullable=False, default={})
    # 角色标签
    tag = db.Column(db.JSON(), nullable=False, default={})
    # 角色称号
    honor = db.Column(db.JSON(), nullable=False, default={})
    # 出生时间
    create_time = db.Column(db.DateTime(), default=datetime.now)
    # 来自群
    group_id = db.Column(db.BigInteger(), default=0)
    # 已经完成的任务
    complete_mission = db.Column(db.JSON(), nullable=False, default={})
    # 游玩了多少个时点
    times = db.Column(db.Integer(), nullable=False, default=0)
    # 图鉴（暂时不在使用）
    collection = db.Column(db.JSON(), nullable=False, default={'IKUN图册': 1})
    # 缺省字段
    reverse1 = db.Column(db.JSON(), nullable=True, default={})
    reverse2 = db.Column(db.JSON(), nullable=True, default={})
    reverse3 = db.Column(db.JSON(), nullable=True, default={})

    @classmethod
    async def get_player_by_name(
            cls,
            name: str,
    ) -> "PlayerDB":
        try:
            async with db.transaction():
                return await cls.query.where(cls.name == name).gino.first()
        except Exception as e:
            logger.info(f"根据角色名字查询数据库出错 {type(e)}: {e}")

    @classmethod
    async def get_player_by_uid(
            cls,
            uid: str,
    ) -> "PlayerDB":
        try:
            async with db.transaction():
                player = await cls.query.where(cls.uid == uid).gino.first()
                if player is None:
                    logger.info(f"未查询到角色 可能是在注册 查询id为{uid}")
                return player
        except Exception as e:
            logger.info(f"根据角色uid查询数据库出错 {type(e)}: {e}")

    @classmethod
    async def register(cls, uid: str, group_id: int, name: str, head_choose: str) -> int:
        try:
            async with db.transaction():
                logger.info(f"{name}加入游戏")
                await cls.create(uid=uid, name=name, head=head_choose, adv_lv=0, system_lv=1, lv=1, group_id=group_id,
                                 atk=20, defe=10, hp=100, spd=0, sp_skill={'吞天者': 1})
                return await db.func.count(cls.id).gino.scalar()  # 虽然不需要，但是应该是具备性能的写法
        except Exception as e:
            logger.info(f"新增角色出错 {type(e)}: {e}")

    @classmethod
    async def set_status(cls, uid: str, status: str) -> None:
        try:
            async with db.transaction():
                s = await cls.get_player_by_uid(uid)
                await s.update(status=status).apply()
        except Exception as e:
            logger.info(f"设置角色状态出错 {type(e)}: {e}")

    @classmethod
    async def get_all(cls) -> list["PlayerDB"]:
        try:
            async with db.transaction():
                return await PlayerDB.query.gino.all()
        except Exception as e:
            logger.info(f"查询所有角色出错 {type(e)}: {e}")

    # 注意 add完仍然需要update哦
    def add_item(self, name, cnt):
        add_item(self.bag, name, cnt)
        add_item(self.collection, name, cnt)

    def add_items(self, items) -> "PlayerDB":
        self.bag = add_items(self.bag, items)
        self.collection = add_items(self.collection, items)
        return self

    def show_bag(self) -> str:
        if len(self.bag) != 0:
            return Stream(self.bag.items()).map(lambda i: f"{i[0]} x{i[1]}\n").reduce(lambda s1, s2: s1 + s2, '')
        return "没有任何物品"

    def show_equip(self) -> str:
        if len(self.equip) != 0:
            return Stream(self.equip.items()).map(lambda i: f"{i[0]}: {i[1]}\n").reduce(lambda s1, s2: s1 + s2, '')
        return "没穿任何装备"

    # 需要在外部检查物品数量是否足够
    def cost_item(self, item_name, num=1):
        if self.bag.get(item_name, 0) >= num:
            self.bag[item_name] -= num
            if self.bag.get(item_name) == 0:
                self.bag.pop(item_name)
            return True
        else:
            logger.warning(f"使用{item_name}时发现物品不足")
            return False

    def cost_items(self, items: dict[str, int]):
        for i in items.items():
            self.cost_item(i[0], i[1])

    def query_item(self, item_name):
        return self.bag.get(item_name, 0)

    def query_arrived(self, name):
        return self.arrived.get(name, 0)

    def query_skill(self, skill_name):
        return self.skill.get(skill_name, 0)

    def query_skill_fuzzy(self, skill_name):
        return Stream(self.skill.keys()).filter(lambda k: skill_name in k).find_first()

    def get_bag(self) -> dict[str, int]:
        return self.bag

    # 装备系统暂时已经删除了
    def get_equip(self, _type) -> str:
        return self.equip.get(_type)

    def wear(self, _type, name):
        self.equip[_type] = name
        self.cost_item(name)

    def unwear(self, _type, name):
        # 这里的添加不会增加图鉴计数，所以不能直接调用playerDB.add_item
        add_item(self.bag, name, 1)
        self.equip.pop(_type)

    def record_monster_killed(self, monster_name):
        add_item(self.monster_killed, monster_name, 1)

    def record_monster_meet(self, monster_name):
        add_item(self.monster_meet, monster_name, 1)
