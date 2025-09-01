import gradio as gr
from loguru import logger

from config import main_request, configDB, global_cookieManager
from util.KVDatabase import KVDatabase

names = []


@logger.catch
def login_tab():
    gr.Markdown("""
> **补充**
>
> 在这里，你可以
> 1. 去更改账号，
> 2. 查看当前程序正在使用哪个账号
> 3. 使用配置文件切换到另一个账号
>
""")
    with gr.Row():
        username_ui = gr.Text(
            main_request.get_request_name(),
            label="账号名称",
            interactive=False,
            info="当前账号的名称",
        )
        gr_file_ui = gr.File(label="当前登录信息文件",
                             value=configDB.get("cookie_path"))
    gr.Markdown("""🏵️ 登录
    
    > 请不要一个程序打开多次
    > 如果这些程序都是同一个文件打开的，当你修改其中这个程序的账号时候，也会影响其他程序""")
    info_ui = gr.TextArea(
        info="此窗口为输出信息", label="输出信息", interactive=False
    )
    with gr.Row():
        upload_ui = gr.UploadButton(label="导入配置文件")

        def upload_file(filepath):
            main_request.cookieManager.reset()
            yield ["已经注销，请选择登录信息文件", gr.update(), gr.update()]
            try:
                configDB.insert("cookie_path", filepath)
                global_cookieManager.db = KVDatabase(filepath)
                name = main_request.get_request_name()
                yield [gr.update(value="导入成功"), gr.update(value=name), gr.update(value=configDB.get("cookie_path"))]
            except Exception:
                name = main_request.get_request_name()
                yield ["登录出现错误", gr.update(value=name), gr.update(value=configDB.get("cookie_path"))]

        upload_ui.upload(upload_file, [upload_ui], [info_ui, username_ui, gr_file_ui])

    with gr.Row():
        user_input = gr.Textbox(label="用户名")
        pass_input = gr.Textbox(label="密码", type="password")
        login_btn = gr.Button("使用账号密码登录")
        logout_btn = gr.Button("注销登录")

        def login(username, password):
            main_request.cookieManager.reset()
            yield ["已经注销，请重新登录", gr.update(value="未登录"), gr.update(value=configDB.get("cookie_path"))]
            try:
                main_request.cookieManager.login_by_phone_passwd(username, password)
                name = main_request.get_request_name()
                if name == '未登录':
                    yield ["登录失败，请检查账号密码", gr.update(value="未登录"), gr.update(value=configDB.get("cookie_path"))]
                else:
                    yield [gr.update(value="登录成功"), gr.update(value=name), gr.update(value=configDB.get("cookie_path"))]
            except Exception:
                name = main_request.get_request_name()
                yield ["登录出现错误", gr.update(value=name), gr.update(value=configDB.get("cookie_path"))]
        def logout():
            main_request.cookieManager.reset()
            yield ["已经注销，重新登录", gr.update(value="未登录"), gr.update(value=configDB.get("cookie_path"))]
        login_btn.click(
            fn=login,
            inputs=[user_input, pass_input],
            outputs=[info_ui, username_ui, gr_file_ui]
        )
        logout_btn.click(
            fn=logout,
            inputs=None,
            outputs=[info_ui, username_ui, gr_file_ui]
        )
    gr.Markdown(
        """
        🗨️ 抢票成功提醒
        > 你需要去对应的网站获取key或token，然后填入下面的输入框  
        > [Server酱](https://sct.ftqq.com/sendkey) | [pushplus](https://www.pushplus.plus/uc.html)  
        > 留空以不启用提醒功能  
        """)
    with gr.Row():
        serverchan_ui = gr.Textbox(
            value=configDB.get("serverchanKey") if configDB.get("serverchanKey") is not None else "",
            label="Server酱的SendKey",
            interactive=True,
            info="https://sct.ftqq.com/",
        )

        pushplus_ui = gr.Textbox(
            value=configDB.get("pushplusToken") if configDB.get("pushplusToken") is not None else "",
            label="PushPlus的Token",
            interactive=True,
            info="https://www.pushplus.plus/",
        )

        def inner_input_serverchan(x):
            return configDB.insert("serverchanKey", x)        
        def inner_input_pushplus(x):
            return configDB.insert("pushplusToken", x)

        serverchan_ui.change(fn=inner_input_serverchan, inputs=serverchan_ui)

        pushplus_ui.change(fn=inner_input_pushplus, inputs=pushplus_ui)
