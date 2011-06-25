#!/usr/bin/env python

import sys
import re
import os
from optparse import OptionParser

class CallBackParser:
    
    section_start = '{'
    section_stop  = '}'
    cb_data_start = None;
    cb_data_stop = None;
    cb_section_start = None
    cb_section_stop = None
    cb_new_line = None
    save = 0;
    buffer = ''
    data = ''
    datalen = 0
    
    def __init__(self,data):
        self.data = data;
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

class BigParser:

    interesting = [];
    level = 0
    cbp = None;
    keyword = ''
    line = 1
    section_line = 0
    _debug = 0;

    # Regex
    regex_obj = None;
    regex_pat = None;
    regex_pat_hl = None;    # used for highlighting only
    regex_flags = '';

    # Options
    color = ''
    casei = ''
    pattern_is_regex = ''
    verbose = ''
    perfect = False;

    def __init__(self,data,keyword,
        color=False,
        casei=False,
        regex=False,
        perfect=False,
        verbose=False):

        # Keyword/pattern to match
        self.keyword = keyword
        
        # Options settings
        self._debug = verbose;
        self.color = color;
        self.casei = casei;
        self.pattern_is_regex = regex;
        self.perfect = perfect;
       
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
       
        self.cbp = CallBackParser(data)
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
        if result != None:
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

# Option parsing
usage = "Usage: %prog [options] [files+]\n\nIf no files or - are provided, stdin is used instead."
parser = OptionParser(usage=usage)
parser.add_option("-c", "--color", action='store_true', dest="color", default=False,help="Show colours")
parser.add_option("-n", "--number", action='store_true', dest="number", default=False,help="Show line numbers")
parser.add_option("-i", "--casei", action='store_true', dest="casei", default=False,help="Case insensitive")
parser.add_option("-E", "--regex", action='store_true', dest="regex", default=False,help='Regex pattern')
parser.add_option("-p", "--perfect", action='store_true', dest="perfect", default=False,help='Perfect matches')
parser.add_option("-v", "--verbose", action='store_true', dest="verbose", default=False,help='Verbose')
(options, posit) = parser.parse_args()
args = options.__dict__

# Check that we received a keyword/pattern
if len(posit) == 0:
    parser.print_help()
    exit(1)

# If we don't receive any file (pattern only), read from stdin
if len(posit) == 1:
    posit.append('-');

keyword = posit[0]
n_files = len(posit)-1

for file in posit[1:]:

    try:
        # Is it stdin or a file
        if file == '-':
            data = sys.stdin.read()
        else:
            f = open(file,'r')
            data = f.read()
            f.close()
        
        # Search it
        bp = BigParser(data,keyword,
            color=args.get('color'),
            casei=args.get('casei'),
            regex=args.get('regex'),
            perfect=args.get('perfect'),
            verbose=args.get('verbose')
            )
        bp.run()
        
        # Loop through the matches
        for item in bp.interesting:

            # Output formatting
            start_line = item[0]
            for line in item[1].split('\n'):
                line_prefix = ''
                if n_files > 1:
                    line_prefix += os.path.basename(file)+':'
                if args.get('number'):
                    line_prefix += str(start_line)+':'
                    start_line += 1
                print line_prefix+line

    except Exception, e:
        print e

