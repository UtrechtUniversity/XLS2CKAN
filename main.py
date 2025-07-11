import globals
import tui
import logging, os
import datetime

def main():
    UI = tui.UI()

if __name__ == '__main__':

    old_log = 'none'
    if not os.path.exists(globals.LOG_FOLDER):
        os.makedirs(globals.LOG_FOLDER)
    else:
        if os.path.exists(globals.LOG_FILE):
            new_extension = '.' + str(datetime.datetime.now().strftime("%I_%M%p_%d%m%y"))
            old_log = globals.LOG_FILE + new_extension
            os.rename(globals.LOG_FILE, old_log)


    # create higher level logger
    stream_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(globals.LOG_FILE)
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            file_handler,
                            stream_handler
                        ])
    log = logging.getLogger(__name__)

    stream_handler.setLevel(logging.INFO)
    file_handler.setLevel(logging.DEBUG)

    log.debug('Former log file: ' + old_log)

    main()

