import logging
import os
import sys
import subprocess
import git
import yaml
import time
import csv
import random
import requests
from gitlab import Gitlab, GitlabError, GitlabAuthenticationError
from progress import ProgressBar
import concurrent.futures

log = logging.getLogger(__name__)

progress = ProgressBar('* syncing projects')
emo = ["\U0001F331",'\U0001F332', '\U0001F333', '\U0001F334', '\U0001F335','\U0001F33E', '\U0001F33F', '\U0001F340', '\U0001F341']
gitlab_keywords = ["image", "services", "stages", "types", "before_script", "after_script", "variables", "cache", "include" ]
class GitAction:
    def __init__(self, node, path, arguments):
        self.node = node
        self.path = path
        self.arguments = arguments


def sync_action(root, action, arguments, disable_progress=False):
    if not disable_progress:
        progress.init_progress(len(root.leaves))
    actions = get_git_actions(root, arguments["<path>"], arguments)
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(arguments["--concurrency"])) as executor:
        if action == 'plugins':
            executor.map(plugins_action, actions)
        if action == 'branch':
            executor.map(security_branch, actions)
        if action == 'clone':
            executor.map(clone_or_pull_project, actions)
        else:
            executor.map(PRINT, actions)

    elapsed = progress.finish_progress()
    log.debug("Syncing projects took [{}]".format(elapsed))

def PRINT():
    print("To do")

def get_git_actions(root, dest, arguments):
    actions = []
    for child in root.children:
        path = "{0}{1}".format(dest, child.root_path)
        if not os.path.exists(path):
            os.makedirs(path)
        if child.is_leaf:
            actions.append(GitAction(child, path, arguments))
        if not child.is_leaf:
            actions.extend(get_git_actions(child, dest, arguments))
    return actions

def is_git_repo(path):
    try:
        x = git.Repo(path).git_dir
        return True
    except git.InvalidGitRepositoryError:
        return False
    except Exception as e:
        log.info(e)
        log.info(sys.exc_info())    

def is_gitlab_project(node):
    return True if node.id > 0 else False

def plugins_action(action):
    if is_gitlab_project(action.node):
        gitlab = action.arguments["gitlab"]
        project = get_project(gitlab, action.node.id)
        branch = action.arguments["--name"]
        yaml_data = get_yaml(project, '.gitlab-ci.yml', branch)
        lang = get_lang(project, yaml_data)
        # print(lang)
        yaml_data = add_veracode(yaml_data, lang)
        dump_file=yaml.safe_dump(yaml_data, default_flow_style=False, sort_keys=False)
        try:
            print("project:\n- url: {url} \n- name: {name}\n- lang: \U0001F419 {lang}\n---".format(url = action.node.url, name=action.node.name, lang=lang))
        except:
            log.info(sys.exc_info())

        if(action.arguments["--output"] != None):
            log.debug("dumping to csv")
            dump_to_csv(project.name, action.arguments["--output"], action.node.url, lang, 'veracode')
        if(action.arguments["--check"] or action.arguments["--dry-run"]):
            print(dump_file)
            print("---")
        # if(action.arguments["--push"]):
        #     update_file(project, '.gitlab-ci.yml', dump_file, branch)
        time.sleep(int(action.arguments["--time"]))
        # plugins_find(yaml_data, action.path, "clair_analysis")

def security_branch(action):
    if is_gitlab_project(action.node):
        time.sleep(1)
        gitlab = action.arguments["gitlab"]
        log.debug("updating existing project {0}".format(action.path))
        project=get_project(gitlab, action.node.id)
        # print(action.arguments)

        if(action.arguments["--create"]):
            try:
                # check if pipeline should be create
                ref = action.arguments["--ref"]
                branch = action.arguments["--name"]
                ## ToDo
                check_ref_branch(project, ref)
                # crete branch
                time.sleep(1)
                # create_branch(project, branch, ref)
            except Exception as e:
                log.fatal("Error: {}".format(e))    

        if(action.arguments["--remove"]):
            try:
                delete_branch(project, branch)
            except Exception as e:
                log.fatal("Error: {}".format(e))
        
        if(action.arguments["--list"]):
            list_branches(project, True)

## ----------------------------------------------------------------------##
##                                                                       ##
## Helpers                                                               ##
##                                                                       ##
## ----------------------------------------------------------------------##

def dump_to_csv(project, path, url, lang, step):
    try:
      with open(path, newline='', mode='a') as file:
          writer = csv.writer(file, delimiter=',')
          writer.writerow([project, url, lang, step])
    except Exception as e:
        log.info("Error trying to openning the file output\nmsg:{}".format(sys.exc_info()))

def get_project(gitlab, id):
    try:
        project=gitlab.projects.get(id)
    except:
        log.info(sys.exc_info())
    return project

def list_branches(project, fig):
    try:
        log.debug("Listing branches in project {}".format(project.name))

        px = project.branches.list()
        print("---\nProject {}".format(project.name))
        smb = random.choices(emo, k=20) if fig else 20*['']
        [print("- {name} {symbol}".format(symbol=smb[i], name= branch.name)) for i,branch in enumerate(px)]
    except Exception as e:
        log.info(e)
        log.info(sys.exc_info())

def create_branch(project, branch_name, ref_name):
    try:
        project.branches.create({'branch': branch_name, 'ref': ref_name})
    except GitlabError:
        log.fatal("Branch error: {}".format(sys.exc_info()))
    except Exception as e:
        log.info(e)    

def delete_branch(project, branch_name):
    try:
        project.branches.delete(branch_name)
    except GitlabError:
        log.fatal("Branch error: {}".format(sys.exc_info()))
    except Exception as e:
        log.info(e)

def get_file(project, file_name, branch):
    try:
        log.debug(project.name)
        file_object=project.files.get(file_path=file_name, ref=branch)
        return file_object
    except:
        log.debug("Error get file")
        log.fatal("error : {}".format(sys.exc_info()))

def get_yaml(project, file_name, branch):
    file_object = get_file(project, file_name, branch)
    try:
        yaml_file = yaml.safe_load(file_object.decode().decode('utf-8'))
    except:
        log.debug(sys.exc_info())
    return yaml_file

def update_file(project, file_name, new_file, branch_name):
    try:
        log.info(project.name)
        file_object=project.files.get(file_path=file_name, ref=branch_name)
        file_object.content = new_file
        push_file(file_object, branch_name, file_name)
        log.info("Pushed file")
    except:
        log.debug("Error get file")
        log.fatal("error update file: {}".format(sys.exc_info()))

def push_file(file, branch, filename):
    try:
        file.save(branch=branch, commit_message="ci: add sec step {step} to {name} from revisor script".format(step="veracode" ,name=filename))
    except GitlabError:
        log.debug("[Failed to push the file] : {0}".format(sys.exc_info()))

def plugins_find(yaml_data, name, type_stage):
    print("Reviewing repository {0} \n".format(name))
    for stage_name in yaml_data:
        if(stage_name == "clair_analysis"):
            print(stage_name + " ✅")
        else:
            print(stage_name)
    print("\n ---")
    dump_file=yaml.safe_dump(
        yaml_file, default_flow_style=False, sort_keys=False)
    return dump_file

def check_ref_branch(project, ref):
    yaml_data = get_yaml(project, '.gitlab-ci.yml', ref)
    [print(stage) for stage in yaml_data]
    # for stage_name in yaml:
    #     print("Stage : {}".format(stage_name))
    #     for steps in yaml_data[stage_name]:
    #         print("-  Step: {}".format(steps))
    #         if(steps == 'only'):
    #             print("Stage {} has only {} ".format(stage_name,steps['only']))

def get_lang(project, yaml_file):
    try:
        lang = []
        lang_dict = project.languages()
        if(bool(lang_dict)):
            for lang_name, por in lang_dict.items():
                lang.append(lang_name)
            return lang[0]
        else:
            lang = yaml_file["variables"]
            flagj = False
            flagn = False
            for l,_ in lang.items():
                if "gradle" in l.lower():
                    flagj = True
                    flagn = False
                if "npm" in l.lower():
                    flagn = True
                    flagj = False
            
            if flagj:
                return 'Java'
            if flagn:
                return 'Node'    
            else:
                return "404notfound"
    except:
        log.info(sys.exc_info())

def modify_file_content(file_object, url):
    yaml_file=yaml.safe_load(file_object.decode().decode('utf-8'))
    print("\n")
    # if (yaml_file["include"][0]["file"] == "/all-in-one/all-cicd-javaGradle-whmg-on-prem.yml"):
    #     print("\n+{}".format(url))
    #     yaml_file=add_security_steps(yaml_file, 'java')

    # if (yaml_file["include"][0]["file"] == "/all-in-one/all-cicd-nodejs-npm-whmg-on-prem.yml"):
    #     print("\n+{}".format(url))
    #     yaml_file=add_security_steps(yaml_file, 'node')
    # if (yaml_file["include"][0]["file"] == "/all-in-one/all-cicd-nodejs-npm-whmg.yml"):
    #     print("\n+{}".format(url))
    #     yaml_file=add_security_steps(yaml_file, 'node')
    print("\n ---")
    yaml_file=add_security_steps(yaml_file, 'node')
    dump_file=yaml.safe_dump(
        yaml_file, default_flow_style=False, sort_keys=False)
    print(dump_file)
    print("\n ---")
    return dump_file

def print_file_content(file_object, url):
    yaml_file=yaml.safe_load(file_object.decode().decode('utf-8'))
    dump_file=yaml.safe_dump(
        yaml_file, default_flow_style=False, sort_keys=False)
    print(dump_file)
    print("\n ---")

def add_security_steps(data, lang):
    data["detect_secrets"]={
        'extends': '.detect_secrets_seecas',
        'variables': [
        {
            'SECAAS_PLUGIN_ID': '$SECAAS_PLUGIN_ID',
            'SECAAS_PLUGIN_SECRET': '$SECAAS_PLUGIN_SECRET',
            'BUSINESS': '$SECAAS_BUSINESS_ID',
        }
    ],
        'only': {
            'refs': ['devsecops']
        }
    }
    data["dependency_scanning"]={
    'extends': '.dependency_cli_secaas',
    'variables': [
        {
            'DC_TARGET_LANG': lang,
            'SECAAS_PLUGIN_ID': '$SECAAS_PLUGIN_ID',
            'SECAAS_PLUGIN_SECRET': '$SECAAS_PLUGIN_SECRET',
            'BUSINESS': '$SECAAS_BUSINESS_ID',
        }
    ],
    'only': {
        'refs': ['devsecops']
        }
    }
    data["sast_scanning"]={
    'extends': '.veracode_{lang}'.format(lang=lang),
    'variables': [{
            'DC_TARGET_LANG': lang,
            'VERSION': '$CI_PROJECT_NAME-$CI_PROJECT_NAMESPACE-$CI_JOB_ID',
            'SECAAS_PLUGIN_ID': '$SECAAS_PLUGIN_ID',
            'SECAAS_PLUGIN_SECRET': '$SECAAS_PLUGIN_SECRET',
            'BUSINESS': '$SECAAS_BUSINESS_ID',
            'SANDBOX_NAME': '${CI_PROJECT_NAME}-${CI_PROJECT_NAMESPACE}',
            'PROJECT': '${CI_PROJECT_NAME}-${CI_PROJECT_NAMESPACE}',
            'BRANCH': '$CI_COMMIT_REF_SLUG'
        }],
    'only': {
        'refs': ['devsecops']
        }
    }
    return data

def add_veracode(yaml_file, lang):
    yaml_file["include"].extend( [
             {'file': '/template/.ci-template.yml',
              'project': 'tech-corp/seguridad-de-la-informacion/ci-templates/veracode-plugin',
              'ref': 'v-2.0-19.6.5.8'}])
    # Deduplication of dictionaries              
    yaml_file["include"] = [dict(t) for t in {tuple(d.items()) for d in yaml_file["include"]}]
    # End deduplication of dictionaries

    if(lang.lower() == 'java'):
        yaml_file["veracode-analysis"]={
        'extends': '.veracode',
        'stage': 'test',
        'image': 'gcr.io/gsc-gitlab-ce/cicd/secaas/plugins/veracode-cli:v-2.0-19.6.5.8',
        'variables': {
                'FILE': 'build/libs/$APP_FULL_NAME',
            },
        'tags': ['docker'],
        'only': {
            'refs': ['devsecops']
            }
        }
    if(lang.lower() == 'node'):
        yaml_file["veracode-analysis"]={
        'extends': '.veracode-zip',
        'stage': 'test',
        'image': 'gcr.io/gsc-gitlab-ce/cicd/secaas/plugins/veracode-cli:v-2.0-19.6.5.8',
        'before_script': ['zip -r src.zip src/*'],
        'variables': {
                'FILE': 'src.zip',
            },
        'tags': ['docker'],
        'only': {
            'refs': ['devsecops']
            }
        }

    return yaml_file

def pull_project_ci_file(action):
    if is_git_repo(action.path):
        '''
        Update existing project
        '''
        log.debug("updating existing project {}".format(action.path))
        progress.show_progress(action.node.name, 'pull')
        try:
            repo=git.Repo(action.path)
            repo.remotes.origin.pull()
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error pulling project {}".format(
                action.path), exc_info=True)


def clone_or_pull_project(action):
    if is_git_repo(action.path):
        '''
        Update existing project
        '''
        log.debug("updating existing project {}".format(action.path))
        progress.show_progress(action.node.name, 'pull')
        try:
            repo=git.Repo(action.path)
            repo.remotes.origin.pull()
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error pulling project {}".format(
                action.path), exc_info=True)
    else:
        '''
        Clone new project
        '''
        log.debug("cloning new project {}".format(action.path))
        progress.show_progress(action.node.name, 'clone')
        try:
            git.Repo.clone_from(action.node.url, action.path)
        except KeyboardInterrupt:
            log.fatal("User interrupted")
            sys.exit(0)
        except Exception as e:
            log.debug("Error cloning project {}".format(
                action.path), exc_info=True)
