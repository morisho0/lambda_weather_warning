# -*- coding: utf-8 -*-

import requests
from lxml import etree
import os

def main():
    r = requests.get('http://www.jma.go.jp/jp/warn/319_table.html')
    dic = parse(r.text.replace('<br>', ''))
    str = to_str(dic)
    res = post_to_slack(str)

# output
# {
#   '警報': {
#     '千代田区': ['大雨', '洪水'],
#     '渋谷区': [''],
#   }
# }

def parse(html):
    dest = {'war': {}, 'adv': {}}
    types = []
    et = etree.HTML(html)
    table = et.xpath("//table[@id='WarnTableTable']")[0]
    rows = list(table)
    del rows[0] # 警報 or 注意報 はいらない
    ths = list(rows[0])
    for th in ths:
        types.append(th.text)
    del rows[0]

    for tr in rows:
        if list(tr)[0].tag == 'th':
            break

        place = ''
        start_index = 0
        for i, td in enumerate(list(tr)):
            if 'rowspan' in td.attrib and 'align' in td.attrib:
                place = td.text
            if len(td.xpath('a')) > 0:
                # for a in td.xpath('a'):
                #     if a.text != None:
                #         place = a.text
                start_index = i + 1
                continue
            if td.text == '●' and len(place) > 0:
                index = i - start_index
                if index < 7:
                    if place not in dest['war']:
                        dest['war'][place] = []
                    if types[index] not in dest['war'][place]:
                        dest['war'][place].append(types[index])
                else:
                    if place not in dest['adv']:
                        dest['adv'][place] = []
                    if types[index] not in dest['adv'][place]:
                        dest['adv'][place].append(types[index])
    return dest

def to_str(dic):
    dest_str = ''
    if len(dic['war']) > 0:
        dest_str += "`警報`\n"
    for key, val in dic['war'].items():
        dest_str += '*' + key + "*\n"
        for v in val:
            dest_str += '- ' + v + "\n"
    if len(dic['adv']) > 0:
        dest_str += "`注意報`\n"
    for key, val in dic['adv'].items():
        dest_str += '*' + key + "*\n"
        for v in val:
            dest_str += '- ' + v + "\n"
    return dest_str

def post_to_slack(str):
    token = os.environ['SLACK_BOT_TOKEN']
    channel = os.environ['CHANNEL']
    params = {'token': token, 'channel': channel, 'text': str, 'as_user': True}
    res = requests.post('https://slack.com/api/chat.postMessage', params=params)
    return res

def lambda_handler(e, c):
    main()

if __name__ == '__main__':
    main()
