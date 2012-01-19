#!/usr/bin/env python

# MIT License
#
# Copyright (c) 2011 Nicolas Rolans
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import sys
import re
import os
import glob
from optparse import OptionParser

class CallBackParser:
    
    def __init__(self,data=None,file=None):

        self.section_start = '{'
        self.section_stop  = '}'
        self.cb_data_start = None;
        self.cb_data_stop = None;
        self.cb_section_start = None
        self.cb_section_stop = None
        self.cb_new_line = None
        self.save = 0;
        self.buffer = ''
        self.data = ''
        self.datalen = 0
    
        if( data == None and file == None ):
            raise Exception("No file or data provided")

        if( data != None and file != None ):
            raise Exception("File and data provided -- mutually exclusive")

        self.data = data;
        self.file = file;

        if( data != None ):
            self.datalen = len(data)
                
    def start_save(self):
        self.save = 1
    
    def stop_save(self):
        self.save = 0
        
    def clear_buffer(self):
        self.buffer = ''
        
    def get_buffer(self):
        return self.buffer
    
    def read(self):
        if self.data != None:
            return self.read_data()
        elif self.file != None:
            return self.read_file()
    
    def read_data(self):
        
        i = 0;
        
        if self.cb_data_start != None:
            self.cb_data_start()
        
        while( i < self.datalen ):
            
            if( self.save ):
                self.buffer += self.data[i];
            
            if( self.data[i] == self.section_start and self.cb_section_start != None ):
                self.cb_section_start()
            
            elif( self.data[i] == self.section_stop and self.cb_section_stop != None ):
                self.cb_section_stop()
        
            elif( self.data[i] == '\n' and self.cb_new_line != None ):
                self.cb_new_line()
            
            i += 1
            
        if self.cb_data_stop != None:
            self.cb_data_stop()

    def read_file(self):
        
        if self.cb_data_start != None:
            self.cb_data_start()
        
        while(1):
            
            char = self.file.read(1)
            if( char == '' ):
                break;
            
            if( self.save ):
                self.buffer += char;
            
            if( char == self.section_start and self.cb_section_start != None ):
                self.cb_section_start()
            
            elif( char == self.section_stop and self.cb_section_stop != None ):
                self.cb_section_stop()
        
            elif( char == '\n' and self.cb_new_line != None ):
                self.cb_new_line()



class BigParser:

    def __init__(self,
        keyword,
        data=None,      # Give a string to analyse
        file=None,      # Or an open file handle -- starts parsing where open
        color=False,
        casei=False,
        regex=False,
        perfect=False,
        invert=False,
        verbose=False):

        self.level = 0
        self.line = 1
        self.section_line = 0
    
        # Regex
        self.regex_obj = None;
        self.regex_pat = None;
        self.regex_pat_hl = None;    # used for highlighting only
        self.regex_flags = '';
    
        # Keyword/pattern to match
        self.keyword = keyword
        
        # Init interesting
        self.interesting = []
        
        # Options settings
        self._debug = verbose;
        self.color = color;
        self.casei = casei;
        self.pattern_is_regex = regex;
        self.perfect = perfect;
        self.invert = invert;
        
        # Set the regex flags
        if self.casei:
            self.regex_flags = '(?mi)'
        else:
            self.regex_flags = '(?m)'
        
        # Set the regex pattern
        if self.pattern_is_regex:
            self.regex_pat = self.regex_flags+self.keyword
            self.regex_pat_hl = self.regex_flags+'('+self.keyword+')'
        else:
            if self.perfect:
                self.regex_pat = self.regex_flags+r'(((^|[ ])'+re.escape(self.keyword)+r'([ {]|$)))'
                self.regex_pat_hl = self.regex_flags+'('+re.escape(self.keyword)+')'
            else:
                self.regex_pat = self.regex_flags+r'('+re.escape(self.keyword)+r')'
                self.regex_pat_hl = self.regex_pat
        
        # Prepare the compiled regex
        self.regex_obj = re.compile(self.regex_pat)
        
        # CBP object mapping
        self.cbp = CallBackParser(data=data,file=file)
        self.cbp.cb_data_start = self.cb_data_start
        self.cbp.cb_data_stop = self.cb_data_stop
        self.cbp.cb_section_start = self.cb_section_start
        self.cbp.cb_section_stop = self.cb_section_stop
        self.cbp.cb_new_line = self.cb_new_line
        self.cbp.start_save()
        
    def run(self):
        self.cbp.read()
        
    def cb_data_start(self):
        if self._debug:
            print "Parsing started"
        self.cbp.start_save()
        
    def cb_data_stop(self):
        if self._debug:
            print "Parsing finished"

    def cb_section_start(self):
        if self.level == 0:
            self.section_line = self.line
        self.level += 1
        if self._debug:
            print "Level: "+str(self.level)+" (start)"

    def cb_section_stop(self):
        self.level -= 1
        if self._debug:
            print "Level: "+str(self.level)+" (stop)"
        
        if self.level == 0:
            # End of a section, looking for matches
            self.match_check()

    def cb_new_line(self):
        self.line += 1;
        
        if self.level == 0:
            # End of a level0 line (i.e. no {}), looking for matches
            self.match_check()

    def match_check(self):
        """Check whether there is something we like in the buffer"""
        result = self.regex_obj.search(self.cbp.get_buffer())
        if (result != None and self.invert == False) or (result == None and self.invert == True):
            buff = self.cbp.get_buffer()
            if buff[0] == '\n':
                buff = buff[1:]
            
            if self.color:
                self.interesting.append( (self.section_line,self.highlight(buff)) )
            else:
                self.interesting.append( (self.section_line,buff) )

        self.cbp.clear_buffer()

    def highlight(self,haystack):
        return re.sub(self.regex_pat, self.cb_highlight, haystack)
    
    def cb_highlight(self,data):
        return re.sub(self.regex_pat_hl,r'\033[91m\1\033[0m',data.group(0))
        #return data.group(0).replace(self.keyword, '\033[91m'+self.keyword+'\033[0m')

def unique_list(seq, idfun=None):  
    # order preserving 
    if idfun is None: 
        def idfun(x): return x 
    seen = {} 
    result = [] 
    for item in seq: 
        marker = idfun(item) 
        # in old Python versions: 
        # if seen.has_key(marker) 
        # but in new ones: 
        if marker in seen: continue 
        seen[marker] = 1 
        result.append(item) 
    return result

# Option parsing
usage = "Usage: %prog [options] pattern [files+]\n\nIf no files or - are provided, stdin is used instead."
parser = OptionParser(usage=usage)
parser.add_option("-c", "--color", action='store_true', dest="color", default=False,help="Show colours")
parser.add_option("-n", "--number", action='store_true', dest="number", default=False,help="Show line numbers")
parser.add_option("-i", "--ignore-case", action='store_true', dest="casei", default=False,help="Case insensitive")
parser.add_option("-E", "--extended-regexp", action='store_true', dest="regex", default=False,help='Regex pattern')
parser.add_option("-w", "--word-regexp", action='store_true', dest="perfect", default=False,help='Perfect matches')
parser.add_option("-v", "--invert-match", action='store_true', dest="invert", default=False,help='Invert match')
parser.add_option("", "--verbose", action='store_true', dest="verbose", default=False,help='Verbose')
(options, posit) = parser.parse_args()
args = options.__dict__

# Check that we received a keyword/pattern
if len(posit) == 0:
    parser.print_help()
    sys.exit(1)

# If we don't receive any file (pattern only), read from stdin
if len(posit) == 1:
    posit.append('-');

# Pattern
keyword = posit[0]

# Check whether glob matches anything
filenames = []
for item in posit[1:]:
    if item == '-':
        filenames.append(item)
    else:
        glob_files = glob.glob(item) 
        if len(glob_files) == 0:
            print >> sys.stderr, "File not found: "+str(item)
        for file in glob_files:
            filenames.append(file)
    
n_files = len(filenames)


for filename in unique_list(filenames):

    try:
        # Is it stdin or a file?
        file = None;
        if filename == '-':
            file = sys.stdin;
        elif os.path.isfile(filename):
            file = open(filename,'r')

        if file != None:

            # Search it
            bp = BigParser(keyword,
                file=file,
                color=args.get('color'),
                casei=args.get('casei'),
                regex=args.get('regex'),
                perfect=args.get('perfect'),
                verbose=args.get('verbose'),
                invert=args.get('invert')
                )
            bp.run()
            
            if filename != '-':
                file.close()
            
            # Loop through the matches
            for item in bp.interesting:
                # Output formatting
                start_line = item[0]                # Line number
                for line in item[1].split('\n'):    # Actual line content
                    line_prefix = ''
                    if n_files > 1:
                        line_prefix += os.path.basename(filename)+':'
                    if args.get('number'):
                        line_prefix += str(start_line)+':'
                        start_line += 1
                    print line_prefix+line

    except Exception, e:
        print >> sys.stderr, e

