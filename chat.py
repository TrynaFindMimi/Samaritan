#!/usr/bin/env python3
from agent.agent import SamaritanAgent
from output.filter import filter_output

def main():
    print("Hola soy samaritan")
    agent = SamaritanAgent()
    while True:
        try:
            user_input = input("> ")
            if not user_input.strip():
                continue
            if user_input.strip().lower() in ['exit', 'salir', 'quit']:
                break
            resp = agent.process(user_input)
            filtered = filter_output(resp)
            print(filtered)
            print()
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"ANOMALY DETECTED\n{e}\nCOMPLETE")
            print()

if __name__ == '__main__':
    main()
