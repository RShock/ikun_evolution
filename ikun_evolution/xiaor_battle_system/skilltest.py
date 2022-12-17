import unittest

from src.gameBoard import GameBoard
from src.logger import Logger
from src.msgManager import MsgManager
from src.pokemon import Pokemon
from src.tools.tools import get_container


class TestCases(unittest.TestCase):
    container = None
    logger = None
    msgManager = None
    gameBoard = None

    @classmethod
    def setUpClass(cls) -> None:
        # print('每个用例前置')
        cls.container = get_container()
        # 单例声明
        cls.logger = cls.container[Logger] = Logger()
        cls.msgManager = cls.container[MsgManager] = MsgManager(cls.container[Logger])
        cls.gameBoard = cls.container[GameBoard] = GameBoard(cls.container[Logger], cls.container[MsgManager])

    def setUp(self) -> None:
        self.gameBoard = self.container[GameBoard]
        self.gameBoard.TURN_LIMIT =7
        self.pkm1 = self.container[Pokemon]
        self.pkm2 = self.container[Pokemon]

        data_init(self.pkm1)
        self.pkm1.name = "小白菜"
        data_init(self.pkm2)
        self.pkm2.name = "小黄瓜"

        self.gameBoard.add_ally(self.pkm1)
        self.gameBoard.add_enemy(self.pkm2)

    def tearDown(self) -> None:
        # print('每个用例的后置')
        self.gameBoard.print_log()
        self.msgManager.clean()
        self.logger.clean()

        if self.result == '我方胜利':
            print(f"{self.pkm1.name}胜利")
        else:
            print(f"{self.pkm1.name}战败！")

    def test发烟测试(self):
        self.pkm1.MAX_HP = 30
        self.pkm2.MAX_HP = 30
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 10)
        self.assertEqual(self.pkm2.hp, 0)

    def test连击(self):
        self.pkm1.skillGroup = ["连击"]

        # pkm2.skillGroup = ["反击50"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 1000)

    def test反击对连击正常反应(self):
        self.pkm1.skillGroup = ["连击"]
        self.pkm2.skillGroup = ["反击50"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 790)
        self.assertEqual(self.pkm2.hp, 1000)

    def test03(self):
        self.pkm2.MAX_HP = 100
        self.pkm2.skillGroup = ["愈合1"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 37)

    def test测试2个回血技能(self):
        self.pkm2.MAX_HP = 100
        self.pkm2.skillGroup = ["愈合1", "长生100"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 44)

    def test毒vs愈合(self):
        self.pkm2.MAX_HP = 100
        self.pkm2.skillGroup = ["愈合1", "长生100"]
        self.pkm1.skillGroup = ["毒液50"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, -2)

    def test毒攻击(self):
        self.pkm1.skillGroup = ["毒液50"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 870)

    def test毒攻击无法被反击(self):
        self.pkm1.skillGroup = ["毒液50", "连击", "尖角10"]
        self.pkm2.skillGroup = ["反击"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 870)

    def test连击会导致攻击力归零(self):
        self.pkm1.skillGroup = ["毒液50", "连击"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 1000)

    def test剧毒之体(self):
        self.pkm1.skillGroup = ["毒液50", "剧毒之体"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 844)

    def test剧毒之体无法造成普通伤害(self):
        self.pkm1.skillGroup = ["剧毒之体"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 1000)

    def test剧毒之体回合结束会强制解毒(self):
        self.pkm1.skillGroup = ["毒液50"]
        self.pkm2.skillGroup = ["剧毒之体"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 1000)
        self.assertEqual(self.pkm2.hp, 930)

    def test猛毒(self):
        self.pkm1.skillGroup = ["毒液50", "猛毒200"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 610)

    def test惜别(self):
        self.pkm1.skillGroup = ["惜别"]
        self.pkm1.MAX_HP = 10
        self.pkm2.skillGroup = ["惜别"]
        self.pkm2.MAX_HP = 10
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 1)
        self.assertEqual(self.pkm2.hp, -9)

    def test暴怒(self):
        self.pkm1.skillGroup = ["惜别", "暴怒1000"]
        self.pkm1.hp = 1000
        self.pkm2.skillGroup = ["惜别", "暴怒1000"]
        self.pkm2.hp = 1000
        self.gameBoard.init()
        self.pkm1.hp = 1
        self.pkm2.hp = 1
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 1)
        self.assertEqual(self.pkm2.hp, -1008)

    def test粘液(self):
        self.pkm1.skillGroup = ["粘液100"]
        self.pkm2.skillGroup = ["利爪100"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 1000)
        self.assertEqual(self.pkm2.hp, 930)

    def test抗毒(self):
        self.pkm1.skillGroup = ["毒液100"]
        self.pkm2.skillGroup = ["抗毒80"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 948)

    def test野性(self):
        self.pkm1.skillGroup = ["尖角10", "野性100"]
        self.pkm2.skillGroup = []
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 720)

    def test尖牙(self):
        self.pkm1.skillGroup = ["尖牙100"]
        self.pkm2.skillGroup = []
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 860)

    def test反击对反击不能触发无限反击(self):
        self.pkm1.skillGroup = ["反击100"]
        self.pkm2.skillGroup =["反击100"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 790)
        self.assertEqual(self.pkm2.hp, 790)

    def test两个人都有毒先手的人获胜(self):
        self.pkm1.skillGroup = ["毒液10000"]
        self.pkm2.skillGroup = ["毒液10000"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 1000)
        self.assertEqual(self.pkm2.hp, -1000)

    def test游泳测试1(self):
        self.pkm1.skillGroup = ["溺水"]
        self.pkm2.skillGroup = ["溺水"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 104)
        self.assertEqual(self.pkm2.hp, 104)

    def test免疫溺水(self):
        self.pkm1.skillGroup = ["溺水","游泳5"]
        self.pkm2.skillGroup = ["溺水"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 854)
        self.assertEqual(self.pkm2.hp, 91)

    def test平地游泳(self):
        self.pkm1.skillGroup = ["游泳5"]
        self.pkm2.skillGroup = []
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp, 930)

    def test水栖免疫溺水(self):
        self.pkm1.skillGroup = ["溺水","水栖"]
        self.pkm2.skillGroup = ["溺水"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 944)
        self.assertEqual(self.pkm2.hp, 90)

    def test灵巧能闪避毒(self):
        self.pkm1.skillGroup = ["灵巧100"]
        self.pkm2.skillGroup = ["毒液50"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 1000)
        self.assertEqual(self.pkm2.hp, 930)

    def test粘液降低攻击的优先级(self):
        self.pkm1.skillGroup = ["粘液50"]
        self.pkm2.skillGroup = ["尖角100"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 650)
        self.assertEqual(self.pkm2.hp, 930)

    def test毒刃被剧毒之体加成(self):
        self.pkm1.skillGroup = ["尖角90","毒刃40","剧毒之体"]
        self.pkm2.skillGroup = ["尖角100"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 450)
        self.assertEqual(self.pkm2.hp, -8)

    def test剧毒之体无效伤害(self):
        self.pkm1.skillGroup = ["尖角90","剧毒之体"]
        self.pkm2.skillGroup = ["尖角100"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 230)
        self.assertEqual(self.pkm2.hp, 1000)

    def test威压测试(self):
        self.pkm1.skillGroup = ["蛊神1","威压1"]
        self.pkm2.skillGroup = []
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 951)
        self.assertEqual(self.pkm2.hp,730)

    def test伤噬测试(self):
        self.pkm1.skillGroup = ["蛊神1","伤噬35","毒液100"]
        self.pkm2.skillGroup = []
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 930)
        self.assertEqual(self.pkm2.hp,558)


    def test镜子(self):
        self.pkm1.skillGroup = ["蛊神1","伤噬35","毒液100"]
        self.pkm2.skillGroup = ["镜中自我"]
        self.gameBoard.init()
        self.result = self.gameBoard.battle()
        self.assertEqual(self.pkm1.hp, 545)
        self.assertEqual(self.pkm2.hp,559)

if __name__ == '__main__':
    unittest.main()


def data_init(pkm: Pokemon):
    pkm.ATK = 20
    pkm.DEF = 10
    pkm.MAX_HP = 1000
    pkm.skillGroup = []
