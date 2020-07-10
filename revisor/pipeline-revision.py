"""Gitlab .

Usage:
  pipeline-revision.py <gitlab-url> [options] <dest>

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  -t --token=<access_token>  Token access to gitlab instance.
  -i --include=<csv>  Included files [default: 1c].       
  -e --exclude=<comma_list>  Excluded files. [default: 1c].
  -c --concurrency=<number of workers>      Number of workers[default: 1].
  -a --file=<file>           File previous input
  --format=<format>       Format of the print yaml, json, tree [default: yaml].
  -m --method=<method>       Method of clone {ssh, http} [default: http]
  --print                    Save tree

"""
from docopt import docopt
import logging
import logging.handlers
from gitlab_tree import GitlabTree
import sys

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

def split(list):
    return list.split(",") if list != "1c" else None

if __name__ == '__main__':
    arguments = docopt(__doc__, version='revisor v 0.0.1')
    print(arguments)
    in_file = arguments["--file"] 
    ipattern = split(arguments["--include"])
    opattern = split(arguments["--exclude"])
    tree = GitlabTree(arguments["<gitlab-url>"], arguments["--token"],
                      includes=ipattern, excludes=opattern, concurrency=int(arguments["--concurrency"]), in_file=in_file, method=arguments["--method"])
    log.debug(
        "Reading projects tree from gitlab at [%s]", arguments["<gitlab-url>"])
    tree.load_tree()
    if tree.is_empty():
        log.fatal(
            "The tree is empty, check your include/exclude patterns or run with more verbosity for debugging")
        sys.exit(1)

    if arguments["--print"]:
        tree.print_tree(arguments["--format"])
    else:
        tree.sync_tree(arguments["<dest>"])
