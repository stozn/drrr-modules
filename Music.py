import json
import re
from modules.module import Module
import requests

API_QQ = 'https://wanghun.top/api/mirai/yy.php'
API_163_search = 'http://cloud-music.pl-fe.cn/search'
API_163_song = 'http://music.163.com/song/media/outer/url?id='
API_ghxi = 'https://music.ghxi.com/wp-admin/admin-ajax.php'
max_results = 7

class Music(Module):
    def __init__(self, bot):
        super().__init__(bot)
        self.songs = None
        self.token = '691283'
        self.defalut_source = 'qq'

    @property
    def cmds(self):
        cmd_dict = {
                    'search': r'^\/搜索\s+\S',
                    'search_qq': r'^\/(qq|QQ)\s+\S',
                    'search_163': r'^\/(163|wy|网易)\s+\S',
                    'search_ghxi': r'^\/(gh|果核)\s+\S',
                    'play': r'^\/播放\s+\d+$',
                    'set_token': r'^\/密码\s+\d{6}\s*$',
                    'set_defalut_source': r'^\/换源\s+(qq|wy)\s*$',
                    }
        return cmd_dict
    
    def search(self, msg):
        self.bot.send(f'/me正在使用{self.defalut_source}音乐源搜索【{msg.message.split(" ", 1)[1].strip()}】中')
        if self.defalut_source == 'qq':
            self.search_qq(msg)
        elif self.defalut_source == 'wy':
            self.search_163(msg)
        elif self.defalut_source == 'ghxi':
            self.search_ghxi(msg)
    
    def search_qq(self, msg):
        self.keywords = re.sub(r'\s+', '%2b', msg.message.split(' ', 1)[1].strip())
        resp = requests.get(API_QQ, params={'msg': self.keywords, 'g': 30})
        if resp.status_code == 200:
            resp = resp.text
            songs = [(i, x) for i,x in enumerate(resp.split('\n'))]
            songs = [(i, x[x.find('：')+1:len(x) if x.find('*')<0 else x.find('*')].replace(' — ', '-')) for i,x in songs if '收费' not in x][:max_results]
            if songs:
                self.songs = [x for i,x in songs]
                self.songids = [i+1 for i,x in songs]
                self.bot.send('\n'.join([str(i+1) + '.' + x for i,x in enumerate(self.songs)][:-1]))
                self.source = 'QQ'
            else:
                self.bot.send('/me搜索结果为空')
        else:
            self.bot.send('/me搜索失败')
    
    def search_163(self, msg):
        self.keywords = msg.message.split(' ', 1)[1].strip()
        resp = requests.get(API_163_search, params={'keywords': self.keywords, 'limit': 30})
        if resp.status_code == 200:
            resp = resp.json()
            playlist = [x for x in resp['result']['songs'] if not x['fee']][:max_results]
            if playlist:
                self.songs = [s['name'] + '-' + s['artists'][0]['name'] for s in playlist]
                self.songids = [s["id"] for s in playlist]
                res = '\n'.join([str(n+1) + '.' + s for n, s in enumerate(self.songs)])
                self.bot.send(res)
                self.source = 'wy'
            else:
                self.bot.send('/me搜索结果为空')
        else:
            self.bot.send('/me搜索失败')
    
    def set_token(self, msg):
        if self.get_ghxi_cookies():
            self.bot.send('/me原密码仍有效，未进行更改')
            return
        self.token = msg.message.split(' ', 1)[1].strip()
        self.bot.dm(msg.user.id, f'密码被设置为【{self.token}】')
        if self.get_ghxi_cookies():
            self.bot.send('/me新密码有效')
        else:
            self.bot.send('/me新密码仍无效')
    
    def set_defalut_source(self, msg):
        self.defalut_source = msg.message.split(' ')[1].strip()
        self.bot.send(f'/me默认音乐源被设置为【{self.defalut_source }】')
    
    def get_ghxi_cookies(self):
        data = {'action': 'gh_music_ajax',
                'type': 'postAuth',
                'code': self.token,
                }
        response = requests.post(API_ghxi, data)
        resp = json.loads(response.text)
        print(resp['msg'])
        if resp['code'] == 200:
            self.cookies =  response.cookies
            return True
        else:
            self.bot.send('/me果核音乐密码已失效，请使用【果核剥壳】小程序获取密码，再使用 /密码 123456 设置密码')
            return False
    
    def search_ghxi(self, msg):
        if self.get_ghxi_cookies():
            self.bot.send(f'/me使用【gh-{self.defalut_source}】音乐源搜索【{msg.message.split(" ", 1)[1].strip()}】中')
            self.keywords = re.sub(r'\s+', '%2b', msg.message.split(' ', 1)[1].strip())
            print(self.keywords)
            data = {'action': 'gh_music_ajax',
                'type': 'search',
                'music_type': self.defalut_source,
                'search_word': self.keywords,
                }
            resp = requests.post(API_ghxi, data, cookies=self.cookies).text
            resp = json.loads(resp)
            if(resp['code'] == 200):
                if 'data' in resp:
                    data = resp['data'][:max_results]
                    self.songs = [ x['songname'] + '-' + x['singer'] for x in data]
                    self.songids = [ x['songid'] for x in data]
                    res = '\n'.join([str(n+1) + '.' + s for n, s in enumerate(self.songs)])
                    self.bot.send(res)
                    self.source = 'ghxi'
                else:
                    self.bot.send('/me搜索结果为空')
            else:
                self.bot.send('/me搜索失败')

    def play(self, msg):
        if self.songs is None:
            self.bot.send('/me请先搜索')
            return
        index = int(msg.message.split(' ', 1)[1].strip()) - 1
        if index < 0 or index >= len(self.songs):
            self.bot.send('/me请输入正确的序号')
            return
        
        if self.source == 'QQ':
            resp = requests.get(API_QQ, params={'msg': self.keywords, 'n': self.songids[index]})
            if resp.status_code == 200:
                url = resp.text.split('链接:')[1]
            else:
                self.bot.send('/me获取链接失败')
                return
        if self.source == 'wy':
            url = f'{API_163_song}{self.songids[index]}'
            response = requests.get(url, allow_redirects=False)
            url = response.headers.get('Location')
            if '404' in url:
                self.bot.send('/me获取链接失败')
                return
        if self.source == 'ghxi':
            if self.get_ghxi_cookies():
                data = {'action': 'gh_music_ajax',
                    'type': 'getMusicUrl',
                    'music_type': self.defalut_source,
                    'music_size': 128,
                    'songid': self.songids[index],
                    }
                resp = requests.post(API_ghxi, data, cookies=self.cookies).text
                resp = json.loads(resp)
                if(resp['code'] == 200):
                    url = resp['url']
                else:
                    self.bot.send('/me获取链接失败')
                    return
            else:
                return
        
        print(self.songs[index], url)
        self.bot.dm_url(msg.user.id, f'【{self.songs[index]}】下载链接：', url)
        self.bot.music(self.songs[index], url)