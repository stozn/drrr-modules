import os
import csv
import random
import itertools
from collections import Counter
from modules.module import Module

dir = os.path.dirname(__file__)


def ckn(username):
    return username.replace('@', '').strip()


def pop(my_list):
    return my_list.pop(random.randrange(len(my_list)))


def readcsv(filename):
    data = []
    with open(os.path.join(dir, filename), 'r', encoding='utf-8-sig') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            data.append(dict(row))
    return data


def choice(probs):
    prob = 0
    rand = random.random()
    for i, p in enumerate(probs):
        prob += p
        if rand < prob:
            return i
    return len(probs) - 1


class PokemonCard:
    def __init__(self, id, uid, name, attribute, attribute2, health, attack, speed, skill):
        self.id = id
        self.uid = uid
        self.up = self.uid != '-'
        self.name = name
        self.attribute = attribute
        self.attribute2 = attribute2
        self.health = health
        self.hp = health
        self.attack = attack
        self.atk = attack
        self.speed = speed
        self.spd = speed
        self.skill = skill
        self.status = ''

    @property
    def score(self):
        return self.health + self.attack + self.speed

    @property
    def grade(self):
        grade = [('C', 13), ('B', 19), ('A', 24)]
        for g, s in grade:
            if self.score <= s:
                return g
        return 'S'

    def __str__(self):
        return f'{"⬆" if self.up else ""}【{self.attribute + self.attribute2}】[{self.grade}]{self.name} {self.score} ({self.health}/{self.attack}/{self.speed})'

    def reset(self):
        self.hp = self.health
        self.atk = self.attack
        self.spd = self.speed
        self.status = ''


class Player:
    def __init__(self, name):
        self.name = name
        self.team = []

    def __str__(self):
        return self.name

    def reset(self):
        for p in self.team:
            p.reset()


class Battle:
    def __init__(self, player1: Player, player2: Player, attribute, skill):
        self.p1 = player1
        self.p2 = player2
        self.round = 0
        self.battlelog = []
        self.log = []
        self.attribute = attribute
        self.skill = skill
        self.p1.reset()
        self.p2.reset() 

    def start(self):
        i1 = 0
        i2 = 0
        while True:
            self.round += 1
            x = self.p1.team[i1]
            y = self.p2.team[i2]
            self.log = [
                f'　-{self.round}-\n【{x.attribute + x.attribute2}】{x.name}　　VS　　【{y.attribute+y.attribute2}】{y.name}'.center(22, '　')]
            win = self.pk(x, y)
            self.battlelog.append(self.log)
            if win:
                i2 += 1
            else:
                i1 += 1
            if i1 == len(self.p1.team):
                return False, self.battlelog
            if i2 == len(self.p2.team):
                return True, self.battlelog

    def pk(self, x: PokemonCard, y: PokemonCard):
        p1 = x
        p2 = y
        reverse = False
        if x.spd < y.spd:
            p1, p2 = p2, p1
            reverse = True

        while True:
            self.hit(p1, p2, reverse)
            if p2.hp <= 0:
                return not reverse

            self.hit(p2, p1, not reverse)
            if p1.hp <= 0:
                return reverse

    def ratio(self, att1, att2):
        return self.attribute.get((att1.attribute, att2.attribute), 1.0) * self.attribute.get((att1.attribute2, att2.attribute2), 1.0)

    
    def hit(self, p1: PokemonCard, p2: PokemonCard, reverse=False):
        prob = [0.55, 0.15, 0.15, 0.15]
        effect = ['○', '◎', '※', 'x']

        result = random.choices(effect, weights=prob, k=p1.atk)
        res = ''.join(result)
        counts = Counter(result)

        atk = 0
        ratio = 1
        for e, c in counts.items():
            if e == effect[0] and c:
                atk += c
            if e == effect[1] and c:
                atk += c * 2
            if e == effect[2] and c:
                skill = self.skill[p1.skill]
                if c >= int(skill['骰子个数']):
                    atk += int(skill['进阶威力']) * (c//int(skill['骰子个数']))
                else:
                    atk += int(skill['基础威力'])
                ratio = self.ratio(p1, p2)
                atk = int(atk * ratio + 0.6)

                if skill['概率'] and random.random() < float(skill['概率']):
                    res = res.replace('※', '🔯') 
                    status = skill['状态']
                    if status:
                        if status == '加速':
                            p1.status = status
                        else:
                            p2.status = status
                    def get(key):
                        if skill[key]:
                            return int(skill[key])
                        return 0

                    p1.hp += get('自血量')
                    p1.atk += get('自攻击')
                    p1.spd += get('自速度')
                    p2.atk -= get('敌攻击')
                    p2.spd -= get('敌速度')

        atk = int(atk)
        p2.hp -= atk

        right = '⇨⇢⭢⇒⇛'
        left = '⇦⇠⭠⇐⇚'
        e = {'': '', '减速': '⏪', '加速': '⏩', '毒素': '☠️', '烧伤': '🔥', '麻痹': '⚡️', '冻结': '🧊', '混乱': '🌀'}
        intervals = [0, 0.5, 1, 2, 4]
        idx = intervals.index(min(intervals, key=lambda x: abs(x - ratio)))

        if reverse:
            self.log.append(
                f'{p2.hp}{e[p2.status]}{f"{left[idx]}{atk} [{res}]".center(14, "　")}{e[p1.status]}{p1.hp}'.center(22, '　'))
        else:
            self.log.append(
                f'{p1.hp}{e[p1.status]}{f"[{res}] {atk}{right[idx]}".center(14, "　")}{e[p2.status]}{p2.hp}'.center(22, '　'))


class Game:
    def __init__(self, bot):
        self.bot = bot
        self.bot = bot
        self.dm = bot.dm
        self.send = bot.send

        self.stage = 0
        self.update()

        self.me('发送/go开始游戏！')
        

    def me(self, msg):
        self.send("/me" + msg)

    def update(self):
        self.allPokemons = self.getAllPokemons()
        self.allItems = self.getItems()
        self.attribute = self.getAttribute()
        self.skill = self.getSkill()

    def getAttribute(self):
        csv = readcsv('attribute.csv')
        chart = {}
        for att in csv:
            chart[(att['攻击属性'], att['防守属性'])] = float(att['倍率'])
        return chart

    def getSkill(self):
        csv = readcsv('skill.csv')
        skills = {}
        for skill in csv:
            skills[skill['技能名称']] = skill
        return skills



    def getAllPokemons(self):
        csv = readcsv('pokemon.csv')
        pets = []
        for pet in csv:
            pets.append(PokemonCard(pet['编号'], pet['下阶段'], pet['名字'], pet['属性'], pet['属性2'], int(
                pet['生命值']), int(pet['攻击力']), int(pet['速度']), pet['技能1']))
        pets = sorted(pets, key=lambda x: x.score)

        self.grouped_pets = {}
        print('宝可梦等级与数量：', len(pets))
        for key, group in itertools.groupby(pets, key=lambda x: x.grade):
            pet_list = list(group)
            self.grouped_pets[key] = pet_list
            print(key, len(pet_list))
        return pets

    def getItems(self):
        csv = readcsv('shop.csv')
        items = []
        for item in csv:
            items.append((item['道具'], int(item['价格'])))
        return items

    def getEnemy(self):
        enemys = [
            Player('小红'),
            Player('小明'),
            Player('小黑'),
            Player('小白'),
        ]
        self.enemy = random.sample(enemys, 1)[0]
        self.enemy.team = random.sample(self.allPokemons, 3)

    def getBoss(self):
        self.enemy = Player('BIG BOSS')
        self.enemy.team = random.sample(self.allPokemons, 3)

    def change(self, idx):
        team = self.player.team.copy()
        for i in range(len(idx)):
            self.player.team[i] = team[idx[i]]

    def start(self, name):
        self.stage = 1
        self.round = 0
        self.win = 0
        self.life = 2
        self.coin = 500
        self.bag = ['精灵球']
        self.field_time = 0
        self.shop_time = 0
        self.master = True
        self.player = Player(name)
        self.me(f'欢迎@{self.player.name}来到宝可梦世界！已赠送 精灵球*1、金币*5，快去冒险吧！【/抓捕 宠物编号】【/对战】【/刷新宠物】')
        self.rf_field()
        self.rf_shop()

    def battle(self):
        self.stage = 2
        self.round += 1
        self.send(f'第{self.round}次挑战\n你的对手是{self.enemy.name}！\n' +
                  f'你的队伍是{"、".join([p.name for p in self.player.team])}\n' +
                  f'你的对手是{"、".join([p.name for p in self.enemy.team])}')
        win, logs = Battle(self.player, self.enemy, self.attribute, self.skill).start()
        for log in logs:
            self.send('\n'.join(log))

        self.reward(win)

    def reward(self, win):
        if win:
            self.win += 1
            self.coin += self.round * 2
            self.me(f'你赢了！获得{self.round*2}金币')
        else:
            self.life -= 1
            self.coin += self.round
            self.bag.append('精灵球')
            self.me(f'你输了！获得{self.round}金币和一个精灵球')

        if self.life <= 0:
            self.end()
        else:
            self.rest()

    def rest(self):
        self.stage = 1
        self.me(f'休息一下，你还有{self.life}条命，你赢了{self.win}/{self.round}次，你有{self.coin}个金币。')
        self.field_time = 0
        self.shop_time = 0
        self.rf_field()
        self.rf_shop()

    def rf_field(self):
        n = min(self.round - self.win, 2)
        r = min(self.field_time, 5)
        grade = ['C', 'B', 'A', 'S']
        probs = [[0.80, 0.15, 0.05, 0.00],
                 [0.65, 0.20, 0.10, 0.05],
                 [0.50, 0.25, 0.15, 0.10],
                 [0.40, 0.30, 0.20, 0.10],
                 [0.35, 0.25, 0.25, 0.15],]
        adjust = [[-0.10, -0.03],
                  [0.06, 0.01],
                  [0.03, 0.01],
                  [0.01, 0.01],]

        i = min(max(self.win - 1, 0), len(probs) - 1)
        prob = probs[4]
        for i in range(len(adjust)):
            prob[i] += adjust[i][0] * n + adjust[i][1] * r

        grades = [grade[choice(prob)] for _ in range(3)]
        self.field = [random.sample(self.grouped_pets[g], 1)[0] for g in grades]
        print(n, r, prob, grades)
        self.showField()

    def showField(self):
        self.send('出现的宝可梦：\n' +
                  '\n'.join([f'{i+1}.{p}' for i, p in enumerate(self.field)]))

    def catch(self, idx):
        self.bag.remove('精灵球')
        if random.random()*100 < max(100 - 3 * self.field[idx].score, 10) or self.master:
            if self.master:
                self.master = False
            self.player.team.append(self.field[idx])
            self.me(
                f'你捕捉到了{self.field[idx].name}！目前队伍是{"、".join([f"【{p.attribute+p.attribute2}】{p.name}" for p in self.player.team])}，共{len(self.player.team)}只宝可梦。')
            if len(self.player.team) > 3:
                self.me('你的队伍超过3只，请选择放生多余的宝可梦。')
        else:
            self.me(f'很遗憾，你没有捕捉到{self.field[idx].name}！')

    def release(self, idx):
        coin = self.player.team[idx].score // 5
        p = self.player.team.pop(idx)
        self.coin += coin
        self.me(
            f'你放生了{p.name}， 获得{coin}金币！目前队伍是{"、".join([p.name for p in self.player.team])}，金币有{self.coin}个')

    def upgrade(self, idx):
        old = self.player.team[idx]
        id = old.uid
        new = [u for u in self.allPokemons if u.id == id][0]
        cost = 5 + new.score//3
        if self.coin < cost:
            self.me(f'你的金币只有{self.coin}，不足{cost}， 无法将{old}升级为{new}')
        else:
            self.player.team[idx] = new
            self.me(f'你花费了{cost}金币，将{old}升级为{new}！目前金币有{self.coin}个')


    def rf_shop(self):
        self.shop = random.sample(self.allItems, 4)
        self.showShop()

    def showShop(self):
        self.send(
            '小店\n' + '\n'.join([f'{i+1}. {item} - {price}' for i, (item, price) in enumerate(self.shop)]))

    def buy(self, idx):
        n, p = self.shop.pop(idx)
        self.coin -= p
        if n == '大师球':
            self.master = True
            self.bag.append('精灵球')
            self.me(f'你花费{p}金币购买了【{n}】，获得【精灵球】*1，下次抓捕必定成功，目前金币有{self.coin}')
        else:
            self.bag.append(n)
            self.me(f'你花费{p}金币购买了【{n}】，目前金币有{self.coin}')

    def showBag(self):
        if len(self.bag):
            self.send(
                '道具\n' + '\n'.join([f'{i+1}. {item}' for i, item in enumerate(self.bag)]))
        else:
            self.me('你没有道具！')

    def next(self):
        self.stage = 1
        self.getEnemy()
        self.battle()

    def end(self):
        self.stage = 0
        self.me(f'游戏结束！你赢了{self.win}/{self.round}次，你有{self.coin}个金币。')

    def use(self, idx):
        item = self.bag.pop(idx)
        if item == '恢复药':
            self.life += 1
            self.me(f'你使用了恢复药，你有{self.life}条命。')


class Pokemon(Module):
    def __init__(self, bot):
        super().__init__(bot)
        self.game = Game(bot)
        self.send = self.game.send
        self.me = self.game.me
        self.doc()
        self.help()

    @property
    def cmds(self):
        cmd_dict = {
            'help': r'^\/指令',
            'doc': r'^\/说明',
            'state': r'^\/s',
            'quit': r'^\/(游戏|结束)',
            'update': r'^\/更新',
            'start': r'^\/go',
            'showTeam': r'^\/队伍',
            'change': r'^\/换位\s+\d+',
            'next': r'^\/对战',
            'field': r'^\/野区',
            'catch': r'^\/抓捕\s+\d+',
            'release': r'^\/释放\s+\d+',
            'upgrade': r'^\/升级\s+\d+',
            'rf_field': r'^\/刷新(野区)?\s*$',
            'rf_shop': r'^\/刷新小店',
            'shop': r'^\/小店',
            'buy': r'^\/购买\s+\d+',
            'bag': r'^\/道具',
            'use': r'^\/使用\s+\d+',
        }
        return cmd_dict

    def switch(self, msg):
        msgs = msg.message.split()
        if len(msgs) == 1 or msgs[1] != "宝可梦":
            self.on = False
            self.me("【宝可梦】游戏已关闭")
        else:
            self.on = True
            self.game.stage = 0
            self.doc()

    def help(self, msg=None):
        cmds = '''指令：
/go 开始游戏┃/s 查看状态
/队伍 查看队伍┃/换位 顺序
/野区 查看野区┃/刷新 刷新野区
/抓捕 编号┃/释放 编号
/道具 查看道具┃/小店 查看小店
/购买 编号┃/使用 物品名
/刷新小店 刷新小店┃/指令 查看指令
/对战 挑战对手┃/结束 结束游戏
'''
        self.bot.send(cmds)

    def doc(self, msg=None):
        self.bot.send_url(
            '图文版游戏说明：', 'https://docs.qq.com/aio/DUmdZeHFteElNa3Z0?p=zvCGUc66a0wtg0EcxJjPuq')
    
    def update(self, msg):
        self.game.update()
        self.me(f'更新成功！共{len(self.game.allPokemons)}只宝可梦')

    def start(self, msg):
        self.game.start(msg.user.name)

    def quit(self, msg):
        if self.chk(msg):
            return
        self.game.end()

    def state(self, msg=None):
        if self.game.stage == 0:
            self.me(f'【报名阶段】发送 /go 开始游戏')
        if self.game.stage == 1:
            self.me(
                f'【休息阶段】@{self.game.player}还有{self.game.life}条命，你赢了{self.game.win}/{self.game.round}次，你有{self.game.coin}个金币。')
        if self.game.stage == 2:
            self.me(f'【战斗阶段】@{self.game.player} VS {self.game.enemy}')
        if self.game.stage == 3:
            self.me(f'【BOSS阶段】@{self.game.player} 你有{self.game.coin}个金币。')
    
    def chk(self, msg):
        if self.game.stage != 1:
            self.me('只能在【休息阶段】使用该命令！')
            self.state()
            return True
        if self.game.player.name != msg.user.name:
            self.me(f'当前玩家是 @{self.game.player.name}。 @{msg.user.name}不是当前玩家！')
            return True
        return False

    def showTeam(self, msg):
        if self.chk(msg):
            return
        self.bot.send('你的队伍：\n' +
                      '\n'.join([f'{i+1}.{p}' for i, p in enumerate(self.game.player.team)]))

    def change(self, msg):
        if self.chk(msg):
            return
        idx = [int(c)-1 for c in msg.message.split()[1]]
        if len(idx) != len(self.game.player.team):
            self.me('换位顺序与队伍数量不符！')
            return
        self.game.change(idx)
        self.me(
            '更换出战顺序为：' + '、'.join([p.name for p in self.game.player.team]))

    def next(self, msg):
        if self.chk(msg):
            return
        if len(self.game.player.team) > 3:
            self.me('你的队伍超过3只，请选择放生多余的宝可梦。')
            return
        if len(self.game.player.team) == 0:
            self.me('你的队伍没有宝可梦！本局判负！')
            self.game.round += 1
            self.game.reward(False)
            return
        self.game.next()

    def field(self, msg):
        if self.chk(msg):
            return
        self.game.showField()

    def catch(self, msg):
        if self.chk(msg):
            return
        if not any(i == '精灵球' for i in self.game.bag):
            self.me('你没有精灵球了！')
            return

        idx = int(msg.message.split()[1])-1
        if idx < 0 or idx >= len(self.game.field):
            self.me('输入编号超出范围！')
            return

        self.game.catch(idx)

    def release(self, msg):
        if self.chk(msg):
            return
        idx = int(msg.message.split()[1])-1
        if idx < 0 or idx >= len(self.game.player.team):
            self.me('输入编号超出范围！')
            return
        self.game.release(idx)
    
    def upgrade(self, msg):
        if self.chk(msg):
            return
        idx = int(msg.message.split()[1])-1
        if idx < 0 or idx >= len(self.game.player.team):
            self.me('输入编号超出范围！')
            return
        p = self.game.player.team[idx]
        if not p.up:
            self.me(f'{p}不可升级')
            return
        self.game.upgrade(idx)

    def rf_field(self, msg):
        if self.chk(msg):
            return
        if not any(i == '精灵球' for i in self.game.bag):
            self.me('你没有精灵球了！刷新野区也没法抓╮（╯＿╰）╭')
            return
        cost = self.game.field_time + 1
        if self.game.coin < cost:
            self.me(f'你的金币只有{self.game.coin}，不足{cost}！')
            return
        self.game.coin -= cost
        self.game.field_time += 1
        self.me(f'第{self.game.field_time}次刷新野区，花费{cost}金币，目前金币有{self.game.coin}个')
        self.game.rf_field()

    def rf_shop(self, msg):
        if self.chk(msg):
            return
        cost = self.game.shop_time + 1
        if self.game.coin < cost:
            self.me(f'你的金币只有{self.game.coin}，不足{cost}！')
            return
        self.game.coin -= cost
        self.game.shop_time += 1
        self.me(f'第{self.game.shop_time}次刷新小店，花费{cost}金币，目前金币有{self.game.coin}个')
        self.game.rf_shop()

    def shop(self, msg):
        if self.chk(msg):
            return
        self.game.showShop()

    def buy(self, msg):
        if self.chk(msg):
            return
        idx = int(msg.message.split()[1])-1
        if idx < 0 or idx >= len(self.game.shop):
            self.me('输入编号超出范围！')
            return
        if self.game.coin < self.game.shop[idx][1]:
            self.me(f'你的金币只有{self.game.coin}，不足{self.game.shop[idx][1]}！')
            return
        self.game.buy(idx)

    def bag(self, msg):
        if self.chk(msg):
            return
        self.game.showBag()

    def use(self, msg):
        if self.chk(msg):
            return
        idx = int(msg.message.split()[1])-1
        if idx < 0 or idx >= len(self.game.bag):
            self.me('输入编号超出范围！')
            return
        if self.game.bag[idx] == '精灵球':
            self.me('精灵球不能直接使用！请输入 /抓捕 宝可梦编号')
            return
        self.game.use(idx)
