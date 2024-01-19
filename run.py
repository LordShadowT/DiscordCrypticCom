from threading import Thread
import os


def run_app():
    os.system('python3 app.py')


if __name__ == '__main__':
    Thread(target=run_app).start()
    os.system('python3 mc_class.py')
