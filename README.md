# bigrep

bigrep filters objects based on keywords in curly braces delimited files. As opposed to grep, it doesn't return the matching line but the complete object.

It works particularly well with F5 BIGIP config files.

## Usage

    Usage: bigrep.py [options] pattern [files+]
    
    If no files or - are provided, stdin is used instead.
    
    Options:
      -h, --help            show this help message and exit
      -c, --color           Show colours
      -n, --number          Show line numbers
      -i, --ignore-case     Case insensitive
      -E, --extended-regexp
                            Regex pattern
      -w, --word-regexp     Perfect matches
      -v, --invert-match    Invert match
      -V, --version         Show version number
      --verbose             Verbose
    

# Examples

Find all the objects containing the keyword 'virtual'.

    # bigrep virtual file.conf 
    ltm virtual vs_web_corporate {
        destination 10.0.0.100:http
        ip-protocol tcp
        mask 255.255.255.255
        pool pool_webserver
        profiles {
            tcp { }
        }
        snat automap
        vlans-disabled
    }

Find all the objects containing the keyword 'pool'.

    # bigrep pool file.conf 
    ltm virtual vs_web_corporate {
        destination 10.0.0.100:http
        ip-protocol tcp
        mask 255.255.255.255
        pool pool_webserver
        profiles {
            tcp { }
        }
        snat automap
        vlans-disabled
    }
    ltm pool /Common/pool_webserver {
        members {
            /Common/web01:http {
                address 10.0.0.1
            }
            /Common/web02:http {
                address 10.0.0.2
            }
        }
    }

A more interesting example, piping the result in another bigrep instance:

    # bigrep virtual bigip2.conf | bigrep pool_webserver
    ltm virtual vs_web_corporate {
        destination 10.0.0.100:http
        ip-protocol tcp
        mask 255.255.255.255
        pool pool_webserver
        profiles {
            tcp { }
        }
        snat automap
        vlans-disabled
    }




