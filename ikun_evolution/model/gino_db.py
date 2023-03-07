# 针对真寻最新版的应急补丁
# 本人在开发新游戏暂时无法深度维护，按需使用。

from gino import Gino

# 全局数据库连接对象
from nonebot import logger, get_driver
from configs.config import address, bind, database, password, port, sql_name, user

db = Gino()


async def init():
    if not bind and (not user and not password and not address and not port and not database):
        raise ValueError("数据库配置未填写")
    i_bind = bind
    if not i_bind:
        i_bind = f"{sql_name}://{user}:{password}@{address}:{port}/{database}"

    try:
        await db.set_bind(i_bind)
        await db.gino.create_all()
        logger.info(f'Database loaded successfully!')
    except Exception as e:
        raise Exception(f'数据库连接错误.... {type(e)}: {e}')


async def disconnect():
    await db.pop_bind().close()