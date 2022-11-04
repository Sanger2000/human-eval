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

    with requests.Session() as session:
        result = session.post(
            'https://api.openai.com/v1/completions',
            headers=HEADERS,
            json={
                "prompt": prompt,
                "model": model,
                "max_tokens": 256,
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
    out_file = OUT_FILE.format(model, num_tries) + "full.json"

    pass_1 = OUT_FILE.format(model, 1)
    pass_10 = OUT_FILE.format(model, 10)
    pass_100 = OUT_FILE.format(model, 100)

    with open(out_file, 'w') as f:
        pass
    with open(pass_1, 'w') as f:
        pass
    with open(pass_10, 'w') as f:
        pass
    with open(pass_100, 'w') as f:
        pass

    out_f = open(out_file, 'a')
    pass_1_f = open(pass_1, 'a')
    pass_10_f = open(pass_10, 'a')
    pass_100_f = open(pass_100, 'a')

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

        """
        num_requests = 0
        start_time = time.time()
        for idx, comp_time in list(enumerate(completion_times))[::-1]:
            if start_time - comp_time > 60:
                del completion_times[idx]
            else:
                num_requests += 1

        if num_requests >= 15:
            # Sleep until we have less than 19 requests in the last minute
            #time.sleep(60 - (time.time() - completion_times[0]))
        """
        time.sleep(max(1, 4-(time.time() - start)))

        for idx, completion in enumerate(completions):
            out = {'task_id': task_id, 'completion': completion}

            if idx == 0:
                pass_1_f.write(json.dumps(out) + '\n')

            if idx < 10 and num_tries >= 10:
                pass_10_f.write(json.dumps(out) + '\n')

            if idx < 100 and num_tries >= 100:
                pass_100_f.write(json.dumps(out) + '\n')

            out_f.write(json.dumps(out) + '\n')





    # for future in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
        # task_id, prompt, completions = await future
    # for task_id, prompt, completions in tasks:


if __name__ == '__main__':
    get_results()
    #asyncio.run(get_results())
