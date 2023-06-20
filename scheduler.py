import os
import sys
import time
import schedule
import glob
import threading
import subprocess
import json

from log import log
from time import strftime, gmtime


task_list = []
task_dir = 'taskList'
# 获取 task 文件夹下所有的 Python 脚本文件
def load_task(task_dir):
    global task_list
    task_list = []
    tasks = glob.glob(os.path.join(task_dir, "*.py"))
    # 遍历每一个 Python 脚本文件，按照文件名规则分类并保存
    for task in tasks:
        try:
            filename = os.path.basename(task)
            task_name, run_time = filename.split(".")[0].split("&")
            run_time = run_time[:2]+":"+run_time[2:]
            task_list.append({
                "task_name":task_name,
                "run_time":run_time,
                "filename":task_dir+"/"+filename,
            })
        except:
            print("注册文件{}时出错".format(filename))
            
def run_task(task):
    filename = task['filename']
    task_name = task['task_name']
    log("开始执行",task_name=task_name)
    status = '0'
    # try:
    #     result = subprocess.run(['python', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    #     output_str = result.stdout.decode().strip().split("\r")[-1].replace("\n","").replace("\'","\"")
    #     task_result = json.loads(output_str)
    #     status = task_result['status']
    #     msg = task_result['msg']
    #     # 记录任务结束消息到日志文件
    #     log(task_name=task_name, result=status, msg=msg)
    # except Exception as e:
    #     exc_type, exc_value, exc_traceback = sys.exc_info()
    #     log(task_name=task_name, msg=f"任务中断：{exc_type.__name__}")
    result = subprocess.run(['python', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_str = result.stdout.decode().strip().split("|")[-1].replace("\'","\"")
    task_result = json.loads(output_str)
    status = task_result['status']
    msg = task_result['msg']
    # 记录任务结束消息到日志文件
    log(task_name=task_name, result=status, msg=msg)

    
    if status == '1':
        #如果运行成功，则清除掉重试任务
        schedule.clear(task_name+"_retry")
    elif status == '0':
        # 如果任务执行失败，则1分钟后再次执行
        log(task_name=task_name, msg="运行失败，将在一分钟后重试")
        schedule.clear(task_name+"_retry")
        schedule.every(1).minutes.do(run_task, task).tag(task_name+"_retry")

def schedule_load(task_list):
    for task in task_list:
        run_time = task['run_time']
        schedule.every().day.at(run_time).do(run_task, task).tag(task['task_name'])
    log("任务载入完成，开始运行")

def schedule_run():
    while True:
        schedule.run_pending()
        time.sleep(1)

def CLI():
    print("调度控制台已加载，请输指示：")
    while True:
        cmd = sys.stdin.readline().strip()
        if cmd == 'tasks':
            print(" ∟任务列表：")
            for job in schedule.jobs:
                next_run = strftime("%H小时%M分钟%S秒", gmtime(job.scheduler.idle_seconds))
                print(f"   ∟任务：{str(job.tags)[2:-2]}，\t\t运行时间：{job.at_time}")
            print(f"   下一次任务将于{next_run}后执行")
        elif cmd == 'exit':
            print(" ∟程序终止")
            os._exit(0)
        elif cmd == 'reload':
            schedule.clear()
            load_task(task_dir)
            schedule_load(task_list)
            print(" ∟已重新加载任务")
        elif cmd == 'clear':
            schedule.clear()
            print(" ∟已清空所有任务")
        elif cmd == 'run all':
            print(" ∟执行所有任务...")
            schedule.run_all()
            print(" ∟执行完成")
        else:
            print("未知的命令")

if __name__ == '__main__':
    load_task(task_dir=task_dir)
    schedule_load(task_list)

    # 启动命令行输入线程
    t1 = threading.Thread(target=schedule_run)
    t1.start()
    t2 = threading.Thread(target=CLI)
    t2.start()

    # 等待线程结束
    t1.join()
    t2.join()

