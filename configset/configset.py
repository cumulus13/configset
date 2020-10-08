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
# from make_colors import make_colors
from pydebugger.debug import debug

__sdk__ = '2.7+'
__platform__ = 'all'
__url__ = 'licface@yahoo.com'
__build__ = '2.7'

#configname ='conf.ini'

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

        if not self.path:
            self.path = os.path.dirname(inspect.stack()[0][1])

        if self.configname:
            if not os.path.isfile(self.configname):
                f = open(self.configname, 'w')
                f.close()
            self.read(self.configname)
            #debug(configname_1 = self.configname)
    
    def configfile(self, configfile):
        self.configname = configfile
        return self.configname

    def filename(self):
        return self.configname

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

    def write_config(self, section, option, value=None, filename=''):
        if not value:
            value = ''
        if filename:
            if not os.path.isfile(self.configname):
                self.read(filename)
            else:
                self.read(self.configname)
        else:
            filename = self.configname
            #self.read(self.configname)

        try:
            self.set(section, option, value)
        except ConfigParser.NoSectionError:
            self.add_section(section)
            self.set(section, option, value)
        except ConfigParser.NoOptionError:
            self.set(section, option, value)

        if os.path.isfile(filename):
            cfg_data = open(filename,'w+')
        else:
            cfg_data = open(filename,'wb')

        self.write(cfg_data) 
        cfg_data.close()  

        return self.read_config(section, option, filename)

    def write_config2(self, section, option, filename='', value=None):
        if filename:
            if os.path.isfile(filename):
                self.read(filename)

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

    def read_config(self, section, option, filename='', value=None):
        """
            option: section, option, filename='', value=None
        """
        if filename:
            if os.path.isfile(filename):
                self.read(filename)
        try:
            data = self.get(section, option)
            #print("data C =", data)
            #debug(data_c = data)
        except:
            try:
                self.write_config(section, option, value, filename)
            except:
                print ("error:", traceback.format_exc())
            data = self.get(section, option)
        self.read(self.configname)
        return data

    def read_config2(self, section, option, filename='', value=None): #format ['aaa','bbb','ccc','ddd']
        """
            option: section, option, filename=''
            format output: ['aaa','bbb','ccc','ddd']

        """
        self.dict_type = MultiOrderedDict
        if filename:
            if os.path.isfile(filename):
                self.read(filename)

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

    def read_config3(self, section, option, filename='', value=None): #format result: [[aaa.bbb.ccc.ddd, eee.fff.ggg.hhh], qqq.xxx.yyy.zzz]
        """
            option: section, option, filename=''
            format output first: [[aaa.bbb.ccc.ddd, eee.fff.ggg.hhh], qqq.xxx.yyy.zzz]
            note: if not separated by comma then second output is normal

        """

        self.dict_type = MultiOrderedDict
        if filename:
            if os.path.isfile(filename):
                self.read(filename)

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

    def read_config4(self, section, option, filename='', value = '', verbosity=None): #format result: [aaa.bbb.ccc.ddd, eee.fff.ggg.hhh, qqq.xxx.yyy.zzz]
        """
            option: section, option, filename=''
            format result: [aaa.bbb.ccc.ddd, eee.fff.ggg.hhh, qqq.xxx.yyy.zzz]
            note: all output would be array/tuple

        """
        self.dict_type = MultiOrderedDict
        if filename:
            if os.path.isfile(filename):
                self.read(filename)

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

    def get_config(self, section, option, value=None, filename=None):
        if value and not isinstance(value, str):
            value = str(value)

        if value == 'None':
            value = ''


        try:
            data = self.read_config(section, option, filename, value)
            # print("value =", value)
            if value:
                self.write_config(section, option, value, filename)
                data = self.read_config(section, option, filename, value)
            # print("DATAX {0} - {1} =".format(section, option), data)
        except ConfigParser.NoSectionError:
            print (traceback.format_exc())
            self.write_config(section, option, value, filename)
            data = self.read_config(section, option, filename, value)
        except ConfigParser.NoOptionError:
            print (traceback.format_exc())
            self.write_config(section, option, value, filename)
            data = self.read_config(section, option, filename, value)
        except:
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

    def get_config2(self, section, option, filename='', value=None, verbosity=None):
        if not os.path.isfile(self.configname):
            filename = self.get_config_file(filename, verbosity)
        else:
            filename = self.configname
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

    def get_config3(self, section, option, filename='', value=None, verbosity=None):
        if not os.path.isfile(self.configname):
            filename = self.get_config_file(filename, verbosity)
        else:
            filename = self.configname
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

    def get_config4(self, section, option, filename='', value='', verbosity=None):
        if not os.path.isfile(self.configname):
            filename = self.get_config_file(filename, verbosity)
        else:
            filename = self.configname
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

    def get_config5(self, section, option, filename='', value=None, verbosity=None):
        if not os.path.isfile(self.configname):
            filename = self.get_config_file(filename, verbosity)
        else:
            filename = self.configname
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

    def get_config6(self, section, option, filename='', value=None, verbosity=None):
        if not os.path.isfile(self.configname):
            filename = self.get_config_file(filename, verbosity)
        else:
            filename = self.configname
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
        if not os.path.isfile(self.configname):
            filename = self.get_config_file(filename, verbosity)
        else:
            filename = self.configname

    def read_all_config(self, section=[]):
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
        if filename:
            if os.path.isfile(filename):
                self.read(filename)

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
    usage()
