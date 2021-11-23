# -*- coding: utf-8 -*-

from .import parser
import re

class maya_abc(parser.parser):
    """Yafray
    """

    def __init__(self):
        parser.parser.__init__(self)
        self.re_percent = re.compile (r'^\d+')
        self.re_frame_start = re.compile (r'.*started.*generating.*alembic.*')
        self.re_frame_done = re.compile (r'.*alembic.*export.*successfully.*done.*')
        self.re_errors = [re.compile(r'.*RuntimeError*')]



    def do(self, data, mode):
        """Missing DocString
        :param data:
        :param mode:
        :return:
        """

        if len (data) < 1:
            return

        self.rendered_frames = []
        for i in data.split ('\n'):
            if not i:
                #skip empty strings
                continue

            elif self.re_percent.match(i):
                try:
                    to_int  = int(i)
                except ValueError:
                    continue
                self.rendered_frames.append (to_int)

            else:
                for j in self.re_errors:
                    if j.match(i):
                        self.error =True
                        return


        if self.rendered_frames:
            self.frame = int(max(self.rendered_frames) % self.numframes-1)
            self.calculate ()
