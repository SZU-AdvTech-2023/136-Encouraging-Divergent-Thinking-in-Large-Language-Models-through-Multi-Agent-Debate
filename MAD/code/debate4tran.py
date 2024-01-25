"""
MAD: Multi-Agent Debate with Large Language Models
Copyright (C) 2023  The MAD Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import os
import json
import random
# random.seed(0)
import argparse
from langcodes import Language
from utils.agent import Agent
from datetime import datetime
from tqdm import tqdm
import logging
import multiprocessing
from typing import Dict
from func_timeout import func_timeout, FunctionTimedOut
import sys
import re
sys.path.append('/public14_data/wzy2023/OpenAI-Parallel-Toolkit') 
import json
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from threading import Lock
from typing import Dict, Optional, Tuple

from openai_parallel_toolkit.utils.logger import LOG_LABEL, Logger
from openai_parallel_toolkit.utils.process_bar import ProgressBar
from openai_parallel_toolkit.api.keys import KeyManager
from openai_parallel_toolkit.api.model import OpenAIModel, Prompt


NAME_LIST=[
    "Affirmative side",
    "Negative side",
    "Moderator",
]

class DebatePlayer(Agent):
    def __init__(self, model_name: str, name: str, temperature:float, openai_api_key: str, sleep_time: float) -> None:
        """Create a player in the debate

        Args:
            model_name(str): model name
            name (str): name of this player
            temperature (float): higher values make the output more random, while lower values make it more focused and deterministic
            openai_api_key (str): As the parameter name suggests
            sleep_time (float): sleep because of rate limits
        """
        super(DebatePlayer, self).__init__(model_name, name, temperature, sleep_time)
        self.openai_api_key = openai_api_key


class Debate:
    def __init__(self,
            model_name: str='gpt-3.5-turbo-16k', 
            temperature: float=0, 
            num_players: int=3, 
            save_file_dir: str=None,
            openai_api_key: str=None,
            prompts_path: str=None,
            max_round: int=3,
            sleep_time: float=0
        ) -> None:
        """Create a debate

        Args:
            model_name (str): openai model name
            temperature (float): higher values make the output more random, while lower values make it more focused and deterministic
            num_players (int): num of players
            save_file_dir (str): dir path to json file
            openai_api_key (str): As the parameter name suggests
            prompts_path (str): prompts path (json file)
            max_round (int): maximum Rounds of Debate
            sleep_time (float): sleep because of rate limits
        """

        self.model_name = model_name
        self.temperature = temperature
        self.num_players = num_players
        self.save_file_dir = save_file_dir
        self.openai_api_key = openai_api_key
        self.max_round = max_round
        self.sleep_time = sleep_time
        self.prompts_path = prompts_path
        print(f"mypromt ------- {prompts_path}")

        # init save file
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H:%M:%S")
        self.save_file = {
            'start_time': current_time,
            'end_time': '',
            'model_name': model_name,
            'temperature': temperature,
            'num_players': num_players,
            'success': False,
            #"src_lng": "",
           ## "tgt_lng": "",
            'source': '',
            'reference': '',
            'base_SQL_query': '',
            "debate_SQL_query": '',
            "Reason": '',
            "Supported Side": '',
            'players': {},
        }
        prompts = json.load(open(prompts_path))
        self.save_file.update(prompts)
        self.init_prompt()

        if self.save_file['base_SQL_query'] == "":
            self.create_base()

        # creat&init agents
        self.creat_agents()
        self.init_agents()


    def init_prompt(self):
        def prompt_replace(key):
            #self.save_file[key] = self.save_file[key].replace("##src_lng##", self.save_file["src_lng"]).replace("##tgt_lng##", self.save_file["tgt_lng"]).replace("##source##", self.save_file["source"]).replace("##base_SQL_query##", self.save_file["base_SQL_query"])
            self.save_file[key] = self.save_file[key].replace("##source##", self.save_file["source"]).replace("##base_SQL_query##", self.save_file["base_SQL_query"])

        prompt_replace("base_prompt")
        prompt_replace("player_meta_prompt")
        prompt_replace("moderator_meta_prompt")
        prompt_replace("judge_prompt_last2")

    def create_base(self):
        pattern = r'\/(\d+)-'
        match = re.search(pattern, self.prompts_path)
        if match:
            extracted_id = match.group(1)
        else:
            extracted_id = 2000 
        print(f"start creat {extracted_id}")
        source = self.save_file['source']
        last_20_chars = source[-50:]
        print(f"\n===== Translation Task {extracted_id}=====\n{last_20_chars}\n")
        agent = DebatePlayer(model_name=self.model_name, name='Baseline', temperature=self.temperature, openai_api_key=self.openai_api_key, sleep_time=self.sleep_time)
        agent.add_event(self.save_file['source'])
        #agent.set_meta_prompt(self.save_file['base_prompt'])
        base_SQL_query = agent.ask()
        agent.add_memory(base_SQL_query)
        self.save_file['base_SQL_query'] = base_SQL_query
        self.save_file['affirmative_prompt'] = self.save_file['affirmative_prompt'].replace("##base_SQL_query##", base_SQL_query)
        self.save_file['players'][agent.name] = agent.memory_lst
        print(f"end creat {extracted_id}")


    def creat_agents(self):
        # creates players
        self.players = [
            DebatePlayer(model_name=self.model_name, name=name, temperature=self.temperature, openai_api_key=self.openai_api_key, sleep_time=self.sleep_time) for name in NAME_LIST
        ]
        self.affirmative = self.players[0]
        self.negative = self.players[1]
        self.moderator = self.players[2]

    def init_agents(self):
        pattern = r'\/(\d+)-'
        match = re.search(pattern, self.prompts_path)
        if match:
            extracted_id = match.group(1)
        else:
           extracted_id = 2000 
        print(f"start init {extracted_id}")
        # start: set meta prompt
        self.affirmative.set_meta_prompt(self.save_file['player_meta_prompt'])
        self.negative.set_meta_prompt(self.save_file['player_meta_prompt'])
        self.moderator.set_meta_prompt(self.save_file['moderator_meta_prompt'])
        
        # start: first round debate, state opinions
        

        
        print(f"===== Debate Round-1 {extracted_id}=====\n")
        self.affirmative.add_event(self.save_file['affirmative_prompt'])
        self.aff_ans = self.affirmative.ask()
        self.affirmative.add_memory(self.aff_ans)

        self.negative.add_event(self.save_file['negative_prompt'].replace('##aff_ans##', self.aff_ans))
        self.neg_ans = self.negative.ask()
        self.negative.add_memory(self.neg_ans)

        self.moderator.add_event(self.save_file['moderator_prompt'].replace('##aff_ans##', self.aff_ans).replace('##neg_ans##', self.neg_ans).replace('##round##', 'first'))
        self.mod_ans = self.moderator.ask()
        self.moderator.add_memory(self.mod_ans)
        self.mod_ans = eval(self.mod_ans)
        print(f"end init {extracted_id}")

    def round_dct(self, num: int):
        dct = {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth', 6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth'
        }
        return dct[num]
            
    def save_file_to_json(self, id):
        now = datetime.now()
        current_time = now.strftime("%Y-%m-%d_%H:%M:%S")
        save_file_path = os.path.join(self.save_file_dir, f"{id}.json")
        
        self.save_file['end_time'] = current_time
        json_str = json.dumps(self.save_file, ensure_ascii=False, indent=4)
        with open(save_file_path, 'w') as f:
            f.write(json_str)

    def broadcast(self, msg: str):
        """Broadcast a message to all players. 
        Typical use is for the host to announce public information

        Args:
            msg (str): the message
        """
        # print(msg)
        for player in self.players:
            player.add_event(msg)

    def speak(self, speaker: str, msg: str):
        """The speaker broadcast a message to all other players. 

        Args:
            speaker (str): name of the speaker
            msg (str): the message
        """
        if not msg.startswith(f"{speaker}: "):
            msg = f"{speaker}: {msg}"
        # print(msg)
        for player in self.players:
            if player.name != speaker:
                player.add_event(msg)

    def ask_and_speak(self, player: DebatePlayer):
        ans = player.ask()
        player.add_memory(ans)
        self.speak(player.name, ans)


    def run(self):

        for round in range(self.max_round - 1):

            if self.mod_ans["debate_SQL_query"] != '':
                break
            else:
                print(f"===== Debate Round-{round+2} =====\n")
                self.affirmative.add_event(self.save_file['debate_prompt'].replace('##oppo_ans##', self.neg_ans))
                self.aff_ans = self.affirmative.ask()
                self.affirmative.add_memory(self.aff_ans)

                self.negative.add_event(self.save_file['debate_prompt'].replace('##oppo_ans##', self.aff_ans))
                self.neg_ans = self.negative.ask()
                self.negative.add_memory(self.neg_ans)

                self.moderator.add_event(self.save_file['moderator_prompt'].replace('##aff_ans##', self.aff_ans).replace('##neg_ans##', self.neg_ans).replace('##round##', self.round_dct(round+2)))
                self.mod_ans = self.moderator.ask()
                self.moderator.add_memory(self.mod_ans)
                self.mod_ans = eval(self.mod_ans)

        if self.mod_ans["debate_SQL_query"] != '':
            self.save_file.update(self.mod_ans)
            self.save_file['success'] = True

        # ultimate deadly technique.
        else:
            judge_player = DebatePlayer(model_name=self.model_name, name='Judge', temperature=self.temperature, openai_api_key=self.openai_api_key, sleep_time=self.sleep_time)
            aff_ans = self.affirmative.memory_lst[2]['content']
            neg_ans = self.negative.memory_lst[2]['content']

            judge_player.set_meta_prompt(self.save_file['moderator_meta_prompt'])

            # extract answer candidates
            judge_player.add_event(self.save_file['judge_prompt_last1'].replace('##aff_ans##', aff_ans).replace('##neg_ans##', neg_ans))
            ans = judge_player.ask()
            judge_player.add_memory(ans)

            # select one from the candidates
            judge_player.add_event(self.save_file['judge_prompt_last2'])
            ans = judge_player.ask()
            judge_player.add_memory(ans)
            
            ans = eval(ans)
            if ans["debate_SQL_query"] != '':
                self.save_file['success'] = True
                # save file
            self.save_file.update(ans)
            self.players.append(judge_player)

        for player in self.players:
            self.save_file['players'][player.name] = player.memory_lst


def parse_args():
    parser = argparse.ArgumentParser("", formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-i", "--input-file", type=str, required=True, help="Input file path")
    parser.add_argument("-o", "--output-dir", type=str, required=True, help="Output file dir")
    #parser.add_argument("-lp", "--lang-pair", type=str, required=True, help="Language pair")
    parser.add_argument("-k", "--api-key", type=str, required=True, help="OpenAI api key")
    parser.add_argument("-m", "--model-name", type=str, default="gpt-3.5-turbo-16k", help="Model name")
    parser.add_argument("-t", "--temperature", type=float, default=0, help="Sampling temperature")

    return parser.parse_args()


if __name__ == "__main__" :
    Optional[str]
    args = parse_args()
    openai_api_key = args.api_key


    #key_manager = KeyManager(config_path="/public14_data/qth/chatgpt_test/config.json")
    key_manager = KeyManager(config_path="/public14_data/qth/chatgpt_test/config.json")
    
    logger = Logger(level=logging.WARNING)
    threads = multiprocessing.cpu_count()
    max_retries = 10

    #openai_api_key = key_manager.get_new_key()
    #completion = None  # Initialize the completion variable
   #attempts = 0  # Initialize attempts


    current_script_path = os.path.abspath(__file__)
    MAD_path = current_script_path.rsplit("/", 2)[0]

#    src_lng, tgt_lng = args.lang_pair.split('-')
#    src_full = Language.make(language=src_lng).display_name()
#    tgt_full = Language.make(language=tgt_lng).display_name()

    config = json.load(open(f"{MAD_path}/code/utils/config4tran.json", "r"))

    inputs = open(args.input_file, "r").readlines()
    inputs = [l.strip() for l in inputs]

    save_file_dir = args.output_dir
    if not os.path.exists(save_file_dir):
            os.mkdir(save_file_dir)

    #prompts_path = f"{save_file_dir}/{2000}-config4tran.json"

    def execute_model(openai_api_key, id, iput, prompts_path):
        
        debate = Debate(save_file_dir=save_file_dir, num_players=3, openai_api_key=openai_api_key, prompts_path=prompts_path, temperature=0, sleep_time=0)
        #print(f"-----------===== init-{id} =====\n")
        ###这一步可以try一try
        debate.run()
        #print(f"-----------===== run-{id} =====\n")
        debate.save_file_to_json(id)

    def request_openai_api(id, input, lock: Lock):
        openai_api_key = key_manager.get_new_key()
        completion = None  # Initialize the completion variable
        attempts = 0
        #for id, input in enumerate(tqdm(inputs)):
        # files = os.listdir(save_file_dir)
        # if f"{id}.json" in files:
        #     continue
        #print(id)
        #if id >= 377:
        prompts_path = f"{save_file_dir}/{id}-config4tran.json"
        
        
        
    #   config['reference'] = input.split('\t')[1]
    #    config['src_lng'] = src_full
    #    config['tgt_lng'] = tgt_full
        #last20input = "".join(input.split(" ")[-20:])
        #print(f"last20input---------------------------------------------------{id} - {last20input}\n")
        with lock:
            config['source'] = input
            with open(prompts_path, 'w') as file:
                #last20source = "".join(config['source'].split(" ")[-20:])
                #print(f"last20isource---------------------------------------------------{id} - {last20source}\n")
                json.dump(config, file, ensure_ascii=False, indent=4)
## 大概在这个地方，判断处理时间，超时换key，重新处理一遍
## 所以策略可以是
## 循环使用key，把所有key直接放sh里面，然后循环使用

        while attempts < max_retries:
            try:
            # Attempt to generate a completion
                print(prompts_path)
                res = func_timeout(500.0, execute_model,args=(openai_api_key, id, input, prompts_path,))

                logging.info(f"{LOG_LABEL}key {openai_api_key} ,request ok")
                key_manager.release_key(openai_api_key)
                res = 0
                break
            except FunctionTimedOut:
                #key_manager.remove_key(openai_api_key)
                key_manager.release_key(openai_api_key)
                openai_api_key = key_manager.get_new_key()
                logging.error(f"{LOG_LABEL}key {openai_api_key} ,request {attempts+1}timeout{id}")
                attempts += 1
                if attempts > 7:
                    res = 0
                    break
                continue
            except Exception as e:
            # Handle different types of errors
                if "exceeded your current quota" in str(e) or "<empty message>" in str(e) or "Limit: 200 / day" in str(e):
                # If the quota has been exceeded, remove the key and try again
                    key_manager.remove_key(openai_api_key)
                    openai_api_key = key_manager.get_new_key()
                    continue
                if "Limit: 3 / min" in str(e) or "Limit: 40000 / min" in str(e):
                # If the rate limit is hit, switch the API key and try again
                    openai_api_key = key_manager.get_new_key(openai_api_key)
                    continue
                if "less than the minimum of" in str(e):
                    # If the rate limit is hit, switch the API key and try again
                    logging.error(f"{id}Error occurred while accessing openai API: {e}")
                    key_manager.release_key(openai_api_key)
                    res = 0
                    break
                if "maximum context length" in str(e):
                # If the context length is too long, log an error and break the loop
                    logging.error(f"{LOG_LABEL}Error occurred while accessing openai API: {e}")
                    res = 0
                    break
                if "Max retries exceeded with url" in str(e):
                # If retries are exceeded, try again
                    continue
                if "That model is currently overloaded with other requests" in str(e):
                # If the model is overloaded, try again
                    continue
                if "The server is overloaded" in str(e):
                    continue
            # If an unknown error occurs, log an error and increment the attempt counter
                logging.error(
                        f"{LOG_LABEL}Unknown error occurred while accessing OpenAI API: {e}. Retry attempt {attempts + 1} "
                        f"of "
                        f"{max_retries}")
                attempts += 1

        #print(id,'down')
        #if not completion:
        #    return None

       # output = completion['choices'][0]['message']['content'].strip()
        return res

    def request_openai_api_with_tqdm(id, input, lock=Lock):
        result = request_openai_api(id = id, input = input, lock=lock)
        #if output_path: 
        #    with lock:
         #       with open(output_path, 'a', encoding='utf-8') as file:
        #            file.write(json.dumps({key: result}, ensure_ascii=False) + '\n')
        #            file.flush()
        #process_bar.update()
        return result

##todo 把上面request_openai_api里面的for循环提出来，以便于并行化
    def check_file_exists(id):
        file_path = f"/public14_data/wzy2023/Multi-Agents-Debate/data/SQL/output3/{id}.json"
        if os.path.exists(file_path):
            return True
    #def parallel_request_openai( ):
    lock = Lock()
    with ThreadPoolExecutor(max_workers=12) as executor:
        #request_openai_api_with_tqdm(id = id, input = input, prompts_path = prompts_path)
        results = []
        for id, input in enumerate(tqdm(inputs)):
            #prompts_path = f"{save_file_dir}/{id}-config4tran.json"
            #config['source'] = input
            #如果/public24_data/wzy2023/Multi-Agents-Debate/data/SQL/output1/{id}.json文件存在，则return
            #if id == 409:
            #    continue
            if check_file_exists(id):
                print(f"{id}.json文件已存在")
                continue
            else: 
                try:
                    result = executor.submit(request_openai_api_with_tqdm, id = id, input = input, lock=lock)
                    results.append(result)
                except Exception as e:
                    tb = traceback.format_exc()
                    #logging.error(f"{LOG_LABEL}Error occurred while processing prompt {prompts_path[0]}: {e}\n{tb}")

    # Wait for all tasks to complete, regardless of whether they were successful or not
    results = [future.result() for future in as_completed(results)]

        #return results

    
    #parallel_request_openai()

        

