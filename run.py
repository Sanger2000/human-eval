"""
Runs the human eval dataset through code-davinci for a pass@k evaluation.

Code is weird because I originally was using asyncio, then I got heavily
rate limited by OpenAI since Codex is in a free private beta. So I just
switched to making the requests sequentially and adding sleeps to prevent
rate-limits.

I didn't test pass@100 because I started running into the rate limit for
tokens/minute.

"""

# import aiohttp
# import asyncio
import json
import os
import re
import requests
import tqdm
import time

from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
    "Content-Type": "application/json",
}

HUMAN_EVAL = os.environ['PWD'] + '/data/HumanEval.jsonl'
OUT_FILE = os.environ['PWD'] + '/data/results-{}-{}.jsonl'

def get_completion(prompt, num_tries=1, model='code-davinci-002', num_errors=0):
    if num_tries == 1:
        temperature = 0.2
    elif num_tries == 10:
        temperature = 0.6
    elif num_tries == 100:
        temperature = 0.8
    else:
        raise ValueError("num_tries must be 1, 10, or 100")


    with requests.Session() as session:
        result = session.post(
            'https://api.openai.com/v1/completions',
            headers=HEADERS,
            json={
                "prompt": prompt,
                "model": model,
                "max_tokens": 512,
                "temperature": temperature,
                "n": num_tries,
            }
        )

        json_out = result.json()
        try:
            return [choice['text'] for choice in json_out['choices']]
        except:
            print(json_out)
            if num_errors == 2:
                raise
            else:
                time.sleep(30*(num_errors+1)+1)
                return get_completion(prompt, num_tries, model, num_errors+1)



def iter_hval():
    with open(HUMAN_EVAL) as f:
        for line in f:
            yield json.loads(line)

def get_results(num_tries=10, model='code-davinci-002'):
    out_file = OUT_FILE.format(model, num_tries)

    with open(out_file, 'w') as f:
        pass

    out_f = open(out_file, 'a')

    for line in tqdm.tqdm(iter_hval()):
        start = time.time()

        prompt = line['prompt']
        task_id = line['task_id']

        # Get list of completions with the right model and num tries
        completions = get_completion(prompt, num_tries=num_tries, model=model)

        # Stupid way to sleep because I keep getting rate limited
        time.sleep(max(1, 4-(time.time() - start)))

        for idx, completion in enumerate(completions):
            out = {'task_id': task_id, 'completion': completion}
            out_f.write(json.dumps(out) + '\n')

    out_f.close()


def remove_bloat(in_jsonl):
    new_results = []
    with open(in_jsonl, 'r') as f:
        for line in f:
            out = json.loads(line)
            new_completion = ''
            stop_token = re.search('\n\S', out['completion'])
            if stop_token:
                out['completion'] = out['completion'][:stop_token.start()]

            new_results.append(out)

    with open(in_jsonl, 'w') as f:
        for result in new_results:
            f.write(json.dumps(result) + '\n')

if __name__ == '__main__':
    #get_results(num_tries=10)
    #get_results(num_tries=1)
    #get_results(num_tries=100)
    remove_bloat('remote_data/results-code-davinci-002-1.jsonl')
