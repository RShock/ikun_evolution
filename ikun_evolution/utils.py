import io
import os

from nonebot.adapters.onebot.v11 import MessageSegment, Bot, GroupMessageEvent

from utils.message_builder import image


def add_items(a, b) -> dict[str, int]:
    temp = dict()
    for key in a.keys() | b.keys():
        temp[key] = round(sum([d.get(key, 0) for d in (a, b)]), 2)
    return temp


def add_item(dic, name, cnt=1):
    if dic.get(name) is None:
        dic[name] = round(cnt)
    else:
        dic[name] = round(dic[name] + cnt, 2)


game_path = os.path.dirname(__file__)


# 不知道官方的那个image怎么用 只能直接用自己文件下的的resources+MessageSegment了 会用的可以告诉我
def get_image(type, name):
    image_file = f"file:///{game_path}/gamedata/image/{type}/{name}"
    return MessageSegment.image(image_file)


SESSION_CODE = "S1"  # 不同赛季的账号是完全不同的


def get_uid(event) -> str:
    return str(event.user_id) + SESSION_CODE


def get_act_str(name) -> str:
    return '正在' + name


async def send_group_msg(
        bot: Bot,
        event: GroupMessageEvent,
        name: str,
        msgs: list[str],
):
    """
    发送合并消息(发送人名称相同)
    @param bot: 机器人的引用
    @param event: 用来获取群id
    @param name: 发消息的人的名字
    @param msgs: 要发的消息(list[str])
    @return:
    """
    messages = [MessageSegment.node_custom(bot.self_id, name, m) for m in msgs]
    await bot.call_api(
        "send_group_forward_msg", group_id=event.group_id, messages=messages
    )


async def send_group_msg_pic(
        bot: Bot,
        name: str,
        msgs: list[str],
):
    """
    发送合并消息(发送人名称相同)的图片，风控时使用
    @param bot: 机器人的引用
    @param event: 用来获取群id
    @param name: 发消息的人的名字
    @param msgs: 要发的消息(list[str])
    @return:
    """
    msg = "\n\n".join(msgs)
    result = f"{name}:\n{msg}"
    await send_img(bot, result)


async def send_group_msg_pic2(
        bot: Bot,
        msgs: list[tuple],
):
    """
    发送合并消息(发送人名称不同)的图片，风控时使用
    @param bot: 机器人的引用
    @param event: 用来获取群id
    @param msgs: 要发的消息([list[(str,str)]）e.g.[("真寻","我爱你"),...]
    @return:
    """
    tmp = io.StringIO()
    tmp2 = ""
    for name, msg in msgs:
        if name != tmp2:
            tmp2 = name
            tmp.write(name)
            tmp.write(':\n')
        tmp.write(msg)
        tmp.write('\n')
    await send_img(bot, tmp.getvalue())


# text2image可能是真寻独有的方法 但是显示不了emoji 只能临时备用罢了
async def send_img(bot, msg: str):
    new_txt = ""
    l = msg.split("\n")
    for txt in l:
        while txt:
            new_txt = "{0}{1}\n".format(new_txt, txt[:20])
            txt = txt[30:]

    from utils.image_utils import text2image
    await bot.send(image(b64=(await text2image(new_txt, padding=10)).pic2bs4()))


async def send_group_msg2(
        bot: Bot,
        event: GroupMessageEvent,
        msgs: list[tuple],
):
    """
    发送合并消息(发送人名称不同)
    @param bot: 机器人的引用
    @param event: 用来获取群id
    @param msgs: 要发的消息([list[(str,str)]）e.g.[("真寻","我爱你"),...]
    @return:
    """
    messages = [MessageSegment.node_custom(bot.self_id, m[0], m[1]) for m in msgs]
    await bot.call_api(
        "send_group_forward_msg", group_id=event.group_id, messages=messages
    )


def fill_list(my_list: list, length, fill=None):  # 使用 fill字符/数字 填充，使得最后的长度为 length
    if len(my_list) >= length:
        return my_list
    else:
        return my_list + (length - len(my_list)) * [fill]
