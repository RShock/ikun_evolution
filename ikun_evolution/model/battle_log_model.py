from services.db_context import db
from datetime import datetime
from services.log import logger


# 记录战斗日志 这个表默认为脏数据 不能参与任何业务流程
class BattleLogDB(db.Model):
    __tablename__ = "ikun_battle_log"

    id: int = db.Column(db.Integer(), primary_key=True)
    # 角色ID
    uid = db.Column(db.String(), nullable=False)
    # 创建时间
    start_time = db.Column(db.DateTime(), default=datetime.now)
    # 我方名字
    our_name: str = db.Column(db.String(), nullable=False)
    # 敌人名字
    enemy_name: str = db.Column(db.String(), nullable=False)
    our_lv: int = db.Column(db.Integer(), nullable=True)
    enemy_lv: int = db.Column(db.Integer(), nullable=True)
    # 对于单个玩家的战斗次数
    battle_times: int = db.Column(db.Integer(), nullable=False, default=0)
    # 日志
    log = db.Column(db.JSON(), nullable=False, default={})

    @classmethod
    async def record_battle(cls, uid: str, our_name: str, enemy_name: str,
                            our_lv: int, enemy_lv: int,
                            log: dict[str, str], battle_times: int
                            ) -> "BattleLogDB":

        try:
            async with db.transaction():
                return await cls.create(uid=uid, log=log, our_name=our_name, enemy_name=enemy_name, our_lv=our_lv,
                                        enemy_lv=enemy_lv, battle_times=battle_times)
        except Exception as e:
            logger.error(f"存储战斗日志出错 {type(e)}: {e}")

    @classmethod
    async def query_by_id(cls, qid: int) -> "BattleLogDB":
        try:
            async with db.transaction():
                log = await cls.query.where(cls.id == qid).gino.first()
                if log is None:
                    logger.warning(f"查询战斗日志出错 查询id为{id}")
                return log
        except Exception as e:
            logger.error(f"查询战斗日志出错 {type(e)}: {e}")

    @classmethod
    async def query_log_count(cls, uid: str) -> int:
        try:
            async with db.transaction():
                num = await db.select([db.func.count(BattleLogDB.id)]) \
                    .where(cls.uid == uid).gino.scalar()
                return num
        except Exception as e:
            logger.error(f"查询战斗日志出错 {type(e)}: {e}")
