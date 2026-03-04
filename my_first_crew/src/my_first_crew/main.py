#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from my_first_crew.crew import MyFirstCrew

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run():
    """
    Run the crew with interactive topic input.
    """
    # 获取用户输入的话题
    print("\n" + "="*60)
    print("[AI] 多智能体协同系统 - 研究助手")
    print("="*60)
    
    # 方式1：从命令行参数获取（如果有）
    if len(sys.argv) > 1:
        topic = sys.argv[1]
        print(f"[参数] 使用命令行参数话题: {topic}")
    else:
        # 方式2：交互式输入
        topic = input("[输入] 请输入研究话题: ").strip()
        if not topic:
            topic = "AI LLMs"  # 默认值
            print(f"[默认] 使用默认话题: {topic}")
    
    inputs = {
        'topic': topic,
        'current_year': str(datetime.now().year)
    }
    
    print(f"\n[配置信息]")
    print(f"   - 话题: {inputs['topic']}")
    print(f"   - 年份: {inputs['current_year']}")
    print("-"*60)
    
    try:
        # 执行智能体团队
        result = MyFirstCrew().crew().kickoff(inputs=inputs)
        
        print("\n" + "="*60)
        print("[完成] 任务执行完成!")
        print("="*60)
        
        # 如果有结果，显示摘要
        if result:
            print("\n[结果摘要]")
            print(result)
        
        return result
        
    except Exception as e:
        print(f"\n[错误] {e}")
        raise Exception(f"An error occurred while running the crew: {e}")

def train():
    """
    Train the crew for a given number of iterations.
    """
    if len(sys.argv) < 3:
        print("[用法] crewai train <迭代次数> <文件名>")
        return
        
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    
    print(f"\n开始训练 {sys.argv[1]} 次...")
    
    try:
        MyFirstCrew().crew().train(
            n_iterations=int(sys.argv[1]), 
            filename=sys.argv[2], 
            inputs=inputs
        )
        print("[完成] 训练完成!")
        
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    if len(sys.argv) < 2:
        print("[用法] crewai replay <任务ID>")
        return
        
    try:
        MyFirstCrew().crew().replay(task_id=sys.argv[1])
        print("[完成] 重放完成!")
        
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    if len(sys.argv) < 3:
        print("[用法] crewai test <迭代次数> <评估LLM>")
        return
        
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    
    print(f"\n开始测试，迭代次数: {sys.argv[1]}...")
    
    try:
        MyFirstCrew().crew().test(
            n_iterations=int(sys.argv[1]), 
            eval_llm=sys.argv[2], 
            inputs=inputs
        )
        print("[完成] 测试完成!")
        
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")

def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("请提供JSON格式的触发参数")

    try:
        trigger_payload = json.loads(sys.argv[1])
        print(f"[触发] 收到触发参数: {trigger_payload}")
        
    except json.JSONDecodeError:
        raise Exception("无效的JSON格式参数")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "topic": trigger_payload.get('topic', 'AI LLMs'),
        "current_year": str(datetime.now().year)
    }

    try:
        result = MyFirstCrew().crew().kickoff(inputs=inputs)
        print("[完成] 触发执行完成!")
        return result
        
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")

# 简单的命令行入口
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["train", "replay", "test", "run_with_trigger"]:
        # 根据第一个参数调用对应函数
        command = sys.argv[1]
        if command == "train":
            train()
        elif command == "replay":
            replay()
        elif command == "test":
            test()
        elif command == "run_with_trigger":
            run_with_trigger()
    else:
        # 默认运行主函数
        run()