from ..model.achievement_model import AchievementDB
from ..utils import get_uid


async def add_achievement(event, name: str, times):
    # 已经拿过的成就不能再拿
    if await AchievementDB.query_by_id_name(get_uid(event), name) is not None:
        return None
    return await AchievementDB.record_archive(get_uid(event), name, times)


