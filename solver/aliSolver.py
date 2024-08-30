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
        'cookie': 'JALKSJFJASKDFJKALSJDFLJSF=8396121218369a45585264b7794166834295c7cad120.244.237.59_468123481; token=O2rVRtanPmOub8MwfT6USnDDd3JgEgovNx7j6L1WkAZt6P1WYT5mrz0yM+sSVxAq25AObGm6pD7Mu4aYINzg/E05+p9gxc+xKRAgELi7pJAKPvw7lmeIXp6haLDYLZAnddDjZsC/zjTS69ou6CCFwNCh1Tme6DWNtjWATQ0cuPs=; acw_tc=6f0d674117250438179142420ee02a295f7f94e2938a7903190b2cc33b; cdn_sec_tc=6f0d674117250438179142420ee02a295f7f94e2938a7903190b2cc33b; JSESSIONID=031420A71235A729E389A2F350F3A63A; Hm_lvt_75e110b2a3c6890a57de45bd2882ec7c=1722742197,1725029294,1725031208,1725043831; HMACCOUNT=08C50FA058BE50FD; Hm_lpvt_75e110b2a3c6890a57de45bd2882ec7c=1725043836; tfstk=f5pqdSfSExH4dKYhKiBN4pDUnT6Apt0BSd_1jhxGcZbmkOOPQULkhN66jNRNrHxXhEiAjU8My1O6G19wyh8HGG9wXRSMjFnA5mhWDnBOI2gQQvtvD9J1LIvVo_qk2MPgs6L2AuXOI2gSji87GOLCvR8r03mPfGr0SFjcr0SAvO2cs-VuraQlSOb0n72lvMs0mRYMq0SOrNc2k1CbNZfmY7Dzv2wCys7H4XegQcSzRw-czR2Gui5qNnbzIRvyw-VZAZcLVNBfknj2WveAn1RpfG8q3-YwvLLPqeDadZxJAB1vnfwCTT7V1KXUjxxP3Z5Hh6r0hexyjB1yFDDd3tbD1tK_Yqty3EtvUhZgZtWXa6JVKvUc5QteQGJtWY8evLLPqeDZog-zWg0v9dd4S55c2g7I40RBgH1Pg8f-45FOZzjPRD7Q65Cc2g7I40PT6_cl4wiFR; JALKSJFJASKDFJKALSJDFLJSF=179183142192f6bbafe2a2df436b9837d4acf72d9f70120.244.237.58_561971482; acw_tc=6f84222417250438731364816e9ddaa97be442de1a23545ebe228fa0c7; cdn_sec_tc=6f84222417250438731364816e9ddaa97be442de1a23545ebe228fa0c7',
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
