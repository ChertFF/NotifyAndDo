import logging
from time import strftime, gmtime

time = strftime("%m.%d.%Y_%H.%M.%S", gmtime())
filename = f'out/logs_{time}.log'
logging.basicConfig(format=u'[%(asctime)s] %(filename)s [LINE:%(lineno)d] #%(levelname)-8s   %(message)s',
                    level=logging.INFO, filename=filename
                    # level=logging.DEBUG,  # Можно заменить на другой уровень логгирования.
                    )