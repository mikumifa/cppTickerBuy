import requests
from loguru import logger

from util.KVDatabase import KVDatabase


class CookieManager:
    def __init__(self, config_file_path):
        self.db = KVDatabase(config_file_path)

    @logger.catch
    def _login_and_save_cookies(
            self, login_url="https://cp.allcpp.cn/#/login/main"
    ):
        print("开始填写登录信息")
        phone = input("输入手机号：")
        password = input("输入密码：")
        login_url = "https://user.allcpp.cn/api/login/normal"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5,ja;q=0.4',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://cp.allcpp.cn',
            'priority': 'u=1, i',
            'referer': 'https://cp.allcpp.cn/',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
        }
        while True:
            payload = f"account={phone}&password={password}&phoneAccountBindToken=undefined&thirdAccountBindToken=undefined"
            response = requests.request("POST", login_url, headers=headers, data=payload)
            res_json = response.json()
            logger.info(f"登录响应体： {res_json}")
            if "token" in res_json:
                cookies_dict = response.cookies.get_dict()
                logger.info(f"cookies: {cookies_dict}")
                self.db.insert("cookie", cookies_dict)
                self.db.insert("password", password)
                self.db.insert("phone", phone)

                return response.cookies
            else:
                phone = input("输入手机号：")
                password = input("输入密码：")

    def refreshToken(self):
        login_url = "https://user.allcpp.cn/api/login/normal"
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5,ja;q=0.4',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'origin': 'https://cp.allcpp.cn',
            'priority': 'u=1, i',
            'referer': 'https://cp.allcpp.cn/',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0'
        }
        phone = self.db.get("phone")
        password = self.db.get("password")
        payload = f"account={phone}&password={password}&phoneAccountBindToken=undefined&thirdAccountBindToken=undefined"
        response = requests.request("POST", login_url, headers=headers, data=payload)
        res_json = response.json()
        logger.info(f"刷新登录响应体： {res_json}")
        if "token" in res_json:
            cookies_dict = response.cookies.get_dict()
            logger.info(f"cookies: {cookies_dict}")
            self.db.insert("cookie", cookies_dict)
            return cookies_dict

    def get_cookies(self, force=False):
        if force:
            return self.db.get("cookie")
        if not self.db.contains("cookie") or not self.db.contains("password") or not self.db.contains("phone"):
            return self._login_and_save_cookies()
        else:
            return self.db.get("cookie")

    def have_cookies(self):
        return self.db.contains("cookie") and self.db.contains("password") and self.db.contains("phone")

    def get_cookies_str(self):
        cookies = self.get_cookies()
        cookies_str = ""
        for key in cookies.keys():
            cookies_str += key + "=" + cookies[key] + "; "
        return cookies_str

    def get_cookies_value(self, name):
        cookies = self.get_cookies()
        for cookie in cookies:
            if cookie["name"] == name:
                return cookie["value"]
        return None

    def get_config_value(self, name, default=None):
        if self.db.contains(name):
            return self.db.get(name)
        else:
            return default

    def set_config_value(self, name, value):
        self.db.insert(name, value)

    def get_cookies_str_force(self):
        self._login_and_save_cookies()
        return self.get_cookies_str()
