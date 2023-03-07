from .gino_db import db
from datetime import datetime
from services.log import logger


# 其他杂项(热度图，签到等）
# 随便填了一些内容，方便更新
class OhterDB(db.Model):
    __tablename__ = "ikun_other"

    id: int = db.Column(db.Integer(), primary_key=True)
    # 配置名称
    name = db.Column(db.String(), nullable=False)
    # 配置类型
    type = db.Column(db.String(), nullable=False)
    # uid
    uid = db.Column(db.String(), nullable=True)
    # 时间
    start_time = db.Column(db.DateTime(), default=datetime.now, nullable=True)
    # 计数
    count = db.Column(db.Integer(), default=0, nullable=True)
    # 信息
    info: str = db.Column(db.JSON(), default={}, nullable=True)

    # @classmethod
    # async def add_new(cls, uid: str, name: str, times: int) -> "OhterDB":
    #     # 这里要计算一下是第几个获得的，其实业务逻辑不应该写在这但是我懒了，一个事务完成
    #     try:
    #         async with db.transaction():
    #             return await cls.create(uid=uid, group=name, order=1 + num, times=times)
    #     except Exception as e:
    #         logger.info(f"新建成就出错 {type(e)}: {e}")
