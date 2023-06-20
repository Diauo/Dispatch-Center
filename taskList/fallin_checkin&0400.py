import httpx
import asyncio
import json
import sys

task_result = "初始化"

async def login():
    print("----登录...")
    global task_result
    # 登录的 URL
    login_url = 'https://fallin.app/auth/login'
    # Cookie
    cookie = {}
    # 登录表单数据
    login_data = {'email': '*********@qq.com', 'passwd': '***********', 'code': ''}
    # 发送登录请求
    async with httpx.AsyncClient() as client:
        response = await client.post(login_url, data=login_data, timeout=30)
    result = json.load(response)
    print("----登录请求已经发送")
    # 检查登录是否成功
    if response.status_code == 200 and result['ret'] == 1:
        # 提取 Cookie
        print("----登录成功")
        cookie = response.cookies
        await checkin(cookie=cookie)
    else:
        print("----登录失败")
        task_result = {"status":"0", "msg":"登录失败：".format(result['msg'])}

async def checkin(cookie):
    print("----开始签到")
    global task_result
    # 签到的 URL
    checkin_url = 'https://fallin.app/user/checkin'
    # 发送签到请求
    async with httpx.AsyncClient() as client:
        response = await client.post(checkin_url, cookies=cookie, timeout=30)
    result = json.load(response)
    if response.status_code == 200:
        result = json.load(response)
        if result['ret'] == 1:
            task_result = {"status":"1", "msg":"签到成功：{} 剩余流量{}"
                                .format(result['msg'], result['trafficInfo']['unUsedTraffic'])}
        elif "签到过" in result['msg']:
            task_result = {"status":"1", "msg":"签到失败：{}".format(result['msg'])}
        else:
            task_result = {"status":"0", "msg":"签到失败：{}".format(result['msg'])}
        
    else:
        task_result = {"status":"0", "msg":"签到失败：{}".format(response.status_code)}

if __name__ == '__main__':
    try:
        print("----执行fallin_checkin")
        asyncio.run(login())
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        task_result = {"status":"0", "msg":"任务运行失败：{}".format(exc_type.__name__)}
    finally:
        print("|"+task_result)
        exit()

    