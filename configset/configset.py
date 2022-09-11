from __future__ import print_function
import sys
import argparse

if sys.version_info.major == 2:
    import ConfigParser
else:
    import configparser as ConfigParser

import os
import traceback
import re
from collections import OrderedDict
import inspect
import ast, json

if not __name__ == '__main__':
    def debug(*args, **kwargs):
        for i in kwargs:
            print(i, "=" , kwargs.get(i), type(kwargs.get(i)))

__platform__ = 'all'
__contact__ = 'licface@yahoo.com'

class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super(OrderedDict, self).__setitem__(key, value)

class configset(ConfigParser.RawConfigParser):
    def __init__(self, configfile = ''):
        ConfigParser.RawConfigParser.__init__(self)
        self.allow_no_value = True
        self.optionxform = str

        #self.cfg = ConfigParser.RawConfigParser(allow_no_value=True)
        self.path = None

        configfile = configfile or os.path.splitext(os.path.realpath(sys.argv[0]))[0] + ".ini"
        
        self.configname = configfile + ".ini"

        self.configname = configfile
        self.configname_str = configfile

        try:
            if os.path.isfile(self.configname):
                if os.getenv('SHOW_CONFIGNAME'):
                    print("CONFIGNAME:", os.path.realpath(self.configname))
        except:
            pass

        configpath = ''
        configpath = inspect.stack()[1][3]

        if os.path.isfile(configpath):
            configpath = os.path.dirname(configpath)
        else:
            configpath = os.getcwd()

        configpath = os.path.realpath(configpath)

        if not self.path:
            self.path = os.path.dirname(inspect.stack()[0][1])

        if not os.path.isfile(self.configname):
            f = open(self.configname, 'w')
            f.close()
            self.read(self.configname)
        
        if not os.path.isfile(self.configname):
            print("CONFIGNAME:", os.path.abspath(self.configname), " NOT a FILE !!!")
            sys.exit("Please Set configname before !!!")

    def configfile(self, configfile):
        self.configname = os.path.realpath(configfile)
        return self.configname

    def config_file(self, configfile):
        return self.configfile(configfile)

    def set_configfile(self, configfile):
        return self.configfile(configfile)

    def set_config_file(self, configfile):
        return self.set_configfile(configfile)

    def filename(self):
        return os.path.realpath(self.configname)

    def get_configfile(self):
        return os.path.realpath(self.configname)

    def get_config_file(self):
        return os.path.realpath(self.configname)

    def write_config(self, section, option, value='', configfile = None):
        self.configname = configfile or self.configname
        if os.path.isfile(self.configname):
            self.read(self.configname)
        else:
            print("Not a file:", self.configname)
            sys.exit("Not a file: " + self.configname)

        value = value or ''

        try:
            self.set(section, option, value)
        except ConfigParser.NoSectionError:
            self.add_section(section)
            self.set(section, option, value)
        except ConfigParser.NoOptionError:
            self.set(section, option, value)

        if sys.version_info.major == '2':
            cfg_data = open(self.configname,'wb')
        else:
            cfg_data = open(self.configname,'w')

        try:
            self.write(cfg_data)
        except:
            print(traceback.format_exc())
            #import io
            #io_data = io.BytesIO(cfg_data.read().encode('utf-8'))
            #self.write(io_data)
        cfg_data.close()

        return self.read_config(section, option)

    def write_config2(self, section, option, value='', configfile=''):
        self.configname = configfile or self.configname
        
        if os.path.isfile(self.configname):
            self.read(self.configname)
        else:
            print("Not a file:", self.configname)
            sys.exit("Not a file: " + self.configname)

        if not value == None:

            try:
                self.get(section, option)
                self.set(section, option, value)
            except ConfigParser.NoSectionError:
                return "\tNo Section Name: '%s'" %(section)
            except ConfigParser.NoOptionError:
                return "\tNo Option Name: '%s'" %(option)
            
            if sys.version_info.major == '2':
                cfg_data = open(self.configname,'wb')
            else:
                cfg_data = open(self.configname,'w')

            self.write(cfg_data)
            cfg_data.close()
            return self.read_config(section, option)
        else:
            return None

    def read_config(self, section, option, value = None):
        """
            option: section, option, value=None
        """
        
        self.read(self.configname)
        
        try:
            data = self.get(section, option)

            if value and not data:
                self.write_config(section, option, value)
        except:
            try:
                self.write_config(section, option, value)
            except:
                print ("error:", traceback.format_exc())

        return self.get(section, option)

    def read_config2(self, section, option, value = None, configfile=''): #format ['aaa','bbb','ccc','ddd']
        """
            option: section, option, filename=''
            format output: ['aaa','bbb','ccc','ddd']

        """

        return self.get_config_as_list(section, option, value)

    def read_config_as_list(self, section, option, value = None, configfile=''): #format ['aaa','bbb','ccc','ddd']
        return self.get_config_as_list(section, option, value)

    def read_config3(self, section, option, value = None, filename=''): #format result: [[aaa.bbb.ccc.ddd, eee.fff.ggg.hhh], qqq.xxx.yyy.zzz]
        """
            option: section, option, filename=''
            format output first: [[aaa.bbb.ccc.ddd, eee.fff.ggg.hhh], qqq.xxx.yyy.zzz]
            note: if not separated by comma then second output is normal

        """

        self.dict_type = MultiOrderedDict
        if filename:
            if os.path.isfile(filename):
                self.read(filename)
        else:
            self.read(self.configname)

        data = []
        cfg = self.get(section, option)

        for i in cfg:
            if "," in i:
                d1 = str(i).split(",")
                d2 = []
                for j in d1:
                    d2.append(str(j).strip())
                data.append(d2)
            else:
                data.append(i)
        self.dict_type = None
        self.read(self.configname)
        return data

    def read_config4(self, section, option, value = '', filename='', verbosity=None): #format result: [aaa.bbb.ccc.ddd, eee.fff.ggg.hhh, qqq.xxx.yyy.zzz]
        """
            option: section, option, filename=''
            format result: [aaa.bbb.ccc.ddd, eee.fff.ggg.hhh, qqq.xxx.yyy.zzz]
            note: all output would be array/tuple

        """
        self.dict_type = MultiOrderedDict
        if filename:
            if os.path.isfile(filename):
                self.read(filename)
        else:
            self.read(self.configname)
        data = []
        try:
            cfg = self.get(section, option)
            if not cfg == None:
                for i in cfg:
                    if "," in i:
                        d1 = str(i).split(",")
                        for j in d1:
                            data.append(str(j).strip())
                    else:
                        data.append(i)
                self.dict_type = None
                self.read(self.configname)
                return data
            else:
                self.dict_type = None
                self.read(self.configname)
                return None
        except:
            data = self.write_config(section, option, filename, value)
            self.dict_type = None
            self.read(self.configname)
            return data

    def read_config5(self, section, option, filename='', verbosity=None): #format result: {aaa:bbb, ccc:ddd, eee:fff, ggg:hhh, qqq:xxx, yyy:zzz}
        """
            option: section, option, filename=''
            input separate is ":" and commas example: aaa:bbb, ccc:ddd
            format result: {aaa:bbb, ccc:ddd, eee:fff, ggg:hhh, qqq:xxx, yyy:zzz}

        """
        self.dict_type = MultiOrderedDict
        if filename:
            if os.path.isfile(filename):
                self.read(filename)
        else:
            self.read(self.configname)
        data = {}

        cfg = self.get(section, option)
        for i in cfg:
            if "," in i:
                d1 = str(i).split(",")
                for j in d1:
                    d2 = str(j).split(":")
                    data.update({str(d2[0]).strip():int(str(d2[1]).strip())})
            else:
                for x in i:
                    e1 = str(x).split(":")
                    data.update({str(e1[0]).strip():int(str(e1[1]).strip())})
        self.dict_type = None
        self.read(self.configname)
        return data

    def read_config6(self, section, option, filename='', verbosity=None): #format result: {aaa:[bbb, ccc], ddd:[eee, fff], ggg:[hhh, qqq], xxx:[yyy:zzz]}
        """

            option: section, option, filename=''
            format result: {aaa:bbb, ccc:ddd, eee:fff, ggg:hhh, qqq:xxx, yyy:zzz}

        """
        self.dict_type = MultiOrderedDict
        if filename:
            if os.path.isfile(filename):
                self.read(filename)
        else:
            self.read(self.configname)
        data = {}

        cfg = self.get(section, option)
        for i in cfg:
            if ":" in i:
                d1 = str(i).split(":")
                d2 = int(str(d1[0]).strip())
                for j in d1[1]:
                    d3 = re.split("['|','|']", d1[1])
                    d4 = str(d3[1]).strip()
                    d5 = str(d3[-2]).strip()
                    data.update({d2:[d4, d5]})
            else:
                pass
        self.dict_type = None
        self.read(self.configname)
        return data

    def get_config(self, section, option, value=None):
        data = None
        if value and not isinstance(value, str):
            value = str(value)

        if not value or value == 'None':
            value = ''
        self.read(self.configname)
        try:
            data = self.read_config(section, option, value)
        except ConfigParser.NoSectionError:
            if os.getenv('DEBUG'):
                print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config(section, option, value)
        except ConfigParser.NoOptionError:
            if os.getenv('DEBUG'):
                print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config(section, option, value)
        except:
            if os.getenv('DEBUG'):
                print (traceback.format_exc())
        #self.read(self.configname)
        if data == 'False' or data == 'false':
            return False
        elif data == 'True' or data == 'true':
            return True
        elif str(data).isdigit():
            return int(data)
        else:
            return data

    def get_config_as_list(self, section, option, value=None):
        '''
            value (str): string comma delimiter or string tuple/list : data1, data2, datax or [data1, data2, datax] or (data1, data2, datax)
        '''
        if value and not isinstance(value, str):
            value = str(value)

        if not value:
            value = ''
        self.read(self.configname)
        try:
            data = self.read_config(section, option, value)
        except ConfigParser.NoSectionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config(section, option, value)
        except ConfigParser.NoOptionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config(section, option, value)
        except:
            print (traceback.format_exc())
        data = re.split("\n|, |,| ", data)
        data = list(filter(None, data))
        data_list = []
        dlist = []
        
        for i in data:
            
            if "[" in str(i) and "]" in str(i):
                dl = re.findall("\[.*?\]", i)
                
                if dl:
                    for x in dl:
                        
                        
                        try:
                            dlist.append(ast.literal_eval(re.sub("\[|\]", "", x)))
                        except:
                            try:
                                dlist.append(json.loads(x))
                            except Exception as e:
                                print("ERROR:", e, "list string must be containt ' or \" example: ['data1', 'data2'] ")
                                return False
                        
                        # data = re.sub(x, "", data)
                        data.remove(x)
                        
                        
            else:
                if "'" in i or '"' in i:
                    
                    x = re.sub("'|\"", "", i)
                    
                    dlist.append(x)
                    data.remove(i)
        
        for i in data:
            if i.strip() == 'False' or i.strip() == 'false':
                data_list.append(False)
            elif i.strip() == 'True' or i.strip() == 'true':
                data_list.append(True)
            elif str(i).strip().isdigit():
                data_list.append(int(i.strip()))
            else:
                  data_list.append(i.strip())
        return dlist + data_list

    def get_config2(self, section, option, value = '', filename='', verbosity=None):
        if os.path.isfile(filename):
            self.read(filename)
        else:
            filename = self.configname
            self.read(self.configname)
        try:
            data = self.read_config2(section, option, filename)
        except ConfigParser.NoSectionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config2(section, option, filename)
        except ConfigParser.NoOptionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config2(section, option, filename)
        return data

    def get_config3(self, section, option, value = '', filename='', verbosity=None):
        if os.path.isfile(filename):
            self.read(filename)
        else:
            filename = self.configname
            self.read(self.configname)
        try:
            data = self.read_config3(section, option, filename)
        except ConfigParser.NoSectionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config3(section, option, filename)
        except ConfigParser.NoOptionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config3(section, option, filename)
        return data

    def get_config4(self, section, option, value = '', filename='', verbosity=None):
        if os.path.isfile(filename):
            self.read(filename)
        else:
            filename = self.configname
            self.read(self.configname)
        try:
            data = self.read_config4(section, option, filename)
        except ConfigParser.NoSectionError:
            #print "Error 1 =", traceback.format_exc()
            self.write_config(section, option, value)
            data = self.read_config4(section, option, filename)
            #print "data 1 =", data
        except ConfigParser.NoOptionError:
            #print "Error 2 =", traceback.format_exc()
            self.write_config(section, option, value)
            data = self.read_config4(section, option, filename)
            #print "data 2 =", data
        #print "DATA =", data
        return data

    def get_config5(self, section, option, value = '', filename='', verbosity=None):
        if os.path.isfile(filename):
            self.read(filename)
        else:
            filename = self.configname
            self.read(self.configname)
        try:
            data = self.read_config5(section, option, filename)
        except ConfigParser.NoSectionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config5(section, option, filename)
        except ConfigParser.NoOptionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config5(section, option, filename)
        return data

    def get_config6(self, section, option, value = '', filename='', verbosity=None):
        if os.path.isfile(filename):
            self.read(filename)
        else:
            filename = self.configname
            self.read(self.configname)
        try:
            data = self.read_config6(section, option, filename)
        except ConfigParser.NoSectionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config6(section, option, filename)
        except ConfigParser.NoOptionError:
            print (traceback.format_exc())
            self.write_config(section, option, value)
            data = self.read_config6(section, option, filename)
        return data

    def write_all_config(self, filename='', verbosity=None):
        if os.path.isfile(filename):
            self.read(filename)
        else:
            filename = self.configname
            self.read(self.configname)

    def read_all_config(self, section=[]):
        print("CONFIGFILE:", self.configname)
        self.read(self.configname)
        dbank = []
        if section:
            for i in section:
                print("[" + i + "]")
                options = self.options(i)
                data = {}
                for o in options:
                    d = self.get(i, o)
                    print("   " + o + "=" + d)
                    data.update({o: d})
                dbank.append([i, data])
        else:
            for i in self.sections():
                #section.append(i)
                print("[" + i + "]")
                data = {}
                for x in self.options(i):
                    d = self.get(i, x)
                    print("   " + x + "=" + d)
                    data.update({x:d})
                dbank.append([i,data])
        print("\n")
        return dbank

    def read_all_section(self, filename='', section='server'):
        if os.path.isfile(filename):
            self.read(filename)
        else:
            filename = self.configname
            self.read(self.configname)

        dbank = []
        dhost = []
        for x in self.options(section):
            d = self.get(section, x)
            #data.update({x:d})
            dbank.append(d)
            if d:
                if ":" in d:
                    data = str(d).split(":")
                    host = str(data[0]).strip()
                    port = int(str(data[1]).strip())
                    dhost.append([host,  port])

        return [dhost,  dbank]

    def usage(self):
        parser = argparse.ArgumentParser(formatter_class= argparse.RawTextHelpFormatter)
        parser.add_argument('CONFIG_FILE', action = 'store', help = 'Config file name path')
        parser.add_argument('-r', '--read', help = 'Read Action', action = 'store_true')
        parser.add_argument('-w', '--write', help = 'Write Action', action = 'store_true')
        parser.add_argument('-s', '--section', help = 'Section Write/Read', action = 'store')
        parser.add_argument('-o', '--option', help = 'Option Write/Read', action = 'store')
        parser.add_argument('-t', '--type', help = 'Type Write/Read', action = 'store', default = 1, type = int)
        if len(sys.argv) == 1:
            print ("\n")
            parser.print_help()
        else:
            print ("\n")
            args = parser.parse_args()
            if args.CONFIG_FILE:
                self.configname =args.CONFIG_FILE
                if args.read:
                    if args.type == 1:
                        if args.section and args.option:
                            self.read_config(args.section, args.option)
                    elif args.type == 2:
                        if args.section and args.option:
                            self.read_config2(args.section, args.option)
                    elif args.type == 3:
                        if args.section and args.option:
                            self.read_config3(args.section, args.option)
                    elif args.type == 4:
                        if args.section and args.option:
                            self.read_config4(args.section, args.option)
                    elif args.type == 5:
                        if args.section and args.option:
                            self.read_config5(args.section, args.option)
                    elif args.type == 6:
                        if args.section and args.option:
                            self.read_config6(args.section, args.option)
                    else:
                        print ("INVALID TYPE !")
                        
                        print ("\n")
                        parser.print_help()
                else:
                    print ("Please use '-r' for read or '-w' for write")
                    
                    print ("\n")
                    parser.print_help()
            else:
                print ("NO FILE CONFIG !")
                
                print ("\n")
                parser.print_help()

if __name__ == '__main__':
    from pydebugger.debug import debug
    usage()
