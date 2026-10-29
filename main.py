#!/usr/bin/env python3
import sys
import argparse
from utils import load_config, check_ram_before


def cmd_build_data(args):
    from data.dataset import build_datasets
    check_ram_before("build_data")
    train, eval = build_datasets()
    print(f"OK: {train}, {eval}")


def cmd_train_sft(args):
    from model.train import train_sft
    check_ram_before("train_sft")
    train_sft()
    print("OK: SFT completado. Adaptador guardado en model/lora_adapter/")


def cmd_create_model(args):
    from serving.ollama_client import create_model
    import os
    modelfile = os.path.join(os.path.dirname(__file__), 'serving', 'Modelfile')
    ok = create_model('samaritan', modelfile)
    print(f"create_model: {ok}")


def cmd_build_dpo(args):
    from judge.dpo_builder import build_dpo_dataset
    check_ram_before("build_dpo_dataset")
    dpo = build_dpo_dataset()
    print(f"OK: {dpo}")


def cmd_train_dpo(args):
    from model.train import train_dpo
    check_ram_before("train_dpo")
    train_dpo()
    print("OK: DPO completado. Adaptador guardado en model/lora_adapter/")


def cmd_eval(args):
    from eval import run_eval
    run_eval()


def cmd_query(args):
    from agent.agent import SamaritanAgent
    from output.filter import filter_output
    from ui.tui import SamaritanTUI

    question = args.question
    if not question:
        print("Error: debes proporcionar una pregunta")
        print("Uso: python main.py query \"tu pregunta aquí\"")
        sys.exit(1)

    agent = SamaritanAgent()
    tui = SamaritanTUI()
    resp = agent.process(question)
    filtered = filter_output(resp)
    tui.respond(filtered)


def cmd_ask(args):
    from serving.ollama_client import generate
    from output.filter import filter_output
    from ui.tui import SamaritanTUI

    question = args.question
    if not question:
        print("Error: debes proporcionar una pregunta")
        print("Uso: python main.py ask \"tu pregunta aquí\"")
        sys.exit(1)

    tui = SamaritanTUI()
    resp = generate([{"role": "user", "content": question}], model="samaritan")
    filtered = filter_output(resp)
    tui.respond(filtered)


def main():
    if len(sys.argv) == 1:
        from agent.agent import SamaritanAgent
        from output.filter import filter_output
        from ui.tui import SamaritanTUI

        tui = SamaritanTUI()
        tui.boot()
        agent = SamaritanAgent()
        while True:
            try:
                user_input = input(f"{tui.prompt()}").strip()
                if not user_input:
                    continue
                if user_input.lower() in ['exit', 'salir', 'quit', 'q']:
                    print(f"{tui.bright_cyan}>{tui.reset} {tui.bone}TERMINATING{tui.reset}")
                    print(f"{tui.bright_green}COMPLETE{tui.reset}")
                    tui.cursor_show()
                    break
                resp = agent.process(user_input)
                filtered = filter_output(resp)
                tui.respond(filtered)
                sys.stdout.flush()
            except EOFError:
                tui.cursor_show()
                break
            except KeyboardInterrupt:
                print()
                print(f"{tui.bright_cyan}>{tui.reset} {tui.bone}SESSION INTERRUPTED{tui.reset}")
                print(f"{tui.bright_green}COMPLETE{tui.reset}")
                tui.cursor_show()
                break
            except Exception as e:
                err = f"ANOMALY DETECTED\nERROR: {e}\nCOMPLETE"
                filtered_err = filter_output(err)
                tui.respond(filtered_err)
                sys.stdout.flush()
        return

    parser = argparse.ArgumentParser(description='SAMARITAN')
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('build-data')
    sub.add_parser('train-sft')
    sub.add_parser('create-model')
    sub.add_parser('build-dpo')
    sub.add_parser('train-dpo')
    sub.add_parser('eval')

    query_parser = sub.add_parser('query')
    query_parser.add_argument('question', nargs='?')

    ask_parser = sub.add_parser('ask')
    ask_parser.add_argument('question', nargs='?')

    args = parser.parse_args()
    if args.command == 'build-data':
        cmd_build_data(args)
    elif args.command == 'train-sft':
        cmd_train_sft(args)
    elif args.command == 'create-model':
        cmd_create_model(args)
    elif args.command == 'build-dpo':
        cmd_build_dpo(args)
    elif args.command == 'train-dpo':
        cmd_train_dpo(args)
    elif args.command == 'eval':
        cmd_eval(args)
    elif args.command == 'query':
        cmd_query(args)
    elif args.command == 'ask':
        cmd_ask(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
