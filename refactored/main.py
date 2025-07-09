#!/usr/bin/env python3
"""
Linux终端AI伴侣 - 重构版本（模块化架构）
"""

import argparse
import sys
from pathlib import Path

# 添加包路径到sys.path
sys.path.insert(0, str(Path(__file__).parent))

from ai_companion import AICompanion


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Linux终端AI伴侣 - 重构版本')
    
    # 基本功能
    parser.add_argument('--install', action='store_true', help='安装Shell钩子')
    parser.add_argument('--uninstall', action='store_true', help='卸载Shell钩子')
    parser.add_argument('--config', action='store_true', help='显示当前配置')
    parser.add_argument('--context', action='store_true', help='显示详细上下文信息')
    parser.add_argument('--test', action='store_true', help='测试API连接')
    
    # API配置
    parser.add_argument('--set-api', nargs='+', metavar='ARG',
                       help='设置API配置: --set-api TYPE URL MODEL KEY [NAME]')
    parser.add_argument('--switch-model', help='切换激活的API配置')
    parser.add_argument('--list-types', action='store_true', help='列出支持的AI服务类型')
    
    # 交互功能
    parser.add_argument('--ask', nargs='+', help='直接提问')
    parser.add_argument('--monitor', nargs='+', metavar='ARG',
                       help='监控命令执行结果（内部使用）: COMMAND EXIT_CODE [STDERR]')
    
    args = parser.parse_args()
    
    # 创建AI伴侣实例
    companion = AICompanion()
    
    try:
        if args.install:
            companion.install_shell_hooks()
            
        elif args.uninstall:
            companion.uninstall_shell_hooks()
            
        elif args.config:
            companion.show_config()
            
        elif args.context:
            companion.show_context_info()
            
        elif args.test:
            companion.test_api_connection()
            
        elif args.set_api:
            if len(args.set_api) < 4:
                print("❌ 参数不足。用法: --set-api TYPE URL MODEL KEY [NAME]")
                print("示例: --set-api openai https://api.openai.com/v1/chat/completions gpt-3.5-turbo YOUR_KEY")
                return
            
            api_type, base_url, model, api_key = args.set_api[:4]
            name = args.set_api[4] if len(args.set_api) > 4 else "default"
            
            companion.set_api_config(api_type, base_url, model, api_key, name)
            
        elif args.switch_model:
            companion.switch_api_service(args.switch_model)
            
        elif args.list_types:
            types = companion.get_supported_ai_types()
            print("支持的AI服务类型:")
            for ai_type in types:
                print(f"  - {ai_type}")
            
        elif args.monitor:
            if len(args.monitor) < 2:
                print("❌ monitor参数不足")
                return
            
            command = args.monitor[0]
            exit_code = int(args.monitor[1])
            stderr_content = args.monitor[2] if len(args.monitor) > 2 else ""
            
            companion.monitor_command(command, exit_code, stderr_content)
            
        elif args.ask:
            question = ' '.join(args.ask)
            response = companion.ask_question(question)
            
            print(f"🤖 \\033[1;36mAI伴侣回答\\033[0m")
            print(response)
            print(f"💡 \\033[2m输入 'ask \"更多问题\"' 可以继续咨询\\033[0m")
            
        else:
            # 显示帮助信息
            print("Linux终端AI伴侣 - 重构版本")
            print("\\n基本命令:")
            print("  --install           安装Shell钩子")
            print("  --uninstall         卸载Shell钩子")
            print("  --config            查看当前配置")
            print("  --context           查看详细上下文")
            print("  --test              测试API连接")
            print("\\nAPI配置:")
            print("  --set-api TYPE URL MODEL KEY [NAME]  设置API配置")
            print("  --switch-model NAME              切换API配置")
            print("  --list-types                     列出支持的AI类型")
            print("\\n交互功能:")
            print("  --ask '问题'         直接提问")
            print("\\n示例:")
            print("  python3 main.py --install")
            print("  python3 main.py --set-api openai https://api.openai.com/v1/chat/completions gpt-3.5-turbo YOUR_KEY")
            print("  python3 main.py --ask '如何查看系统内存？'")
            
    except KeyboardInterrupt:
        print("\\n👋 再见！")
    except Exception as e:
        print(f"❌ 出现错误: {e}")
        if "--debug" in sys.argv:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
