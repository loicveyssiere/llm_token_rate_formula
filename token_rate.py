import timeit
import logging
import json
import argparse
import http.client
import urllib.parse
import os.path

import tqdm
from langchain_community.llms.ollama import Ollama

logging.basicConfig(encoding="utf-8", level=logging.INFO)


def main():
    output = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="bonjour, raconte-moi une courte histoire", type=str, help="Input prompt to run the model", nargs='?')
    parser.add_argument("--loops", default=10, type=int, help="number of loops for performance testing", nargs='?')
    parser.add_argument("--base_url", default="http://localhost:11434", type=str, help="Ollama server url", nargs='?')
    parser.add_argument("--model", default="llama3", type=str, help="The LLM model", nargs='?')
    parser.add_argument("--output", default="output/", type=str, help="The output path", nargs='?')
    config = parser.parse_args()

    model_info = prepare_ollama(config.base_url, config.model)
    
    if model_info is None:
        logging.error("Impossible to contact and prepare Ollama")
        return
    else:
        del model_info["license"]
        del model_info["modelfile"]
        output["model_info"] = model_info

    ollama_agent = OllamaAgent(base_url=config.base_url, model=config.model)

    # Warmup and visualisation for Ollama
    for t in ollama_agent.predict(config.query): print(t, end='', flush=True)

    output["gpu_info_warmup"] = gpu_info()
    results = ollama_agent.performances(config.query, loops=config.loops)
    output["gpu_info_done"] = gpu_info()

    output["model"] = config.model
    output["results"] = results    

    print(json.dumps(output))
    with open(f"output/test.json", "w") as file:
        json.dump(output, file, indent=2)
    
    
def gpu_info():
    gpu_info=None
    try:
        import nvidia_smi
        gpu_info = {}
        nvidia_smi.nvmlInit()
        nvidia_smi.nvmlDeviceGetCount()
        handle = nvidia_smi.nvmlDeviceGetHandleByIndex(0)
        gpu_info["name"] = nvidia_smi.nvmlDeviceGetName(handle).decode('utf-8')
        memory = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
        gpu_info["total_memory"] = memory.total
        gpu_info["used_memory"] = memory.used
        gpu_info["free_memory"] = memory.free
        utilization = nvidia_smi.nvmlDeviceGetUtilizationRates(handle)
        gpu_info["gpu_utilization"] = utilization.gpu
        gpu_info["memory_utilization"] = utilization.memory
        
        gpu_info["driver_version"] = nvidia_smi.nvmlSystemGetDriverVersion().decode('utf-8')
        gpu_info["graphics_clock"] = nvidia_smi.nvmlDeviceGetClockInfo(handle, nvidia_smi.NVML_CLOCK_GRAPHICS)
        gpu_info["memory_clock"] = nvidia_smi.nvmlDeviceGetClockInfo(handle, nvidia_smi.NVML_CLOCK_MEM)
        gpu_info["pci_id"] = nvidia_smi.nvmlDeviceGetPciInfo(handle).busId.decode('utf-8')
        gpu_info["pci_speed"] = nvidia_smi.nvmlDeviceGetCurrPcieLinkGeneration(handle)
        gpu_info["pci_width"] = nvidia_smi.nvmlDeviceGetCurrPcieLinkWidth(handle)
        
    except nvidia_smi.NVMLError as error:
        logging.error(error)
    return gpu_info

def prepare_ollama(base_url, model):
    url_parsed = urllib.parse.urlparse(base_url)
    print(url_parsed.netloc)
    connection = http.client.HTTPConnection(url_parsed.netloc)
    connection.request("POST", "/api/pull", body=json.dumps({"name": model}), headers={'Content-Type': 'application/json'})
    response = connection.getresponse()
    response.read()
    if response.status != 200:
        logging.error(f"Impossible to pull model {model}, status_code {response.status}")
        return None
    else:
        logging.info(f"Ollama Pull success for model {model}")
    connection.request("POST", "/api/show", body=json.dumps({"name": model}))
    response = connection.getresponse()
    if response.status != 200:
        logging.error(f"Impossible to show model {model}, status_code {response.status}")
        return None
    else:
        logging.info(f"Ollama Show success for model {model}")
    
    model_info = response.read()
    connection.close()
    return json.loads(model_info)

class Agent:

    DEFAULT_SYSTEM_PROMPT = " \
Tu es un assistant respectueux et honnête. \
Réponds toujours de façon précise et concise. Tu répondras toujours en français. \
Si une question n'a pas de sens ou n'est pas cohérente, explique pourquoi à la place de répondre de façon incorrect. \
Si tu ne connais pas la réponse, soit honnête et ne donne pas une fausse réponse."

    PROMPT_TEMPLATE = """
    <|begin_of_text|><|start_header_id|>system<|end_header_id|>{system_prompt}<|eot_id|>
    <|start_header_id|>user<|end_header_id|>{user_query}<|eot_id|>
    <|start_header_id|>assistant<|end_header_id|>
    """

    def get_prompt(self, query: str):
        return self.PROMPT_TEMPLATE.format(
            system_prompt=self.DEFAULT_SYSTEM_PROMPT,
            user_query=query
        )

    def predict(self, query: str): ...

    def performances(self, query, loops=1):
        tokens = 0
        total_timer = 0
        details = []
        for i in tqdm.tqdm(range(loops)):
            nb_tokens, timer = self.predict_and_time(query)
            tokens += nb_tokens
            total_timer += timer
            details.append({
                "nb_tokens": nb_tokens,
                "timer": timer,
                "per_sec": nb_tokens / timer
            })
        logging.info(
            f"Performance: Token per seconds : {tokens / total_timer:.1f}, Time per token: {total_timer / tokens * 1000:.1f} milliseconds,  (Total of {total_timer:.1f} seconds for {tokens} tokens)"
        )
        return {
            "details": details,
            "summary": {
                "nb_tokens": tokens,
                "timer": total_timer,
                "per_sec": tokens / total_timer
            }
        }

    def predict_and_time(self, query: str, debug=False):
        start_time = timeit.default_timer()
        response = list(self.predict(query))
        end_time = timeit.default_timer()
        time_response = end_time - start_time

        num_tokens = len(response)

        return num_tokens, time_response
    
class OllamaAgent(Agent):
    def __init__(self, model="llama3", base_url="http://localhost:11434") -> None:
        logging.info(f"Initializing Ollama with {model} model")
        self.model = Ollama(model=model, base_url=base_url)

    def predict(self, query: str):
        prompt = self.get_prompt(query)
        for item in self.model.stream(prompt):
            yield item

if __name__ == "__main__":
    main()