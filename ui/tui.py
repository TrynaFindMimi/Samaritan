import sys
import time


class SamaritanTUI:
    def __init__(self):
        self.black = '\033[40m'
        self.white_bone = '\033[97m'
        self.red = '\033[91m'
        self.reset = '\033[0m'
        self.bold = '\033[1m'

    def clear(self):
        print('\033[2J\033[H', end='')

    def print_text(self, text: str, word_by_word: bool = True, delay: float = 0.03):
        if word_by_word:
            words = text.split()
            for i, word in enumerate(words):
                print(f"{self.white_bone}{word}{self.reset}", end=' ')
                sys.stdout.flush()
                time.sleep(delay)
            print()
        else:
            print(f"{self.white_bone}{text}{self.reset}")

    def print_alert(self, text: str):
        print(f"{self.red}{self.bold}{text}{self.reset}")

    def indicator(self):
        return f"{self.white_bone}►{self.reset}"

    def show(self, text: str):
        self.clear()
        print(f"{self.black}", end='')
        self.print_text(text)
        print(f"{self.reset}", end='')


def main():
    tui = SamaritanTUI()
    tui.show("ANALYZING\nSISTEMA INICIALIZADO\nCOMPLETE")


if __name__ == '__main__':
    main()
