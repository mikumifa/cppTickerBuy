import requests

from util.CookieManager import CookieManager


class CppRequest:
    def __init__(self, headers=None, cookies_config_path=""):
        self.session = requests.Session()
        self.cookieManager = CookieManager(cookies_config_path)
        self.headers = headers or {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5,ja;q=0.4',
            'cookie': "",
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

    def get(self, url, data=None):
        self.headers["cookie"] = self.cookieManager.get_cookies_str()
        response = self.session.get(url, data=data, headers=self.headers)
        response.raise_for_status()
        return response

    def post(self, url, data=None):
        self.headers["cookie"] = self.cookieManager.get_cookies_str()
        response = self.session.post(url, data=data, headers=self.headers)
        response.raise_for_status()
        return response

    def get_request_name(self):
        try:
            if not self.cookieManager.have_cookies():
                return "未登录"
            result = self.get("https://www.allcpp.cn/allcpp/circle/getCircleMannage.do").json()
            return result["result"]["joinCircleList"][0]["nickname"]
        except Exception as e:
            return "未登录"

    def refreshToken(self):
        self.cookieManager.refreshToken()


if __name__ == "__main__":
    test_request = CppRequest(cookies_config_path="cookies.json")
    res = test_request.get("https://www.allcpp.cn/api/tk/getList.do?type=1&sort=0&index=1&size=10")
    print(res.headers)
    print(res.text)
