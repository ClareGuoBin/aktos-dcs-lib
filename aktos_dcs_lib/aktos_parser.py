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

        #print "DEBUG: indent char: ", repr(self.indent)


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

    def flat_dict(self):
        flat_list = self.flatten()
        _dict = {}
        for i in flat_list:
            last_key, value = i[-1].split(':')
            value = value.strip()
            if value:
                try:
                    if len(value.split('.')) > 1:
                        value = float(value)
                    else:
                        value = int(value)
                except:
                    pass

                stripped_keys = [j.replace(':', '') for j in i[:-1]]
                keys = stripped_keys + [last_key]
                flat_key = '.'.join(keys)
                _dict[flat_key] = value

        #pprint(_dict)
        return _dict



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
    """
    example config:

        a:
            b:
                c: 1
                d: 2
            e: 3
        f: 4

    flatten:



    raw_config_table:
    [
        ['a:', 'b:', 'c: 1'],
        ['a:', 'b:', 'd: 2'],
        ['a:', 'e: 3'],
        ['f: 4'],
    ]

    flat_dict:

    {
        'a.b.c': 1,
        'a.b.d': 2,
        'a.e': 3,
        'f': 4,
    }
    """
    def raw_config_table(self):
        """
        :return: lines which have ":..." at the end
        """
        flatten = self.flatten()
        flatten_cfg = [l for l in flatten if len(l[-1].split(':')[1].strip()) > 0]
        return flatten_cfg

    def raw_config_table_str(self):
        for l in self.raw_config_table():
            print ''.join(l)



if __name__ == '__main__':
    c = AktosConfig('aktos-parser-test2.db')
    c.tests()
    #pprint(c.raw_config_table())
    c.flat_dict()

    
