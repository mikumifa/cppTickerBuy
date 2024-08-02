import json
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import gradio as gr
from loguru import logger

from config import main_request, get_application_tmp_path

buyer_value = []
addr_value = []
ticket_value = []
project_name = []
ticket_str_list = []


def convert_timestamp_to_str(timestamp):
    return datetime.fromtimestamp(timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')


def filename_filter(filename):
    filename = re.sub('[\/:*?"<>|]', '', filename)
    return filename


def on_submit_ticket_id(num):
    global buyer_value
    global addr_value
    global ticket_value
    global project_name
    global ticket_str_list

    try:
        buyer_value = []
        addr_value = []
        ticket_value = []
        if "http" in num or "https" in num:
            num = extract_id_from_url(num)
            extracted_id_message = f"已提取URL票ID：{num}"
        else:
            return [
                gr.update(),
                gr.update(),
                gr.update(visible=False),
                gr.update(value='输入无效，请输入一个有效的网址。', visible=True),
            ]
        ret = main_request.get(
            url=f"https://www.allcpp.cn/allcpp/ticket/getTicketTypeList.do?eventMainId={num}"
        )
        ret = ret.json()
        logger.debug(ret)

        # 检查 errno
        if "ticketMain" not in ret:
            return [
                gr.update(),
                gr.update(),
                gr.update(visible=True),
                gr.update(value='输入无效，请输入一个有效的票。', visible=True),
            ]

        ticketMain = ret['ticketMain']
        ticketTypeList = ret["ticketTypeList"]
        project_name = ticketMain['eventName']
        ticket_str_list = [
            (f"{ticket['ticketName']} - 开始时间: {convert_timestamp_to_str(ticket['sellStartTime'])} - 截止时间: "
             f"{convert_timestamp_to_str(ticket['sellEndTime'])} - 描述: {ticket['ticketDescription']}")
            for ticket in ticketTypeList
        ]
        ticket_value = [
            ticket['id']
            for ticket in ticketTypeList
        ]
        buyer_value = main_request.get(
            url=f"https://www.allcpp.cn/allcpp/user/purchaser/getList.do"
        ).json()
        logger.debug(buyer_value)
        buyer_str_list = [
            f"{item['realname']}-{item['idcard']}-{item['mobile']}" for item in buyer_value
        ]

        return [
            gr.update(choices=ticket_str_list),
            gr.update(choices=buyer_str_list),
            gr.update(visible=True),
            gr.update(
                value=f"{extracted_id_message}\n"
                      f"获取票信息成功:\n"
                      f"活动名称：{ticketMain['eventName']}\n\n"
                      f"{ticketMain['description']}\n"
                      f"{ticketMain['eventDescription']}\n",
                visible=True,
            ),
        ]
    except Exception as e:
        return [
            gr.update(),
            gr.update(),
            gr.update(),
            gr.update(value=f"发生错误：{e}", visible=True),
        ]


def extract_id_from_url(url):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    return query_params.get('event', [None])[0]


def on_submit_all(ticket_id, ticket_info, people_indices):
    try:
        # if ticket_number != len(people_indices):
        #     return gr.update(
        #         value="生成配置文件失败，保证选票数目和购买人数目一致", visible=True
        #     )
        ticket_cur = ticket_value[ticket_info]
        people_cur = [buyer_value[item] for item in people_indices]
        ticket_id = extract_id_from_url(ticket_id)
        if ticket_id is None:
            return [gr.update(value="你所填不是网址，或者网址是错的", visible=True),
                    gr.update(value={}),
                    gr.update()]
        if len(people_indices) == 0:
            return [gr.update(value="至少选一个实名人", visible=True),
                    gr.update(value={}),
                    gr.update()]
        detail = f'{project_name}-{ticket_str_list[ticket_info]}'
        config_dir = {
            'detail': detail,
            'tickets': ticket_cur,
            'people_cur': people_cur
        }
        filename = os.path.join(get_application_tmp_path(), filename_filter(detail) + ".json")
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(config_dir, f, ensure_ascii=False, indent=4)
        return [gr.update(), gr.update(value=config_dir, visible=True), gr.update(value=filename, visible=True)]
    except Exception as e:
        return [gr.update(value="生成错误，仔细看看你可能有哪里漏填的", visible=True), gr.update(value={}),
                gr.update()]


def setting_tab():
    gr.Markdown("""
> **必看**
>
> 保证自己在抢票前，已经配置了购买人信息(就算不需要也要提前填写) 如果没填，生成表单时候不会出现任何选项
> - 购买人信息：https://cp.allcpp.cn/ticket/prePurchaser
""")
    info_ui = gr.TextArea(
        info="此窗口为输出信息", label="输出信息", interactive=False, visible=False
    )
    with gr.Column():
        ticket_id_ui = gr.Textbox(
            label="想要抢票的网址",
            interactive=True,
            info="例如：https://www.allcpp.cn/allcpp/event/event.do?event=3163",
        )
        ticket_id_btn = gr.Button("获取票信息")
        with gr.Column(visible=False) as inner:
            with gr.Row():
                people_ui = gr.CheckboxGroup(
                    label="身份证实名认证",
                    interactive=True,
                    type="index",
                    info="必填，选几个就代表买几个人的票，在 https://cp.allcpp.cn/ticket/prePurchaser 中添加",
                )
                ticket_info_ui = gr.Dropdown(
                    label="选票",
                    interactive=True,
                    type="index",
                    info="必填，请仔细核对起售时间，千万别选错其他时间点的票",
                )

            config_btn = gr.Button("生成配置")
            config_file_ui = gr.File(visible=False)
            config_output_ui = gr.JSON(
                label="生成配置文件（右上角复制）",
                visible=False,
            )
            config_btn.click(
                fn=on_submit_all,
                inputs=[
                    ticket_id_ui,
                    ticket_info_ui,
                    people_ui
                ],
                outputs=[info_ui, config_output_ui, config_file_ui]
            )

        ticket_id_btn.click(
            fn=on_submit_ticket_id,
            inputs=ticket_id_ui,
            outputs=[
                ticket_info_ui,
                people_ui,
                inner,
                info_ui,
            ],
        )
