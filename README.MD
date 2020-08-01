## Utilities for review of gitlab
---

The scope of this tool is to interact more naturally with a gitlab instance, where there are entire organizations and when auditing what and where thing exists it becomes chaotic to use the web interface.

---

* Usage:
  pipeline-revision.py [options] branch (--list | (--create --name=<branch_name> --ref=<branch_ref>) | --remove --name=<branch_name>)  
  pipeline-revision.py [options] clone <path>  
  pipeline-revision.py [options] plugins [--sast | --dependency-check | --detect-secrets] [ --recursive ]  

* Options:  
  -h --help                  Show this screen.  
  -v --version               Show version.  
  -g --gitlab=<gitlab>       URL to gitlab instance.  
  -t --token=<access_token>  Token access to gitlab instance.  
  -i --include=<csl>         Included files in a comma separated string [default: 1c].  
  -e --exclude=<csl>         Excluded files in a comma separated string. [default: 1c].  
  -c --concurrency=<number of workers>      Number of workers[default: 1].  
  -f --file=<file>           File previous input, this should be yaml format  
  --format=<format>          Format of the output {yaml, json, tree} [default: yaml].  
  -m --method=<method>       Method of clone {ssh, http} [default: http]  
  --dry-run                  
  -r --recursive            Recursive pipeline inspector


* Actions
  * Plugins  
    - [ ] add
      - [ ] dependency check
      - [x] sast
      - [ ] container scan
      - [ ] detect-secrets
    - [x] check
    - [ ] list
    - [ ] recursive check or list
  * Clone
  * Branch
    - [x] list
    - [x] create
    - [x] delete


* ToDo
 * review the branch creation process, because it is done only on the remote and this will immediately trigger a pipeline if the CI file is badly created
 * Get the lang of the repository
 * Scoring the best practices of the .gitlab-ci.yml