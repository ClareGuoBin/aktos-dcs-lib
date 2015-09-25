# coding: utf-8

import re
from pprint import pprint

class MarkdownConfig(object):
    """
    self.flatten(): returns flattened array list of config file
    self.tests(): runs tests

    example usage:

        cfg = MarkdownConfig('test-config.md')
        cfg.tests()
        for fl in cfg.flatten():
            print ''.join(fl)

    """
    def __init__(self, config_file=''):
        if config_file:
            self.open_config(config_file)


    def open_config(self, config_file):
        with open(config_file) as f:
            self.content = f.read().decode('utf-8')


    def find_indent_char(self, content):
        m = re.search(r'^([ \t]{1,})[a-zA-Z_0-9\*]+', content, re.M|re.L|re.U)
        if m:
            #print "groups: ", m.groups()
            self.indent = m.group(1)
        else:
            self.indent = ' ' * 2

        print "indent char: ", repr(self.indent)


    def flatten(self):
        return self._flatten(self.content)

    def _flatten(self, content):
        """
        :param content:
        :param prev:
        :return:

        """
        self.find_indent_char(content)
        parent = []
        flattened = []

        for line in content.split('\n'):
            if line.strip():
                indent_level = self.get_indent_level(line)
                if indent_level == len(parent):
                    pass
                elif indent_level == len(parent) + 1:
                    # one more level indent
                    parent = flattened[-1]
                elif indent_level < len(parent):
                    # one level dedent
                    parent = parent[:indent_level]
                elif indent_level > len(parent) + 1:
                    raise BaseException

                #print "line, parent, flattened: ", line
                #pprint(parent)
                #pprint(flattened)

                flattened.append(parent + [line.strip()])

        return flattened

    def test_flattened_1(self):
        config_file = """
a:
    b: 1
    c: 2
    d:
        aa: 3
        bb: 4
        cc:
            aaa: 5
            bbb: 6
    e:
        dd: 123
        ee: 567

b: 1

c:
    f: 5
        """

        expected = """a:
a:b: 1
a:c: 2
a:d:
a:d:aa: 3
a:d:bb: 4
a:d:cc:
a:d:cc:aaa: 5
a:d:cc:bbb: 6
a:e:
a:e:dd: 123
a:e:ee: 567
b: 1
c:
c:f: 5"""

        flatten = self._flatten(config_file)
        flatten = '\n'.join([''.join(i) for i in flatten])
        assert flatten == expected

    def tests(self):
        self.test_flattened_1()
        print "All tests passed successfully..."

    def test_indent(self):
        for line in self.content.split('\n'):
            print "indent: ", self.get_indent_level(line), line

    def get_indent_level(self, string, prev_level=0):
        if string[:len(self.indent)] == self.indent:
            prev_level += 1
            try:
                rest = string[len(self.indent):]
                return self.get_indent_level(rest, prev_level=prev_level)
            except IndexError:
                pass
        return prev_level



class AktosConfig(MarkdownConfig):
    def config_table(self):
        """
        :return: lines which have ":..." at the end
        """
        flatten = self.flatten()
        flatten_cfg = [l for l in flatten if len(l[-1].split(':')[1].strip()) > 0]

        for l in flatten_cfg:
            print ''.join(l)

        return flatten_cfg

if __name__ == '__main__':
    c = AktosConfig('test-config.md')
    c.tests()
    c.config_table()
    
