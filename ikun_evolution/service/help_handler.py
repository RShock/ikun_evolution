from .. import send_group_msg2, get_image, send_group_msg
from .game_handler import get_world_data


async def handle_help(num, ikun_help, bot, event):
    if not num.isdigit():
        await ikun_help.finish("输入的格式不对，请输入数字")
    num = int(num)
    help = get_world_data().get_help_answer(num)
    if not help:
        await ikun_help.finish("未找到对应帮助")
    if help.type == "图片型":
        await ikun_help.finish(get_image("notice", help.ans))
        return
    if help.type == "消息型":
        await send_group_msg(bot, event,help.name, help.ans)


def get_msg():
    help = "\n".join(get_world_data().get_help_question())

    return [("超级吞噬系统", "请用数字选择具体帮助："),
            ("超级吞噬系统", help)]

