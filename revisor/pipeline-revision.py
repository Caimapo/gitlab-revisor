"""Gitlab .

Usage:
  pipeline-revision.py [options] branch ( --list | (--create --name=<branch_name> --ref=<branch_ref>) | --remove --name=<branch_name>)
  pipeline-revision.py [options] clone <path>
  pipeline-revision.py [options] plugins ((--list --name=<branch_name>) | (--check --name=<branch_name>) | (--push --name=<branch_name>)) [--sast | --dependency-check | --detect-secrets | --add-veracode] [ --recursive ]

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  -g --gitlab=<gitlab>       URL to gitlab instance.
  -t --token=<access_token>  Token access to gitlab instance.
  -i --include=<csv>         Included files in a comma separated string or csv path. [default: 1c].
  -e --exclude=<csv>         Excluded files in a comma separated string or csv path. [default: 1c].
  -c --concurrency=<number of workers>      Number of workers[default: 1].
  -f --file=<file>           File previous input, this should be yaml format
  --format=<format>          Format of the output {yaml, json, tree} [default: yaml].
  -m --method=<method>       Method of clone {ssh, http} [default: http]
  --dry-run                  
  -r --recursive            Recursive pipeline inspector
  -o --output=<output>      Output CSV File
  --throttle=<time>      throttle [default: 360]
"""
from docopt import docopt
import logging
import logging.handlers
from tree import Tree
import sys
import os
import csv
from gitlab import Gitlab

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def split(list):
    return list.split(",") if list != "1c" else None

def include_paths(path):
    includes = []
    try:
      with open(path, newline='') as file:
          includes = [row[0] for row in csv.reader(file)]
    except Exception as e:
        # No file, trying parse
        includes = split(path)
        log.debug("Error trying to openning the file input")
    return includes

def exclude_paths(path):
    excludes = []
    try:
      with open(path, newline='') as file:
          excludes = [row[0] for row in csv.reader(file)]
    except Exception as e:
        excludes = split(path)
        log.debug("Error trying to openning the file input")
    return excludes

def auth_gitlab(url, token):
    try:
        log.debug("Loading credentials")
        gitlab = Gitlab(url, private_token=token)
        return gitlab
    except GitlabAuthenticationError:
        log.fatal("[Invalid credentials]: {}".format(sys.exc_info()))
        sys.exit(1)

if __name__ == '__main__':
    arguments = docopt(__doc__, version='revisor v 0.0.1')
    # print(arguments)
    in_file = arguments["--file"]
    ipattern= []
    # ifile = os.environ.get('INCLUDE_FILES',include_paths(arguments["--include"]))
    ipattern = include_paths(arguments["--include"])
    opattern = exclude_paths(arguments["--exclude"])
    url = os.environ.get('GITLAB_URL', arguments["--gitlab"])
    token = os.environ.get('GITLAB_TOKEN', arguments["--token"])
    
    gitlab = auth_gitlab(url, token)
    arguments["gitlab"]  = gitlab
    arguments["token"]  = token
    arguments["url_base"]  = url
    tree = Tree(url, gitlab, includes=ipattern, excludes=opattern, concurrency=int(
        arguments["--concurrency"]), in_file=in_file, method=arguments["--method"])
    log.debug("Reading projects tree from gitlab at [{url}]".format(
        url=url))
    tree.load_tree()
    if tree.is_empty():
        log.fatal("The tree is empty, check your include/exclude patterns")
        sys.exit(1)

    if arguments["--dry-run"]:
        tree.print_tree(arguments["--format"])
    else:
        if arguments["branch"]:
            tree.sync_tree("branch", arguments)
        if arguments["clone"]:
            tree.sync_tree("clone", arguments)
        if arguments["plugins"]:
            tree.sync_tree("plugins", arguments)
