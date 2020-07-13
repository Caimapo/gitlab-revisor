"""Gitlab .

Usage:
  pipeline-revision.py <gitlab-url> [options] <dest>
  pipeline-revision.py [options] <dest>

Options:
  -h --help                  Show this screen.
  -v --version               Show version.
  -t --token=<access_token>  Token access to gitlab instance.
  -i --include=<csl>         Included files in a comma separated string [default: 1c].
  -e --exclude=<csl>         Excluded files in a comma separated string. [default: 1c].
  -c --concurrency=<number of workers>      Number of workers[default: 1].
  -f --file=<file>           File previous input, this should be yaml format
  --format=<format>          Format of the output {yaml, json, tree} [default: yaml].
  -m --method=<method>       Method of clone {ssh, http} [default: http]
  --dry-run                  
  -a --action=<action>       Action to apply in batch to the gitlab instance [default: print]

"""
from docopt import docopt
import logging
import logging.handlers
from tree import GitlabTree
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)


def split(list):
    return list.split(",") if list != "1c" else None


if __name__ == '__main__':
    arguments = docopt(__doc__, version='revisor v 0.0.1')
    in_file = arguments["--file"]
    ipattern = split(arguments["--include"])
    opattern = split(arguments["--exclude"])
    url = os.environ.get('GITLAB_URL', arguments["<gitlab-url>"])
    token = os.environ.get('GITLAB_TOKEN', arguments["--token"])
    tree = GitlabTree(url, token, includes=ipattern, excludes=opattern, concurrency=int(
        arguments["--concurrency"]), in_file=in_file, method=arguments["--method"])
    log.debug("Reading projects tree from gitlab at [{url}]".format(
        url=arguments["<gitlab-url>"]))
    tree.load_tree()
    if tree.is_empty():
        log.fatal("The tree is empty, check your include/exclude patterns")
        sys.exit(1)

    if arguments["--dry-run"]:
        tree.print_tree(arguments["--format"])
    else:
        tree.sync_tree(arguments["--action"], arguments["<dest>"])
