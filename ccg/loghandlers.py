import os
from logging.handlers import TimedRotatingFileHandler


class ParentPathFileHandler(TimedRotatingFileHandler):
    def __init__(self, filename, *args, **kwargs):            
        try: 
            os.makedirs(os.path.dirname(filename))
        except OSError:
            pass
	TimedRotatingFileHandler.__init__(self, filename, *args, **kwargs)
