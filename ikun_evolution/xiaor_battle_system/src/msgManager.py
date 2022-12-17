from .logger import Logger
from .tools.stream import Stream
from .buff import Buff, new_buff
from .msgPack import MsgPack
from .enums import Trigger, BuffPriority


class MsgManager:

    def __init__(self, logger: Logger):
        self.logger = logger
        self.buffs: dict[Trigger, list["Buff"]] = {}
        self.force_end = False  # 强制结束游戏
        # self.hooks = []  # 扭曲类效果存放

        self.add_death_watcher()

    def register(self, buff: Buff):
        # self.logger.log(f"新增了buff:{buff}")
        if buff.trigger not in self.buffs:
            self.buffs[buff.trigger] = []
        self.buffs[buff.trigger].append(buff)
        self.buffs[buff.trigger] = sorted(self.buffs[buff.trigger], key=lambda b: b.get_priority())

    def send_msg(self, pack: MsgPack):

        def handle(buff, p):
            if self.force_end:
                return
            if pack.check_trigger(Trigger.ACTIVE):
                if not pack.get_allow():
                    return  # 一个事件一旦被禁止，便无法再被禁止。如果攻击换成了毒，就无法再被换成其他的
            # 打断机制：一个已经附加的buff可能会因为其他buff无法执行（例如毒液攻击会取代普通攻击，这使得普通攻击无法执行）
            # 也就是简化的扭曲机制，把普攻扭曲成了毒液攻击，但是没法做到非常细节的扭曲。
            # 目前只有攻击会被打断，如果每个buff都需要判断是否打断，游戏速度会变慢很多
            if pack.check_trigger(Trigger.ACTIVE) or (not pack.check_trigger(Trigger.ATTACK) and
                                                      not pack.check_trigger(Trigger.DEAL_DAMAGE) and
                                                      not pack.check_trigger(Trigger.TURN_START)):  # 目前只有这3种事件需要active
                DEBUG = None
                if DEBUG:
                    if pack.check_trigger(DEBUG):
                        self.logger.debug_log(f"before{p.get_max_hp()}")
                        print(trigger)

                buff.handle(p)
                if DEBUG:
                    if pack.check_trigger(DEBUG):
                        self.logger.debug_log(f"after{p.get_max_hp()}")

            else:
                _pack: MsgPack = MsgPack.active_pack().pack(p)
                self.send_msg(_pack)
                if _pack.get_allow():
                    buff.handle(p)
                # else:
                #     self.logger.log(f"{buff}被阻止了")

        # if pack.check_trigger(Trigger.TAKEN_DAMAGE):
        #     self.logger.log(f"{pack.get_our()}atk")

        trigger = pack.data["trigger_type"]
        if trigger not in self.buffs:
            return
        for buff in self.buffs[trigger]:
            # self.logger.log(f"{buff} {pack.data['trigger_type']}")
            if not pack.check_trigger(buff.trigger):
                continue
            if not buff.check(pack):
                continue
            handle(buff, pack)

    # 回合结束时需要删除一些过期的buff
    def turn_end(self):
        for k, buff_list in self.buffs.items():
            tmp = []
            for buff in buff_list:
                if buff.get_time() == 9999:
                    tmp.append(buff)
                    continue
                buff.time_pass()
                if buff.get_time() > 0:
                    tmp.append(buff)
                elif buff.get_del_msg():
                    self.logger.log(buff.get_del_msg())
            self.buffs[k] = tmp

    def clean(self):
        self.buffs = {}
        self.add_death_watcher()
        self.hooks = []

    def get_buff_stream(self) -> Stream["Buff"]:
        return Stream(self.buffs).flat_map(lambda k: Stream(self.buffs[k]))

    def add_death_watcher(self):
        # 添加死亡监控
        # 在每次受伤后都进行死亡检测
        def check_death(pack: MsgPack):
            if pack.get_our().hp <= 0:
                self.force_end = True

        self.force_end = False
        self.register(new_buff(self, Trigger.TAKEN_DAMAGE).name("死亡检测").handler(check_death)
                      .priority(BuffPriority.ABS_FINAL))

    # def add_hook(self, checker, ):
    #     self.hooks.append(checker)
