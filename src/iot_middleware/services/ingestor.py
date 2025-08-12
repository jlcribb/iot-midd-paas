import time


def run(config_path: str|None=None)->None:
    print("Ingestor placeholder en ejecución", config_path)
    while True:
        time.sleep(5)


if __name__=="__main__":
    run()
