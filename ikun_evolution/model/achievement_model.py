from .gino_db import db
from datetime import datetime
from services.log import logger


# 成就表
# 单独放一个表是因为这个表组查询操作（计算序号），不太方便丢在player的json里，干脆抽出来方便扩展
class AchievementDB(db.Model):
    __tablename__ = "ikun_achievement"

    id: int = db.Column(db.Integer(), primary_key=True)
    # 角色ID（同时包含了赛季信息）
    uid = db.Column(db.String(), nullable=False)
    # 创建时间
    start_time = db.Column(db.DateTime(), default=datetime.now)
    # 成就名字
    name: str = db.Column(db.String(), nullable=False)
    # 第几个获得这个成就的序号
    order: int = db.Column(db.Integer(), nullable=False)
    # 赛季
    session: str = db.Column(db.String(), default="S1")
    # 完成时总共探索的次数
    times: int = db.Column(db.Integer(), nullable=False, default="999999")

    @classmethod
    async def record_archive(cls, uid: str, name: str, times: int) -> "AchievementDB":
        # 这里要计算一下是第几个获得的，其实业务逻辑不应该写在这但是我懒了，一个事务完成
        try:
            async with db.transaction():
                # # 查询总共有多少个同名成就
                num = await db.select([db.func.count(AchievementDB.id)]) \
                    .where((cls.session == "S1") & (cls.name == name)).gino.scalar()
                return await cls.create(uid=uid, name=name, order=1 + num, times=times)
        except Exception as e:
            logger.info(f"新建成就出错 {type(e)}: {e}")

    @classmethod
    async def query_all_by_id(cls, qid: int) -> list["AchievementDB"]:
        try:
            async with db.transaction():
                return await cls.query.where(cls.uid == qid).gino.all()
        except Exception as e:
            logger.error(f"查询成就出错 {type(e)}: {e}")

    @classmethod
    async def query_by_id_name(cls, qid, name) -> "AchievementDB":
        try:
            async with db.transaction():
                return await cls.query.where((cls.uid == qid) & (cls.name == name)).gino.first()
        except Exception as e:
            logger.error(f"查询成就出错 {type(e)}: {e}")
