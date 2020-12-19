from __future__ import print_function
import sys
import argparse
import inspect

if sys.version_info.major == 2:
    import ConfigParser
else:
    import configparser as ConfigParser

import os
import traceback
import re
from collections import OrderedDict
import inspect
# from make_colors import make_colors
# SITE_PACKAGES = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'site-packages')
# print(SITE_PACKAGES)
# sys.path.append(SITE_PACKAGES)
if not __name__ == '__main__':
    def debug(*args, **kwargs):
        for i in kwargs:
            print("i =", kwargs.get(i))

__platform__ = 'all'
__contact__ = 'licface@yahoo.com'

class MultiOrderedDict(OrderedDict):
    def __setitem__(self, key, value):
        if isinstance(value, list) and key in self:
            self[key].extend(value)
        else:
            super(OrderedDict, self).__setitem__(key, value)


class configset(ConfigParser.RawConfigParser):
    def __init__(self, configfile = None):
        ConfigParser.RawConfigParser.__init__(self)
        self.allow_no_value = True
        self.optionxform = str

        #self.cfg = ConfigParser.RawConfigParser(allow_no_value=True)
        self.path = None
        self.configname = configfile
        self.configname_str = configfile
        try:
            if os.path.isfile(self.configname):
                if os.getenv('SHOW_CONFIGNAME'):
                    print("CONFIGNAME:", os.path.abspath(self.configname))
        except:
            pass
        configpath = ''
        try:
            configpath = inspect.stack()[0][1]
        except:
            pass
        if os.path.isfile(configpath):
            configpath = os.path.dirname(configpath)
        else:
            configpath = os.getcwd()
        
        if not self.configname:
            configname = os.path.splitext(inspect.stack()[1][1])[0]
            self.configname = configname + ".ini"

        if not self.path:
            self.path = os.path.dirname(inspect.stack()[0][1])
            
        if not os.path.isfile(self.configname):
            try:
                f = open(self.configname, 'w')
                f.close()
                self.read(self.configname)
            except:
                self.configname = "configset.ini"
                self.configname = os.path.join(configpath, self.configname)
                f = open(self.configname, 'w')
                f.close()
                self.read(self.configname)
        # debug(self_configname = self.configname, debug = True) 
        self.configname = os.path.abspath(self.configname)
        if os.path.isfile(self.configname):
            if not self.configname == self.configname_str:
                if os.getenv('SHOW_CONFIGNAME'):
                    print("CONFIGNAME:", os.path.abspath(self.configname))
            self.read(self.configname)
        else:
            print("CONFIGNAME:", os.path.abspath(self.configname), " NOT a FILE !!!")
            sys.exit("Please Set configname before !!!")

    
    def configfile(self, configfile):
        self.configname = configfile
        return self.configname

    def filename(self):
        return os.path.abspath(self.configname)

    #def get_config_file(self, filename='', verbosity=None):
        #if not filename:
            #filename = self.configname
        #configname = filename
        #self.configname = configname
        ##debug(configset_configname = self.configname)
        #self.path = None
        #if self.path:
            #if configname:
                #self.configname = os.path.join(os.path.abspath(self.path), os.path.basename(self.configname))

        #if os.path.isfile(os.path.join(os.getcwd(), filename)):
            ###debug(checking_001 = "os.path.isfile(os.path.join(os.getcwd(), filename))")
            #self.configname =os.path.join(os.getcwd(), filename)
            ###debug(configname = os.path.join(os.getcwd(), filename))
            #return os.path.join(os.getcwd(), filename)
        #elif os.path.isfile(filename):
            ###debug(checking_002 = "os.path.isfile(filename)")
            #self.configname =filename
            ###debug(configname = os.path.abspath(filename))
            #return filename
        #elif os.path.isfile(os.path.join(os.path.dirname(__file__), filename)):
            ###debug(checking_003 = "os.path.isfile(os.path.join(os.path.dirname(__file__), filename))")
            #self.configname =os.path.join(os.path.dirname(__file__), filename)
            ###debug(configname = os.path.join(os.path.dirname(__file__), filename))
            #return os.path.join(os.path.dirname(__file__), filename)
        #elif os.path.isfile(self.configname):
            ###debug(checking_004 = "os.path.isfile(configname)")
            ###debug(configname = os.path.abspath(configname))
            #return configname
        #else:
            ###debug(checking_006 = "ELSE")
            #fcfg = self.configname
            #f = open(fcfg, 'w')
            #f.close()
            #filecfg = fcfg
            ###debug(CREATE = os.path.abspath(filecfg))
            #return filecfg

    def write_config(self, section, option, value=''):
        self.read(self.configname)
        if value == None:
            value = ''
        
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

    def write_config2(self, section, option, value='', filename=''):
        if filename:
            if os.path.isfile(filename):
                self.read(filename)
        self.read(self.configname)

        if not value == None:

            try:
                self.get(section, option)
                self.set(section, option, value)
            except ConfigParser.NoSectionError:
                return "\tNo Section Name: '%s'" %(section)
            except ConfigParser.NoOptionError:
                return "\tNo Option Name: '%s'" %(option)
            cfg_data = open(filename,'wb')
            self.write(cfg_data)   
            cfg_data.close()
            return self.read_config(section, option)
        else:
            return None

    def read_config(self, section, option, value = None):
        """
            option: section, option, value=None
        """
        #print("read_config -> value =", value)
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

    def read_config2(self, section, option, value = None, filename=''): #format ['aaa','bbb','ccc','ddd']
        """
            option: section, option, filename=''
            format output: ['aaa','bbb','ccc','ddd']

        """
        self.dict_type = MultiOrderedDict
        if filename:
            if os.path.isfile(filename):
                self.read(filename)
        else:
            self.read(self.configname)

        try:
            data = self.get(section, option)
            #print("data C =", data)
            #debug(data_c = data)
        except:
            try:
                self.write_config(section, option, filename, value)
            except:
                print ("error:", traceback.format_exc())
            data = self.get(section, option)
        self.dict_type = None
        self.read(self.configname)
        return data

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
        data = re.split("\n|,| ", data)
        data = list(filter(None, data))
        data_list = []
        for i in data:
            if i.strip() == 'False' or i.strip() == 'false':
                data_list.append(False)
            elif i.strip() == 'True' or i.strip() == 'true':
                data_list.append(True)
            elif str(i).strip().isdigit():
                data_list.append(int(i.strip()))
            else:
                data_list.append(i.strip())
        return data_list
        
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
                        #debug("INVALID TYPE !")
                        print ("\n")
                        parser.print_help()
                else:
                    print ("Please use '-r' for read or '-w' for write")
                    #debug("Please use '-r' for read or '-w' for write")
                    print ("\n")
                    parser.print_help()
            else:
                print ("NO FILE CONFIG !")
                #debug("NO FILE CONFIG !")
                print ("\n")
                parser.print_help()


#configset_class = configset()
#configset_class.configname = configname
#if PATH:
#    configset_class.path = PATH 
#get_config_file = configset_class.get_config_file
#write_config = configset_class.write_config
#write_config2 = configset_class.write_config2
#read_config = configset_class.read_config
#read_config2 = configset_class.read_config2
#read_config3 = configset_class.read_config3
#read_config4 = configset_class.read_config4
#read_config5 = configset_class.read_config5
#read_config6 = configset_class.read_config6
#get_config = configset_class.get_config
#get_config2 = configset_class.get_config2
#get_config3 = configset_class.get_config3
#get_config4 = configset_class.get_config4
#get_config5 = configset_class.get_config5
#get_config6 = configset_class.get_config6
#write_all_config = configset_class.write_all_config
#read_all_config = configset_class.read_all_config
#read_all_section = configset_class.read_all_section
#usage = configset_class.usage

if __name__ == '__main__':
    from pydebugger.debug import debug
    usage()
