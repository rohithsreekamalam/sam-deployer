import json
import os
import time
import traceback
from pathlib import Path
from subprocess import PIPE, STDOUT, Popen
import shlex

import PySimpleGUI as sg

sg.theme("Reddit")

button_padding = (10,20)
button_size = (8,1)
title_font = ("Arial", 12, "bold")
text_size = 18
progress_text_size = 3
frame_size = (735,250)
deployer_config_file_path = f"sam_deployer.json"

progress_counter = 0
progress_bar_limit = 1

configuration_frame = [
    [
        sg.Text("Project Folder Path: ", font=title_font, size=text_size),
        sg.Input("", key='-PROJECT_BASE_PATH-', change_submits=True, size=50),
        sg.FolderBrowse("BROWSE", key='-PROJECT_BROWSE-', size=button_size, pad=button_padding),
        sg.Button('SAVE', size=button_size, pad=button_padding, key='-PROJECT_SAVE-'),
    ],
    [
        sg.Text("SAM Binary Path: ", font=title_font, size=text_size),
        sg.Input("", key='-SAM_PATH-', change_submits=True, size=50),
        sg.FileBrowse("BROWSE", key='-SAM_BROWSE-', size=button_size, pad=button_padding),
        sg.Button('SAVE', size=button_size, pad=button_padding, key='-SAM_CONFIG_SAVE-')
    ],
    [
        sg.Text("Environment: ", font=title_font, size=11),
        sg.Checkbox('Develop', key='-DEVELOP_RADIO-', default=True),
        sg.Checkbox('QA', key='-QA_RADIO-'),
        sg.Checkbox('Staging', key='-STAGING_RADIO-'),
        sg.Checkbox('Production', key='-PRODUCTION_RADIO-'),
        sg.Push(),
        sg.VerticalSeparator(),
        sg.Push(),
        sg.Checkbox('Receive Alerts', default=True, key='-IS_NOTIFY-', font=title_font),
        sg.Push(),
        sg.Button('DEPLOY', size=button_size, pad=button_padding, key='-DEPLOY_BUTTON-', button_color=("#FFFFFF", "#9C3E2B"))
    ]
]

progress_frame = [
    [sg.VPush()],
    [
        sg.Push(),
        sg.ProgressBar(progress_bar_limit, orientation='h', size=(60, 20), key='-PROGRESS_BAR-', visible=True),
        sg.Push()
        
    ],
    [
        sg.Push(),
        sg.Text("", key='-STATUS_TEXT-', font=("Courier", 10, "bold")),
        sg.Push()
    ],
    [
        sg.Push(),
        sg.Text("", key='-COMPLETE_TEXT-', text_color="green", font=title_font),
        sg.Push()
    ],
    [
        sg.Push(),
        sg.Text("", key='-FAILED_TEXT-', text_color="red", font=title_font),
        sg.Push()
    ],
    [sg.VPush()]
]
layout = [
    [
        sg.Frame('CONFIGURATION', configuration_frame, size=frame_size)
    ],
    [sg.VPush()],
    [ 
        sg.Frame('PROGRESS', progress_frame, size=frame_size)
    ],
    [sg.VPush()],
    [
        sg.Push(),
        sg.Text("SAM Deployer v2.0 | Developed by Rohith", font=("Arial", 10)),
        sg.Push()
    ]
]

window = sg.Window(
        "SAM Deployer v2.0", 
        layout, 
        finalize=True, 
        keep_on_top=True,
        resizable=False
    ).Finalize()
# window['-PROJECT_BASE_PATH-'].bind("<Return>", "_Enter")

progress_bar = window['-PROGRESS_BAR-']


def get_environment():
    """
    function to get environment
    """
    radio_map = {
        "-DEVELOP_RADIO-": "develop",
        "-QA_RADIO-": "qa",
        "-STAGING_RADIO-": "staging",
        "-PRODUCTION_RADIO-": "production",
    }
    return [radio_map[x] for x in values if x in radio_map.keys() and values[x]]
    

def read_config(data=None):
    """
    function to read config
    """
    try:
        with open(deployer_config_file_path, 'r') as config_file:
            data = json.load(config_file)
    except FileNotFoundError:
        window['-FAILED_TEXT-'].update("Default configurations not found, create new one!")
    return data if data else {}

def update_config(config):
    """
    function to update config
    """
    existing_data = read_config()
    with open(deployer_config_file_path, 'w+') as config_file:
        config_file.write(json.dumps({**existing_data, **config}, indent=4))

def run_generator(command):
    """
    function to run generator
    """
    process = Popen(command, stdout=PIPE, shell=True, stderr=STDOUT)
    while True:
        line = process.stdout.readline().strip()
        if not line:
            break
        yield line

def update_progress(message=None, final=False):
    """
    function to update progress counter
    """
    window['-STATUS_TEXT-'].update(message)
    global progress_counter, progress_bar_limit
    progress_counter += 1
    if final:
        progress_bar.UpdateBar(progress_bar_limit+1, progress_bar_limit)
    else:
        progress_bar.UpdateBar(progress_counter, progress_bar_limit)


sam_deployer_config = read_config()

window['-SAM_PATH-'].update(sam_deployer_config.get('sam_path'))
window['-PROJECT_BASE_PATH-'].update(sam_deployer_config.get('project_path'))

while True:
    event, values = window.read()

    if event==sg.WIN_CLOSED:
        break
    elif event=='-SAM_CONFIG_SAVE-':
        sam_path = values['-SAM_PATH-'].strip()
        if not sam_path.endswith("/sam"):
            print("[ERROR] Invalid path to SAM binaries!")
            continue
        config_content = {"sam_path": sam_path}
        update_config(config_content)
        window['-SAM_PATH-'].update(sam_path.strip())
        sam_deployer_config = read_config()
        window['-FAILED_TEXT-'].update("")
    elif event=='-PROJECT_SAVE-':
        project_path = values['-PROJECT_BASE_PATH-'].strip()
        config_content = {'project_path': project_path}
        update_config(config_content)
        window['-PROJECT_BASE_PATH-'].update(project_path)
        sam_deployer_config = read_config()
        window['-FAILED_TEXT-'].update("")
    elif event in ['-DEPLOY_BUTTON-']:#, "-PROJECT_BASE_PATH-_Enter"]:
        environment_list = get_environment()
        print("environment_list", environment_list)
        progress_bar_limit += len(environment_list)*6
        progress_bar.update(progress_bar_limit)

        update_progress("Initializing files")
        time.sleep(0.5)
        window['-COMPLETE_TEXT-'].update("")

        project_base_path = values['-PROJECT_BASE_PATH-'].strip()
        samconfig_path = f'{project_base_path}/samconfig.toml'
        template_path = f'{project_base_path}/template.yaml'
        if not Path(samconfig_path).is_file() or not Path(template_path).is_file():
            print("[ERROR] Selected project does not contain the required files!")
            window['-FAILED_TEXT-'].update("Please select a valid SAM project!")
            continue

        if not environment_list:
            print("[ERROR] No environments selected")
            window['-FAILED_TEXT-'].update("Please select at least one environment to deploy!")
            continue
        for environment in environment_list:
            display_environment = environment.title() if environment!="qa" else "QA"
            # window['-STOP_BUTTON-'].update(visible=True)

            #deployment logic
            initial_stage_command = f"""cat {project_base_path}/template.yaml | grep -P "^.*Default:\s*(\w*)" | sed 's/.*Default:\s*//g'"""
            initial_stage = os.popen(initial_stage_command).read()

            update_progress(f"Configuring SAM template for {display_environment}")
            time.sleep(0.5)
            samconfig_replace_command = f'sed -i "s/{initial_stage.strip()}/{environment}/g" {project_base_path}/samconfig.toml'
            samconfig_replace_exec = Popen(shlex.split(samconfig_replace_command))
            samconfig_replace_exec.wait()

            update_progress(f"Setting default environment for {display_environment}")
            time.sleep(0.5)
            template_replace_command = rf'sed -i "s/\(.*\Default:\s*\)\(\w*$\)/\1{environment}/g" {project_base_path}/template.yaml'
            template_replace_exec = Popen(shlex.split(template_replace_command))
            template_replace_exec.wait()

            if sam_deployer_config:
                try:
                    update_progress(f"[{display_environment.upper()}] Build in progress...")
                    # time.sleep(3)
                    os.chdir(project_base_path)
                    sam_build_command = rf'{sam_deployer_config["sam_path"]} build'
                    sam_build_exec = Popen(shlex.split(sam_build_command))
                    sam_build_exec.wait()

                    # time.sleep(0.5)
                    update_progress(f"[{display_environment.upper()}] Deployment in progress...")
                    # time.sleep(3)
                    sam_deploy_command = rf'cd {project_base_path} && {sam_deployer_config["sam_path"]} deploy'
                    sam_deploy_exec = Popen(shlex.split(sam_deploy_command))
                    sam_deploy_exec.wait()
                except Exception:
                    print(traceback.format_exc())
                    window['-FAILED_TEXT-'].update("Failed to deploy project!")
                    continue
            else:
                print("[ERROR] SAM PATH IS NOT CONFIGURED!")
                update_progress(f"[FAILED] | SAM Binaries are not configured!")
                window['-FAILED_TEXT-'].update("SAM Binaries are not configured!")
                continue
            
            if values['-IS_NOTIFY-']:
                update_progress("Alerting user")
                notify_command = f'notify-send "{display_environment} deployment completed"'
                notify_exec = Popen(shlex.split(notify_command))
                notify_exec.wait()
                time.sleep(1)
            update_progress(f"{display_environment} deployment complete!", final=True)
        window['-STATUS_TEXT-'].update("")
        window['-COMPLETE_TEXT-'].update(f"Deployment complete!")
        progress_counter = 0
        progress_bar_limit = 1

window.close()
