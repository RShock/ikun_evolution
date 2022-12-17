from typing import Callable, Any

from lagom import Container

from .logger import Logger
from .msgPack import MsgPack
from .tools.tools import get_container
from .enums import Trigger, BuffPriority


class Buff:

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self._name = "未定义"  # buff的名字
        self.anti = []  # 这个buff施加后，这里面的buff将无法施加，存储内容为buff的名字
        self.trigger: Trigger = None  # buff施加的时机
        self._time = 9999  # buff持续的时间，9999为无限
        self._owner = None  # 拥有者
        self._tag = []  # 这个Buff拥有的标签
        self._del_msg = None  # 删除标签时的提示
        self._checker: list[Callable[[MsgPack], bool]] = []  # 这里传入一个函数，函数为真值则继续执行
        self._priority = BuffPriority.NORMAL  # buff优先级，基本都是1
        self.disable = False  # True时无法触发

        def default_handler(pack):
            self.logger.log(f"触发了{self._name}的默认行为")

        self._handler: Callable[[MsgPack], None] = default_handler

    def __str__(self) -> str:
        return f"【{self._owner}_{self._name}_{self.trigger}】"

    # def default_checker(self, pack):
    #     return True

    def name(self, name: str) -> "Buff":
        self._name = name
        return self

    def priority(self, priority) -> "Buff":
        self._priority = priority
        return self

    def get_priority(self):
        return self._priority

    def checker(self, checker: Callable[[Any], bool]) -> "Buff":
        self._checker.append(checker)
        return self

    def handler(self, handler: Callable[[MsgPack], None]) -> "Buff":
        self._handler = handler
        return self

    def check(self, pack: MsgPack) -> bool:
        if self.disable:
            return False
        pack.buff_name(self._name)
        pack.buff_owner(self._owner)
        for c in self._checker:
            if not c(pack):
                return False
        return True

    def handle(self, pack) -> None:
        pack.buff_name(self._name)
        return self._handler(pack)

    def time(self, time: int) -> "Buff":
        self._time = time
        return self

    def get_time(self):
        return self._time

    def time_pass(self):
        self._time -= 1

    def mark_as_delete(self) -> "Buff":
        self._time = -1
        return self

    def mark_as_disable(self):
        self.disable = True

    def owner(self, owner) -> "Buff":
        self._owner = owner
        return self

    def tag(self, tag) -> "Buff":
        self._tag.append(tag)
        return self

    def check_tag(self, tag):
        return tag in self._tag

    def check_owner(self, owner):
        return self._owner == owner

    def get_del_msg(self):
        return self._del_msg


def new_buff(owner: "Pokemon", trigger: Trigger) -> "Buff":
    tmp = get_container()[Buff]
    tmp.trigger = trigger
    tmp._owner = owner
    return tmp
