from .gino_db import db
from datetime import datetime
from services.log import logger


class MissionDB(db.Model):
    __tablename__ = "ikun_mission"

    id: int = db.Column(db.Integer(), primary_key=True)
    # 角色ID
    uid = db.Column(db.String(), nullable=False)
    # 群ID
    group_id = db.Column(db.Integer(), nullable=False)
    # 任务名称
    name = db.Column(db.String(), nullable=False)
    # 什么时候去的
    start_time = db.Column(db.DateTime(), default=datetime.now)
    # 懒更新时间
    update_time = db.Column(db.DateTime(), default=datetime.now)
    # 已经提交的物品
    submit_item = db.Column(db.JSON(), nullable=True, default={})
    # 日志
    log = db.Column(db.String(), nullable=False, default="")
    # 完成状态
    status = db.Column(db.String(), nullable=False, default="")
    # 任务类型(主线 支线等等)
    type = db.Column(db.String(), nullable=False)
    # 任务类型(一次 每日等等)
    type2 = db.Column(db.String(), nullable=False)
    # 缺省字段
    reverse1 = db.Column(db.JSON(), nullable=True, default={})
    reverse2 = db.Column(db.JSON(), nullable=True, default={})
    reverse3 = db.Column(db.JSON(), nullable=True, default={})

    @classmethod
    async def receive_mission(cls, player_name: str, uid: str, group_id: int, name: str, type, type2) -> "MissionDB":
        try:
            async with db.transaction():
                return await cls.create(uid=uid, group_id=group_id, name=name, submit_item={},
                                        log=f"{player_name}开始了这个任务\n", type=type, type2=type2, status="进行中")
        except Exception as e:
            logger.info(f"领取任务出错 {type(e)}: {e}")

    @classmethod
    async def get_mission(cls, uid: str, name: str) -> "MissionDB":
        try:
            async with db.transaction():
                return await cls.query.where((cls.uid == uid) & (cls.name == name)).gino.first()
        except Exception as e:
            logger.info(f"任务获取出错 {type(e)}: {e}")

    @classmethod
    async def get_all_in_progress_mission(cls, uid: str) -> list["MissionDB"]:
        try:
            async with db.transaction():
                return await cls.query.where((cls.uid == uid) & (cls.status == '进行中')).gino.all()
        except Exception as e:
            logger.info(f"任务列表获取出错 {type(e)}: {e}")

    # 获取所有领取过的（包括完成和未完成）的任务的名字，只包括一次性任务，这是用来查重防止反复领取的
    @classmethod
    async def get_all_received_mission(cls, uid: int) -> list[str]:
        try:
            async with db.transaction():
                names = await cls.select('name').where((cls.uid == uid) & (cls.type2 == '一次')).gino.all()
                return map(lambda x: x[0], names)
        except Exception as e:
            logger.info(f"任务列表获取出错 {type(e)}: {e}")

    @classmethod
    async def get_mission_by_id(cls, id: int) -> "MissionDB":
        try:
            async with db.transaction():
                return await cls.query.where(cls.id == id).gino.first()
        except Exception as e:
            logger.info(f"任务列表获取出错 {type(e)}: {e}")
