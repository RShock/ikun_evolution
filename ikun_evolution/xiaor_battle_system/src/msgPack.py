from .enums import Trigger, DamageType


# 一坨getter和setter 用来保证不会写错变量名
# 虽然写的很挫但是py没有lombok只能这样了
class MsgPack:
    def __init__(self) -> None:
        self.data = {}  # 数据

    # 触发类型
    def trigger_type(self, trigger_type) -> "MsgPack":
        if self.data.get("trigger_type") is not None:
            raise "警告，请勿循环使用同一个pack"
        self.data["trigger_type"] = trigger_type
        return self

    def check_trigger(self, trigger) -> bool:
        return self.data["trigger_type"] == trigger

    # 攻击
    def atk(self, atk) -> "MsgPack":
        self.data["atk"] = atk
        return self

    def get_atk(self) -> int:
        return self.data["atk"]

    def change_atk(self, apply) -> None:
        self.data["atk"] = apply(self.get_atk())

    # 防御
    def defe(self, defe) -> "MsgPack":
        self.data["def"] = defe
        return self

    def get_def(self) -> int:
        return self.data["def"]

    def change_def(self, apply) -> None:
        self.data["def"] = apply(self.get_def())

    # 速度
    def spd(self, spd) -> "MsgPack":
        self.data["spd"] = spd
        return self

    def get_spd(self) -> int:
        return self.data["spd"]

    def change_spd(self, apply) -> None:
        self.data["spd"] = apply(self.get_spd())

    # 生命
    def hp(self, hp) -> "MsgPack":
        self.data["hp"] = hp
        return self

    def get_max_hp(self) -> int:
        return self.data["hp"]

    def change_max_hp(self, apply) -> None:
        self.data["hp"] = apply(self.get_max_hp())

    # 等级
    def lv(self, lv) -> "MsgPack":
        self.data["lv"] = lv
        return self

    def change_lv(self, apply) -> None:
        self.data["lv"] = apply(self.get_lv())

    def get_lv(self) -> int:
        return self.data["lv"]

    # 生命回复速度
    def life_inc_spd(self, spd) -> "MsgPack":
        self.data["life_inc_spd"] = spd
        return self

    def change_life_inc_spd(self, apply) -> None:
        self.data["life_inc_spd"] = apply(self.get_life_inc_spd())

    def get_life_inc_spd(self):
        return self.data["life_inc_spd"]

    # 暴击率
    def crit(self, crit) -> "MsgPack":
        self.data["crit"] = crit
        return self

    def get_crit(self) -> int:
        return self.data["crit"]

    def change_crit(self, apply) -> None:
        self.data["crit"] = apply(self.get_crit())

    # 暴击伤害
    def csd(self, crit) -> "MsgPack":
        self.data["csd"] = crit
        return self

    def get_csd(self) -> int:
        return self.data["csd"]

    def change_csd(self, apply) -> None:
        self.data["csd"] = apply(self.get_csd())

    # 受到的伤害（来自be_attack）
    def damage(self, num) -> "MsgPack":
        self.data["damage"] = int(num)
        return self

    def get_damage(self) -> int:
        return round(self.data["damage"])

    def change_damage(self, apply) -> None:
        self.data["damage"] = apply(self.get_damage())

    # 我方
    def our(self, our: "Pokemon") -> "MsgPack":
        self.data["our"] = our
        self.data["name"] = our.name if our is not None else "无来源"
        return self

    def get_our(self) -> "Pokemon":
        return self.data["our"]

    def get_name(self) -> str:
        return self.data["name"]

    def is_our_owner(self) -> bool:
        return self.data["our"] == self.data["buff_owner"]

    # 敌方
    def enemy(self, enemy) -> "MsgPack":
        self.data["enemy"] = enemy
        return self

    def get_enemy(self):
        return self.data["enemy"]

    # def is_enemy_owner(self) -> bool:
    #     return self.data["enemy"] == self.data["buff_owner"]

    # buff名字（debug用）
    def buff_name(self, buff_name: str):
        self.data["buff_name"] = buff_name
        return self

    def get_buff_name(self):
        return self.data["buff_name"]

    def check_buff_name(self, buff_name: str):
        return buff_name in self.data["buff_name"]

    # 是否禁用后续事件
    def not_allow(self):
        self.data["allow"] = False

    def get_allow(self) -> bool:
        return self.data.get("allow", True)

    # 连锁结算数据包
    def pack(self, pack) -> "MsgPack":
        self.data["pack"] = pack
        return self

    def get_pack(self) -> "MsgPack":
        return self.data["pack"]

    # buff拥有者(后续可能会取代我方)
    def buff_owner(self, buff_owner):
        self.data["buff_owner"] = buff_owner
        return self

    def get_owner(self) -> "Pokemon":
        return self.data["buff_owner"]

    def check_owner(self, owner):
        return owner.id == self.data["buff_owner"].id

    # 开启穿透伤害（来自attack）
    def perfw(self) -> "MsgPack":
        self.data["perfw"] = True
        return self

    def is_perfw(self):
        return self.data.get("perfw", False)

    # 最终伤害系数（来自attack）
    def percent(self, num) -> "MsgPack":
        self.data["percent"] = num
        return self

    def get_percent(self) -> float:
        return self.data.get("percent", 100)

    # 伤害类型
    def damage_type(self, damage_type):
        self.data["damage_type"] = damage_type
        return self

    def check_damage_type(self, type):
        return self.data["damage_type"] == type

    # 受到伤害时，造成伤害的触发器。如果是攻击触发，容易造成反击。毒触发则不会。
    def damage_taken_trigger(self, tri: Trigger):
        self.data["damage_taken_trigger"] = tri
        return self

    def check_damage_taken_trigger(self, tri: Trigger):
        return self.data["damage_taken_trigger"] == tri

    # 回合开始计数
    def turn_count(self, num:int) -> "MsgPack":
        self.data["turn_count"] = num
        return self

    def get_turn_count(self) -> int:
        return self.data["turn_count"]

    def __str__(self) -> str:
        return f"{self.data}"

    @staticmethod
    def builder() -> "MsgPack":
        return MsgPack()

    @staticmethod
    def get_atk_pack():
        return MsgPack.builder().trigger_type(Trigger.GET_ATK)

    @staticmethod
    def get_def_pack():
        return MsgPack.builder().trigger_type(Trigger.GET_DEF)

    @staticmethod
    def get_lv_pack():
        return MsgPack.builder().trigger_type(Trigger.GET_LV)

    @staticmethod
    def get_max_hp_pack():
        return MsgPack.builder().trigger_type(Trigger.GET_HP)

    @staticmethod
    def get_spd_pack():
        return MsgPack.builder().trigger_type(Trigger.GET_SPD)

    @staticmethod
    def get_life_inc_spd_pack():
        return MsgPack.builder().trigger_type(Trigger.GET_LIFE_INC_SPD)

    @staticmethod
    def get_crit_pack():
        return MsgPack.builder().trigger_type(Trigger.GET_CRIT)

    @staticmethod
    def get_csd_pack():
        return MsgPack.builder().trigger_type(Trigger.GET_CSD)

    @staticmethod
    def active_pack():
        return MsgPack.builder().trigger_type(Trigger.ACTIVE)

    @staticmethod
    def atk_pack():
        return MsgPack.builder().trigger_type(Trigger.ATTACK)

    @staticmethod
    def turn_end_pack():
        return MsgPack.builder().trigger_type(Trigger.TURN_END)

    @staticmethod
    def turn_start_pack(num):
        return MsgPack.builder().trigger_type(Trigger.TURN_START).turn_count(num)


    # @staticmethod
    # def be_atk_pack():
    #     return MsgPack.builder().trigger_type(Trigger.BE_ATTACK)

    @staticmethod
    def damage_pack(our, enemy, num, type: DamageType = DamageType.NORMAL):
        return MsgPack.builder().trigger_type(Trigger.DEAL_DAMAGE).damage_type(type).damage(num).our(our).enemy(enemy)

    @staticmethod
    def taken_damage_pack(our, enemy, num, taken_trigger: Trigger, type: DamageType = DamageType.NORMAL):
        return MsgPack.builder().trigger_type(Trigger.TAKEN_DAMAGE).damage_type(type).damage(num).our(our).enemy(enemy) \
            .damage_taken_trigger(taken_trigger)
