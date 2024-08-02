import hashlib
import json
import os
import secrets
import string
import threading
import time
from datetime import datetime
from json import JSONDecodeError
from urllib.parse import quote

import gradio as gr
import qrcode
import retry
from gradio import SelectData
from loguru import logger
from playsound import playsound
from requests import HTTPError, RequestException

from config import global_cookieManager, main_request, configDB, time_service
from util import PlusUtil
from util.error import ERRNO_DICT, withTimeString


def format_dictionary_to_string(data):
    formatted_string_parts = []
    for key, value in data.items():
        if isinstance(value, list) or isinstance(value, dict):
            formatted_string_parts.append(
                f"{quote(key)}={quote(json.dumps(value, separators=(',', ':'), ensure_ascii=False))}"
            )
        else:
            formatted_string_parts.append(f"{quote(key)}={quote(str(value))}")

    formatted_string = "&".join(formatted_string_parts)
    return formatted_string


def go_tab():
    isRunning = False

    gr.Markdown("""""")
    with gr.Column():
        gr.Markdown(
            """
            ### 上传或填入你要抢票票种的配置信息
            """
        )
        with gr.Row(equal_height=True):
            upload_ui = gr.Files(label="上传多个配置文件，点击不同的配置文件可快速切换", file_count="multiple")
            ticket_ui = gr.TextArea(
                label="填入配置",
                info="再次填入配置信息 （不同版本的配置文件可能存在差异，升级版本时候不要偷懒，老版本的配置文件在新版本上可能出问题",
                interactive=True
            )
        gr.HTML(
            """<label for="datetime">选择抢票的时间</label><br>
                <input type="datetime-local" id="datetime" name="datetime" step="1">""",
            label="选择抢票的时间",
            show_label=True,
        )

        def upload(filepath):
            try:
                with open(filepath[0], 'r', encoding="utf-8") as file:
                    content = file.read()
                return content
            except Exception as e:
                return str(e)

        def file_select_handler(select_data: SelectData, files):
            file_label = files[select_data.index]
            try:
                with open(file_label, 'r', encoding="utf-8") as file:
                    content = file.read()
                return content
            except Exception as e:
                return str(e)

        upload_ui.upload(fn=upload, inputs=upload_ui, outputs=ticket_ui)
        upload_ui.select(file_select_handler, upload_ui, ticket_ui)

        # 手动设置/更新时间偏差
        with gr.Accordion(label='手动设置/更新时间偏差', open=False):
            time_diff_ui = gr.Number(label="当前脚本时间偏差 (单位: ms)",
                                     info="你可以在这里手动输入时间偏差, 或点击下面按钮自动更新当前时间偏差。正值将推迟相应时间开始抢票, 负值将提前相应时间开始抢票。",
                                     value=format(time_service.get_timeoffset() * 1000, '.2f'))
            refresh_time_ui = gr.Button(value="点击自动更新时间偏差")
            refresh_time_ui.click(fn=lambda: format(float(time_service.compute_timeoffset()) * 1000, '.2f'),
                                  inputs=None, outputs=time_diff_ui)
            time_diff_ui.change(fn=lambda x: time_service.set_timeoffset(format(float(x) / 1000, '.5f')),
                                inputs=time_diff_ui, outputs=None)

        with gr.Accordion(label='配置抢票成功声音提醒[可选]', open=False):
            with gr.Row():
                audio_path_ui = gr.Audio(
                    label="上传提示声音", type="filepath")

        def input_phone(_phone):
            global_cookieManager.set_config_value("phone", _phone)

        with gr.Row():

            interval_ui = gr.Number(
                label="抢票间隔",
                value=300,
                minimum=1,
                info="设置抢票任务之间的时间间隔（单位：毫秒），建议不要设置太小",
            )
            mode_ui = gr.Radio(
                label="抢票模式",
                choices=["无限", "有限"],
                value="无限",
                info="选择抢票的模式",
                type="index",
                interactive=True,
            )
            total_attempts_ui = gr.Number(
                label="总过次数",
                value=100,
                minimum=1,
                info="设置抢票的总次数",
                visible=False,
            )

    validate_con = threading.Condition()

    def start_go(tickets_info_str, time_start, interval, mode,
                 total_attempts, audio_path):
        nonlocal isRunning
        isRunning = True
        left_time = total_attempts
        yield [
            gr.update(value=withTimeString("详细信息见控制台"), visible=True),
            gr.update(visible=True),
            gr.update(),
        ]
        while isRunning:
            try:
                if time_start != "":
                    logger.info("0) 等待开始时间")
                    timeoffset = time_service.get_timeoffset()
                    logger.info("时间偏差已被设置为: " + str(timeoffset) + 's')
                    while isRunning:
                        try:
                            time_difference = (
                                    datetime.strptime(time_start, "%Y-%m-%dT%H:%M:%S").timestamp()
                                    - time.time() + timeoffset
                            )
                        except ValueError as e:
                            time_difference = (
                                    datetime.strptime(time_start, "%Y-%m-%dT%H:%M").timestamp()
                                    - time.time() + timeoffset
                            )
                        if time_difference > 0:
                            if time_difference > 5:
                                yield [
                                    gr.update(value="等待中，剩余等待时间: " + (str(int(
                                        time_difference)) + '秒') if time_difference > 6 else '即将开抢',
                                              visible=True),
                                    gr.update(visible=True),
                                    gr.update()
                                ]
                                time.sleep(1)
                            else:
                                # 准备倒计时开票, 不再渲染页面, 确保计时准确
                                # 使用 time.perf_counter() 方法实现高精度计时, 但可能会占用一定的CPU资源
                                start_time = time.perf_counter()
                                end_time = start_time + time_difference
                                current_time = start_time
                                while current_time < end_time:
                                    current_time = time.perf_counter()
                                break
                            if not isRunning:
                                # 停止定时抢票
                                yield [
                                    gr.update(value='手动停止定时抢票', visible=True),
                                    gr.update(visible=True),
                                    gr.update(),
                                ]
                                logger.info("手动停止定时抢票")
                                return
                        else:
                            break
                if not isRunning:
                    gr.update(value="停止", visible=True),
                    return

                # 数据准备
                tickets_info = json.loads(tickets_info_str)
                people_cur = tickets_info["people_cur"]
                ticket_id = tickets_info["tickets"]
                _request = main_request
                # 订单准备
                logger.info(f"1）发起抢票请求")

                @retry.retry(exceptions=RequestException, tries=60, delay=interval / 1000)
                def inner_request():
                    if not isRunning:
                        raise ValueError("抢票结束")

                    timestamp = int(time.time())
                    n = string.ascii_letters + string.digits
                    nonce = ''.join(secrets.choice(n) for i in range(32))
                    sign = hashlib.md5(f"2x052A0A1u222{timestamp}{nonce}{ticket_id}2sFRs".encode('utf-8')).hexdigest()

                    ret = _request.post(
                        url=f"https://www.allcpp.cn/allcpp/ticket/buyTicketWeixin.do?ticketTypeId={ticket_id}"
                            f"&count={len(people_cur)}&nonce={nonce}&timeStamp={timestamp}&sign={sign}&payType=0&"
                            f"purchaserIds={','.join([str(p['id']) for p in people_cur])}",
                    ).json()
                    err = ret["isSuccess"]
                    logger.info(
                        f'状态码: {err}({ERRNO_DICT.get(err, "未知错误码")}), 请求体: {ret}'
                    )
                    if not ret["isSuccess"]:
                        raise HTTPError("重试次数过多，重新准备订单")
                    return ret, err

                request_result, errno = inner_request()
                left_time_str = "无限" if mode == 0 else left_time
                logger.info(
                    f'状态码: {errno}({ERRNO_DICT.get(errno, "未知错误码")}), 请求体: {request_result} 剩余次数: {left_time_str}'
                )
                yield [
                    gr.update(
                        value=withTimeString(
                            f"正在抢票，具体情况查看终端控制台。\n剩余次数: {left_time_str}\n当前状态码: {errno} ({ERRNO_DICT.get(errno, '未知错误码')})"),
                        visible=True,
                    ),
                    gr.update(visible=True),
                    gr.update()]
                if errno:
                    logger.info(f"2）扫码支付")
                    qr_gen = qrcode.QRCode()
                    qr_gen.add_data(request_result['result']['code'])
                    qr_gen.make(fit=True)
                    qr_gen_image = qr_gen.make_image()
                    yield [
                        gr.update(value=withTimeString("生成付款二维码"), visible=True),
                        gr.update(visible=False),
                        gr.update(value=qr_gen_image.get_image(), visible=True)
                    ]
                    plusToken = configDB.get("plusToken")
                    if plusToken is not None and plusToken != "":
                        PlusUtil.send_message(plusToken, "抢票成功", "付款吧")
                    if audio_path is not None and audio_path != "":
                        def play_sound_in_loop(file_path):
                            while True:
                                try:
                                    playsound(file_path)
                                except Exception as e:
                                    logger.info(f"播放音乐失败: {e}")
                                time.sleep(1)

                        yield [
                            gr.update(value="开始放歌, 暂未实现关闭音乐功能，想关闭音乐请重启程序", visible=True),
                            gr.update(visible=False),
                            gr.update()
                        ]
                        play_sound_in_loop(os.path.normpath(audio_path))

                    break
                if mode == 1:
                    left_time -= 1
                    if left_time <= 0:
                        break
            except JSONDecodeError as e:
                logger.error(f"配置文件格式错误: {e}")
                return [
                    gr.update(value=withTimeString("配置文件格式错误"), visible=True),
                    gr.update(visible=True),
                    gr.update()
                ]
            except ValueError as e:
                logger.info(f"{e}")
                yield [
                    gr.update(value=withTimeString(f"有错误，具体查看控制台日志\n\n当前错误 {e}"), visible=True),
                    gr.update(visible=True),
                    gr.update()
                ]
            except HTTPError as e:
                logger.error(f"请求错误: {e}")
                yield [
                    gr.update(value=withTimeString(f"有错误，具体查看控制台日志\n\n当前错误 {e}"), visible=True),
                    gr.update(visible=True),
                    gr.update()

                ]
            except Exception as e:
                logger.exception(e)
                yield [
                    gr.update(value=withTimeString(f"有错误，具体查看控制台日志\n\n当前错误 {e}"), visible=True),
                    gr.update(visible=True),
                    gr.update()
                ]
            finally:
                time.sleep(interval / 1000.0)

        yield [
            gr.update(value="抢票结束", visible=True),
            gr.update(visible=False),  # 当设置play_sound_process,应该有提示声音
            gr.update()
        ]

    mode_ui.change(
        fn=lambda x: gr.update(visible=True)
        if x == 1
        else gr.update(visible=False),
        inputs=[mode_ui],
        outputs=total_attempts_ui,
    )
    with gr.Row():
        go_btn = gr.Button("开始抢票")
        stop_btn = gr.Button("停止", visible=False)

    with gr.Row():
        go_ui = gr.Textbox(
            info="此窗口为临时输出，具体请见控制台",
            label="输出信息",
            interactive=False,
            visible=False,
            show_copy_button=True,
            max_lines=10,

        )
        qr_image = gr.Image(label="使用微信扫码支付", visible=False, elem_classes="pay_qrcode")

    time_tmp = gr.Textbox(visible=False)

    go_btn.click(
        fn=None,
        inputs=None,
        outputs=time_tmp,
        js='(x) => document.getElementById("datetime").value',
    )

    def stop():
        nonlocal isRunning
        isRunning = False

    go_btn.click(
        fn=start_go,
        inputs=[ticket_ui, time_tmp, interval_ui, mode_ui,
                total_attempts_ui, audio_path_ui],
        outputs=[go_ui, stop_btn, qr_image],
    )
    stop_btn.click(
        fn=stop,
        inputs=None,
        outputs=None,
    )
