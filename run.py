"""
Runs the human eval dataset through code-davinci for a pass@k evaluation."""

#import aiohttp
import requests
import asyncio
import json
import tqdm
import time
import os

from dotenv import load_dotenv

load_dotenv()

HEADERS = {
    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
    "Content-Type": "application/json",
}

HUMAN_EVAL = os.environ['PWD'] + '/data/HumanEval.jsonl'
OUT_FILE = os.environ['PWD'] + '/data/results_{}_{}.jsonl'

def get_completion(prompt, num_tries=1, model='code-davinci-002', num_errors=0):
    if num_tries == 1:
        temperature = 0.2
    elif num_tries == 10:
        temperature = 0.6
    elif num_tries == 100:
        temperature = 0.8
    else:
        raise ValueError("num_tries must be 1, 10, or 100")

    print('temp', temperature)
    print('num tries', num_tries)

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
                time.sleep(30)
                return get_completion(prompt, num_tries, model, num_errors+1)




def iter_hval():
    out = []
    with open(HUMAN_EVAL) as f:
        for line in f:
            out.append(json.loads(line))
    return out

def get_results(num_tries=10, model='code-davinci-002'):
    out_file = OUT_FILE.format(model, num_tries)

    with open(out_file, 'w') as f:
        pass
    out_f = open(out_file, 'a')

    def wrapped_future(tid, prompt, future):
        return tid, prompt, future

    tasks = []
    completion_times = []
    for line in tqdm.tqdm(iter_hval()):
        start = time.time()

        prompt = line['prompt']
        task_id = line['task_id']
        # future = get_completion(semaphore, prompt, num_tries=num_tries, model=model)
        completions = get_completion(prompt, num_tries=num_tries, model=model)
        completion_times.append(time.time())

        tasks.append((task_id, prompt, completions))
        # tasks.append(wrapped_future(task_id, prompt, future))

        time.sleep(max(1, 4-(time.time() - start)))

        for idx, completion in enumerate(completions):
            out = {'task_id': task_id, 'completion': completion}
            out_f.write(json.dumps(out) + '\n')



if __name__ == '__main__':
    #get_results(num_tries=10)
    get_results(num_tries=1)
    #get_results(num_tries=100)
    #asyncio.run(get_results())
