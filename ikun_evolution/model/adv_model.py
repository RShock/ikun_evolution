from ..utils import get_act_str
from services.db_context import db
from datetime import datetime
from services.log import logger


class ActionDB(db.Model):
    __tablename__ = "ikun_adventure"

    id: int = db.Column(db.Integer(), primary_key=True)
    # 角色ID
    uid = db.Column(db.String(), nullable=False)
    # 在干什么
    action = db.Column(db.String(), nullable=False)
    # 在哪里
    position = db.Column(db.String(), nullable=False)
    # 什么时候去的
    start_time = db.Column(db.DateTime(), default=datetime.now)
    # 懒更新时间
    update_time = db.Column(db.DateTime(), default=datetime.now)
    # 已经获得的物品
    item_get = db.Column(db.JSON(), nullable=False, default={})
    # 已经获得的技能经验
    skill_get = db.Column(db.JSON(), nullable=False, default={})
    # 日志
    log = db.Column(db.String(), nullable=False, default="")
    # 角色被附加的额外属性(记录角色受到的buff 角色的攻击一类 太多了不想写列了)
    other = db.Column(db.JSON(), nullable=False, default={})
    # 缺省字段
    reverse1 = db.Column(db.JSON(), nullable=True, default={})
    reverse2 = db.Column(db.JSON(), nullable=True, default={})
    reverse3 = db.Column(db.JSON(), nullable=True, default={})

    @classmethod
    async def go_outside(cls, uid: str, pos: str, other:dict, log) -> "ActionDB":
        try:
            async with db.transaction():
                logger.info(f"{uid}出发了")
                return await cls.create(uid=uid, position=pos, action=get_act_str(pos), log=log,
                                        other=other)
        except Exception as e:
            logger.info(f"角色出发出错 {type(e)}: {e}")

    @classmethod
    async def get_action_by_uid(cls, uid: str) -> "ActionDB":
        try:
            async with db.transaction():
                return await cls.query.where(cls.uid == uid).gino.first()
        except Exception as e:
            logger.info(f"角色查询出错 {type(e)}: {e}")
