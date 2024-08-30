import json
import os
import random
import time

from loguru import logger
from playwright.sync_api import sync_playwright
from retrying import retry


def Timer(f):
    def inner(*arg, **kwarg):
        s_time = time.time()
        res = f(*arg, **kwarg)
        e_time = time.time()
        logger.info('cost：{},res: {}'.format(e_time - s_time, res))
        return res

    return inner


@Timer
def solve(_browser):
    page = _browser.new_page()
    page.goto(f"file:///{os.path.abspath('tmp.html')}")
    slide_btn = page.query_selector(".btn_slide")
    slide_scale = page.query_selector(".nc_scale")
    btn_box = slide_btn.bounding_box()
    width = slide_scale.bounding_box()['width'] + btn_box['width']
    offsets = []
    while width > 0:
        offset = min(random.randint(50, 70), width)
        width -= offset
        offsets.append(offset)

    x = btn_box['x'] + btn_box['width'] / 2
    y = btn_box['y'] + btn_box['height'] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    for offset in offsets:
        page.mouse.move(x, y)
        x += offset
    page.mouse.up()

    @retry()
    def get_result():
        return page.query_selector("#mync").inner_html()

    ret = json.loads(get_result())
    page.close()
    return ret


def get_edge_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True, channel="msedge")
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/91.0.4472.124 Safari/537.36"
    )
    context.add_init_script(script='Object.defineProperty(navigator, "webdriver", {get: () => undefined})')

    return context


if __name__ == '__main__':
    br = get_edge_browser()
    res = solve(br)
    import requests

    url = f"https://www.allcpp.cn/allcpp/ticket/afs/valid.do?sessionId={res['sessionId']}&sig={res['sig']}&outToken={res['token']}"
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5,ja;q=0.4',
        'content-type': 'application/json;charset=UTF-8',
        'cookie': '',
        'origin': 'https://cp.allcpp.cn',
        'priority': 'u=1, i',
        'referer': 'https://cp.allcpp.cn/',
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'
    }

    response = requests.request("POST", url, headers=headers)
    print(response.text)
