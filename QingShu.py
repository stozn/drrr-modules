from modules.module import Module
import random

def ckn(username):
    return username.replace('@', '').strip()

def pop(my_list):
    return my_list.pop(random.randrange(len(my_list)))

# 全卡牌
class Card:
    def __init__(self, mp, name, desc):
        self.mp = mp
        self.name = name
        self.desc = desc
    
    def __str__(self):
        return self.name

SW = Card(1, '守卫', '猜测某人的手牌，猜对则对方出局')

JS= Card(2, '祭司', '查看某人的手牌')

NJ= Card(3, '男爵', '与某人拼点，MP小的出局')

SN= Card(4, '侍女', '免疫所有技能，直到再次轮到自己')

WZ= Card(5, '王子', '使某人弃牌并重新抽取')

GW= Card(7, '国王', '与某人交换手牌')

NBJ= Card(8, '女伯爵', '持有国王或王子，则必须打出此卡')

GZ= Card(9, '公主', '打出或丢弃此卡，玩家被淘汰')

class Player:
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.cards = []
        self.used = []
        self.alive = True
        self.protected = False
        self.score = 0

    def __str__(self):
        return self.name
    
    def has(self, card):
        return any(c.name == card for c in self.cards)

    def get(self, card):
        self.cards.append(card)

    def lose(self, card):
        if not self.has(card):
            return False
        
        for c in self.cards:
            if c.name == card:
                self.cards.remove(c)
                return c

    def showCards(self):
        return f"@{self.name} 的手牌：\n" + "\n".join(f"⭐{c.mp}【{c}】" + 
                                        f"{c.desc}" for  c in self.cards)
    def showUsed(self):
        return f"@{self.name} ：" + "".join(f"【{c}】" for c in self.used)
        
    def use(self, card):
        if not self.has(card) or card in ["王子", "国王"] and self.has("女伯爵"):
            return False
        self.used.append(self.lose(card))
        return True


class Game:
    def __init__(self, bot):
        self.bot = bot
        self.dm = bot.dm
        self.send = bot.send
        
        self.players = []
        self.deck = []
        self.discards = []

        self.stage = 0
        self.cur = None
        self.curCard = None
    
    def me(self, msg):
        self.send("/me" + msg)
    
    def reset(self):
        self.players = []
        self.deck = []
        self.discards = []

        self.stage = 0
        self.cur = None
        self.curCard = None
    
    def join(self, name, id):
        if any(p.name == name for p in self.players):
            self.me(f"@{name} 你已经加入了游戏")
        else:
            self.players.append(Player(name, id))
            self.me(f"@{name} 加入游戏")
    
    def quit(self, name):
        p = [p for p in self.players if p.name == name]
        if p:
            self.players.remove(p[0])
            self.me(f"@{name} 退出游戏")
        else:
            self.me(f"@{name} 你没有加入游戏")
    
    def start(self):
        self.me("开始发牌...")
        self.cards = [SW] * 5 + [JS] * 3 + [NJ] * 2 + [SN] * 2 + \
                        [WZ] * 2 + [GW] * 1 + [NBJ] * 1 + [GZ] * 1
        
        random.shuffle(self.cards)
        num = 1
        if len(self.players) == 2:
            num = 3
        self.deck = self.cards[:len(self.cards)-num]
        self.discards = self.cards[len(self.cards)-num:]

        for p in self.players:
            p.get(pop(self.deck))
            self.dm(p.id, p.showCards())
        
        self.cur = self.players[random.randrange(len(self.players))]
        self.next()
        
    def next(self):
        self.stage = 1

        alive = [p for p in self.players if p.alive]
        if len(alive) == 1:
            self.end()
            return
        
        idx = (self.players.index(self.cur) + 1) % len(self.players)
        while not self.players[idx].alive:
            idx = (idx + 1) % len(self.players)
            if idx == self.players.index(self.cur):
                self.end()
                break
        self.cur = self.players[idx]
        if len(self.deck):
            self.cur.protected = False
            self.cur.get(pop(self.deck))
            self.dm(self.cur.id, self.cur.showCards())
            self.me(f"请 @{self.cur} 开始行动，【/使用 卡牌名】，牌堆剩余{len(self.deck)}张牌")
        else:
            self.end()

    def end(self):
        self.stage = 3
        self.showPlayers()
        self.showResult()
        self.showScore()

    def restart(self):
        self.send("新一轮开始！")
        for p in self.players:
            p.cards = []
            p.used = []
            p.alive = True
            p.protected = False
        self.start()      
    
    def showPlayers(self):
        if self.stage == 0:
            self.send("玩家:\n" + "\n".join(f"{i + 1}.@{p}" for i, p in enumerate(self.players)))
        elif self.stage < 3:
            self.send("玩家:\n" + "\n".join(f"{i + 1}.@{p} " + 
                    f"{'侍女守护中' if p.protected and p.alive else '' if p.alive else f'已出局'}"
                                     for i, p in enumerate(self.players)))
        else:
            self.send("玩家身份:\n" + "\n".join(f"{i + 1}.@{p} " + 
                    f'{"已出局" if not p.alive else f"⭐{p.cards[0].mp}【{p.cards[0]}】"}' for i, p in enumerate(self.players)))
    
    def showScore(self):
        rank = sorted(self.players, key=lambda p: p.score, reverse=True)
        self.send("积分榜\n" + "\n".join(f"{i + 1}.@{p} {p.score} 积分" for i, p in enumerate(rank)))
                    
    def showUsed(self):
        self.send("弃牌区:\n" + "\n".join(f"{i + 1}.{p.showUsed()}" for i, p in enumerate(self.players)))

    def showResult(self):
        alive = [p for p in self.players if p.alive]
        if len(alive) == 1:
            alive[0].score += 1
            self.send(f"游戏结束！\n唯一未出局的 @{alive[0]} \n成功传递情书！\n【/继续】进行下一轮")
        else:
            winner = max(alive, key=lambda p: p.cards[0].mp)
            winner.score += 1
            self.send(f"游戏结束！\nMP最高的 @{winner} 成功传递情书！\n【/继续】进行下一轮")
        
    def showState(self):
        if self.stage == 0:
            self.me("报名阶段")
        elif self.stage == 1:
            self.me(f"@{self.cur} 行动中，牌堆剩余{len(self.deck)}张牌")
        elif self.stage == 2:
            self.me(f"@{self.cur} 发动【{self.curCard}】技能中，【/取消】取消技能（防卡死），牌堆剩余{len(self.deck)}张牌")
        elif self.stage == 3:
            self.showResult()

    def use(self, card):
        if not self.cur.use(card):
            self.dm(self.cur.id, f"@{self.cur} 你没有【{card}】或你必须打出【女伯爵】")
            return False
        
        self.stage = 2
        self.curCard = card
        
        if card == "守卫":
            self.me(f"@{self.cur} 发动【守卫】，请猜测一名玩家的手牌【/猜测 玩家名 手牌名】")
        elif card == "祭司":
            self.me(f"@{self.cur} 发动【祭司】，请查看一名玩家的手牌【/查看 玩家名】")
        elif card == "男爵":
            self.me(f"@{self.cur} 发动【男爵】，请与一名玩家拼点【/拼点 玩家名】")
        elif card == "侍女":
            self.me(f"@{self.cur} 发动【侍女】，免疫所有技能，直到再次轮到自己")
            self.cur.protected = True
            self.next()
        elif card == "王子":
            self.me(f"@{self.cur} 发动【王子】，请选择一名玩家使其弃牌重摸【/弃牌 玩家名】")
        elif card == "国王":
            self.me(f"@{self.cur} 发动【国王】，请选择一名玩家与其交换手牌【/交换 玩家名】")
        elif card == "女伯爵":
            self.me(f"@{self.cur} 打出【女伯爵】（无效果）")
            self.next()
        elif card == "公主":
            self.send(f"@{self.cur} 打出【公主】，你被淘汰\n剩余手牌为⭐{self.cur.cards[0].mp}【{self.cur.cards[0]}】")
            self.cur.alive = False
            self.next()
        else:
            self.me(f"@{self.cur} 打出【{card}】????")
            self.next()

    

    
class QingShu(Module):
    def __init__(self, bot):
        super().__init__(bot)
        self.game = Game(bot)
        self.game.me("【情书】游戏开始, [+1] 加入, [-1] 退出, [/p] 玩家," + \
                "[/go] 开始, [/游戏] 重新报名, [/指令] 指令列表")

    @property
    def cmds(self):
        cmd_dict = {
                    'help': r'^\/指令',
                    'reset': r'^\/游戏',
                    'restart': r'^\/继续',
                    'cardSet': r'^\/卡组',
                    'state': r'^\/s',
                    'join': r'^\+1',
                    'quit': r'^\-1',
                    'showPlayers': r'^\/p',
                    'start': r'^\/go',
                    'showCards': r'^\/手牌',
                    'showScore': r'^\/积分',
                    'showUsed': r'^\/弃牌区',
                    'use': r'^\/使用\s+\S+',
                    'cancel': r'^\/取消',
                    'guess': r'^\/猜测\s+\S+\s+\S+',
                    'check': r'^\/查看\s+\S+',
                    'compare': r'^\/拼点\s+\S+',
                    'discard': r'^\/弃牌\s+\S+',
                    'exchange': r'^\/交换\s+\S+',
                    }
        return cmd_dict
    
    def help(self, msg):
        cmds='''指令列表：
/游戏 回到报名阶段┃/go 开始游戏
/s 查看状态┃/p 查看玩家
+1 加入游戏┃-1 退出游戏
/手牌 查看手牌┃/卡组 查看卡组
/积分 查看积分榜┃/取消 取消技能
/弃牌区 查看所有玩家的弃牌牌
'''
        self.bot.send(cmds)
    
    def cardSet(self, msg):
        cards='''全卡组：
守卫：5
祭司：3
男爵：2
侍女：2
王子：2
国王：1
女伯爵：1
公主：1
'''
        self.bot.send(cards)
    
    def reset(self, msg):
        self.game.reset()
        self.game.me("【情书】游戏开始, [+1] 加入, [-1] 退出, [/p] 玩家," + \
                "[/go] 开始, [/游戏] 重新报名, [/指令] 指令列表")
    
    def restart(self, msg):
        self.game.restart()
    
    def state(self, msg):
        self.game.showState()
    
    def join(self, msg):
        if self.game.stage == 0:
            self.game.join(msg.user.name, msg.user.id)
    
    def quit(self, msg):
        if self.game.stage == 0:
            self.game.quit(msg.user.name)
    
    def showPlayers(self, msg):
        self.game.showPlayers()
    
    def start(self, msg):
        if 0 < self.game.stage < 3:
            self.game.me("游戏已经开始")
            return
        
        if self.game.stage == 3:
            self.game.me("游戏已结束！ /游戏 重新报名 | /继续 开始下一轮")
            return
        
        if 1< len(self.game.players) < 6:
            self.game.start()
        else:
            self.game.me(f"本游戏支持2-5人游戏，当前玩家数为{len(self.game.players)}")
        
    
    def showCards(self, msg):
        if self.game.stage > 0:
            player = [p for p in self.game.players if p.name == msg.user.name]
            if player:
                self.game.dm(msg.user.id, player[0].showCards())
            else:
                self.game.me(f"@{msg.user.name} 你没有加入游戏")
        else:
            self.game.me("游戏未开始")
    
    def showScore(self, msg):
        if self.game.stage > 0:
            self.game.showScore()
        else:
            self.game.me("游戏未开始")
        
    def showUsed(self, msg):
        if self.game.stage > 0:
            self.game.showUsed()
        else:
            self.game.me("游戏未开始")
    
    def use(self, msg):
        if self.game.stage == 1:
            if msg.user.name != self.game.cur.name:
                self.game.me(f"@{msg.user.name} 不是你的回合")
            else:            
                self.game.use(msg.message.split()[1])
        else:
            self.game.showState()
    
    def cancel(self, msg):
        if self.game.stage == 2:
            if msg.user.name != self.game.cur.name:
                self.game.me(f"@{msg.user.name} 不是你的回合")
            else:
                self.game.me(f"@{msg.user.name} 取消【{self.game.curCard}】技能")
                self.game.curCard = None
                self.game.next()
        else:
            self.game.me("当前没有技能正在发动")
    
    def checkSkill(self, user, card):
        if self.game.stage == 2:
            if user != self.game.cur.name:
                self.game.me(f"@{user} 不是你的回合")
                return False
            
            if self.game.curCard != card:
                self.game.me(f"@{user} 你没有发动【{card}】")
                return False
            return True
        else:
            self.game.showState()
            return False
    
    def checkPlayer(self, user, to_p):
        player = [p for p in self.game.players if p.name == to_p]
        if not player:
            self.game.me(f"@{user} 玩家 @{to_p} 不存在")
            return False
        
        p = player[0]
        if not p.alive:
            self.game.me(f"@{user} 玩家 @{p} 已出局") 
            return False
        if p.protected:
            self.game.me(f"@{user} 玩家 @{p} 正在被侍女守护，所有技能对其无效")
            return False
        return p

    
    def guess(self, msg):
        user = msg.user.name
        to_p = ckn(msg.message.split()[1])
        card = msg.message.split()[2]
        
        if not self.checkSkill(user, "守卫"):
            return
        
        p = self.checkPlayer(user, to_p)
        if not p:
            return
        
        if card == "守卫":
            self.game.me(f"@{user} 不可以猜测对方手牌为【守卫】")
            return
                        
        if p.has(card):
            self.game.send(f"@{user} 猜测 @{p} 的手牌为【{card}】正确，@{p} 出局")
            p.alive = False
            p.used.append(p.lose(p.cards[0].name))
            self.game.next()
        else:
            if any(c.name == card for c in self.game.cards):
                self.game.me(f"@{user} 猜测 @{p} 的手牌为【{card}】错误")
                self.game.next()
            else:
                self.game.me(f"@{user} 本卡组无【{card}】")
        

    def check(self, msg):
        user = msg.user.name
        to_p = ckn(msg.message.split()[1])
        
        if not self.checkSkill(user, "祭司"):
            return
        
        p = self.checkPlayer(user, to_p)
        if not p:
            return
        
        self.game.me(f"@{user} 查看 @{p} 的手牌")
        self.game.dm(msg.user.id, p.showCards())
        self.game.next()
    
    def compare(self, msg):
        user = msg.user.name
        to_p = ckn(msg.message.split()[1])
        
        if not self.checkSkill(user, "男爵"):
            return
        
        p = self.checkPlayer(user, to_p)
        if not p:
            return
        
        c1 = self.game.cur.cards[0]
        c2 = p.cards[0]
        
        if c1.mp > c2.mp:
            self.game.send(f"@{user} 与 @{p} 拼点，@{p} 出局, 手牌为⭐{c2.mp}【{c2}】")
            p.alive = False
            p.used.append(p.lose(p.cards[0].name))
            self.game.next()
        elif c1.mp < c2.mp:
            self.game.send(f"@{user} 与 @{p} 拼点，@{user} 出局, 手牌为⭐{c1.mp}【{c1}】")
            self.game.cur.alive = False
            self.game.cur.used.append(self.game.cur.lose(self.game.cur.cards[0].name))
            self.game.next()
        else:
            self.game.me(f"@{user} 与 @{p} 拼点，平局")
            self.game.next()
    
    def discard(self, msg):
        user = msg.user.name
        to_p = ckn(msg.message.split()[1])
        
        if not self.checkSkill(user, "王子"):
            return
        
        p = self.checkPlayer(user, to_p)
        if not p:
            return
        
        if p.cards[0].name == "公主":
            self.game.send(f"@{user} 使 @{p} 弃掉⭐{p.cards[0].mp}【{p.cards[0]}】，@{p} 出局")
            p.alive = False
            p.used.append(p.lose(p.cards[0].name))
            self.game.next()
            return
        
        self.game.me(f"@{user} 使 @{p} 弃掉⭐{p.cards[0].mp}【{p.cards[0]}】，并重新抽取一张牌")
        p.used.append(p.lose(p.cards[0].name))

        if len(self.game.deck):
            p.get(pop(self.game.deck))
        else:
            p.get(pop(self.game.discards))
        
        self.game.dm(p.id, p.showCards())
        self.game.next()
    
    def exchange(self, msg):
        user = msg.user.name
        to_p = ckn(msg.message.split()[1])
        
        if not self.checkSkill(user, "国王"):
            return
        
        p = self.checkPlayer(user, to_p)
        if not p:
            return
        
        self.game.me(f"@{user} 与 @{p} 交换手牌")
        p.cards[0], self.game.cur.cards[0] = self.game.cur.cards[0], p.cards[0]
        self.game.dm(p.id, p.showCards())
        self.game.dm(self.game.cur.id, self.game.cur.showCards())
        self.game.next()
