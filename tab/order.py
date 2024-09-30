from datetime import datetime

import gradio as gr
import loguru
import pandas
import qrcode

from config import main_request


def order_tab():
    # Function to fetch data from API
    orders = []
    orders_dict = []
    orders_str = []

    def get_order_list():
        nonlocal orders, orders_dict, orders_str
        try:
            resp = main_request.get(url="https://www.allcpp.cn/api/tk/getList.do?type=0&sort=0&index=1&size=100").json()
            orders = resp["result"]["data"]
            loguru.logger.info(f"获取订单： {orders}")
            orders_dict = [
                {
                    "id": order["id"],
                    "eventName": order["eventName"],
                    "ticketName": order["ticketName"],
                    "createTime": datetime.utcfromtimestamp(order["createTime"] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                } for order in orders
            ]
            orders_str = [
                f'{order["eventName"]}- {order["ticketName"]}-{order["createTime"]}'
                for order in orders]
            df = pandas.DataFrame(orders)
            return [gr.update(value=df), gr.update(choices=orders_str)]
        except Exception as e:
            loguru.logger.exception(e)
            return [gr.update(), gr.update()]

    # Create Gradio app
    order_list_ui = gr.Dataframe(value=[], row_count=(2, "dynamic"))
    load_btn_ui = gr.Button("加载订单")

    with gr.Blocks() as order_pay:
        order_pay_ui = gr.Dropdown(label="选择付款的订单", interactive=True, type="index")
        buy_btn_ui = gr.Button("购买该票")
        log_ui = gr.JSON(label="打印日志")
        qr_image = gr.Image(label="使用微信扫码支付", elem_classes="pay_qrcode")

    def buy_order(order_idx):
        order = orders[order_idx]
        url = f"https://www.allcpp.cn/allcpp/ticket/buyTicketForOrder.do?orderid={order['id']}&ticketInfo=undefined,{order['ticketCount']},{order['price']}&paytype={order['payType']}"
        resp = main_request.post(url=url).json()
        loguru.logger.info(f"支付订单： {resp}")
        qr_gen = qrcode.QRCode()
        qr_gen.add_data(resp['result']['code'])
        qr_gen.make(fit=True)
        qr_gen_image = qr_gen.make_image()
        return [gr.update(value=resp), gr.update(value=qr_gen_image.get_image())]

    buy_btn_ui.click(fn=buy_order, inputs=order_pay_ui, outputs=[log_ui, qr_image])
    load_btn_ui.click(fn=get_order_list, inputs=None, outputs=[order_list_ui, order_pay_ui])
