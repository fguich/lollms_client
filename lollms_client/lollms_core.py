import requests
from ascii_colors import ASCIIColors
from lollms_client.lollms_types import MSG_TYPE
from lollms_client.lollms_utilities import encode_image
import json
from enum import Enum
import tiktoken
import base64
import requests
import pipmaster as pm
from typing import List, Optional, Callable, Union

class ELF_GENERATION_FORMAT(Enum):
    LOLLMS = 0
    OPENAI = 1
    OLLAMA = 2
    LITELLM = 3
    TRANSFORMERS = 4

class ELF_COMPLETION_FORMAT(Enum):
    Instruct = 0
    Chat = 1

class LollmsClient():
    def __init__(
                    self, 
                    host_address="http://localhost:9600",
                    model_name=None,
                    ctx_size=4096,
                    personality=-1, 
                    n_predict=1024,
                    min_n_predict=512, 
                    temperature=0.1, 
                    top_k=50, 
                    top_p=0.95, 
                    repeat_penalty=0.8, 
                    repeat_last_n=40, 
                    seed=None, 
                    n_threads=8, 
                    service_key:str="",
                    tokenizer=None,
                    default_generation_mode=ELF_GENERATION_FORMAT.LOLLMS
                ) -> None:
        import tiktoken

        self.host_address=host_address
        self.model_name = model_name
        self.ctx_size = ctx_size
        self.n_predict = n_predict
        self.min_n_predict = min_n_predict
        self.personality = personality
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty
        self.repeat_last_n = repeat_last_n
        self.seed = seed
        self.n_threads = n_threads
        self.service_key = service_key
        self.default_generation_mode = default_generation_mode
        self.tokenizer = tiktoken.model.encoding_for_model("gpt-3.5-turbo-1106") if tokenizer is None else tokenizer
        if default_generation_mode == ELF_GENERATION_FORMAT.TRANSFORMERS:
            if not pm.is_installed("torch"):
                ASCIIColors.yellow("Diffusers: Torch not found. Installing it")
                pm.install_multiple(["torch","torchvision","torchaudio"], "https://download.pytorch.org/whl/cu121", force_reinstall=True)
            
            import torch
            if not torch.cuda.is_available():
                ASCIIColors.yellow("Diffusers: Torch not using cuda. Reinstalling it")
                pm.install_multiple(["torch","torchvision","torchaudio"], "https://download.pytorch.org/whl/cu121", force_reinstall=True)
                import torch
            
            if not pm.is_installed("transformers"):
                pm.install_or_update("transformers")
            from transformers import AutoModelForCausalLM, AutoTokenizer,   GenerationConfig  
            self.tokenizer = AutoTokenizer.from_pretrained(
                    str(model_name), trust_remote_code=False
                    )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                        str(model_name),
                        device_map="auto",
                        load_in_4bit=True,
                        torch_dtype=torch.bfloat16  # Load in float16 for quantization
                    )
            self.generation_config = GenerationConfig.from_pretrained(str(model_name))



    def tokenize(self, prompt:str):
        """
        Tokenizes the given prompt using the model's tokenizer.

        Args:
            prompt (str): The input prompt to be tokenized.

        Returns:
            list: A list of tokens representing the tokenized prompt.
        """
        tokens_list = self.tokenizer.encode(prompt)

        return tokens_list

    def detokenize(self, tokens_list:list):
        """
        Detokenizes the given list of tokens using the model's tokenizer.

        Args:
            tokens_list (list): A list of tokens to be detokenized.

        Returns:
            str: The detokenized text as a string.
        """
        text = self.tokenizer.decode(tokens_list)

        return text
    
    
    def generate_with_images(self, prompt, images, n_predict=None, stream=False, temperature=0.1, top_k=50, top_p=0.95, repeat_penalty=0.8, repeat_last_n=40, seed=None, n_threads=8, service_key:str="", streaming_callback=None):
        if self.default_generation_mode == ELF_GENERATION_FORMAT.LOLLMS:
            return self.lollms_generate_with_images(prompt, images, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, service_key, streaming_callback)
        elif self.default_generation_mode == ELF_GENERATION_FORMAT.OPENAI:
            return # To be implemented #self.openai_generate_with_images(prompt, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, ELF_COMPLETION_FORMAT.Instruct, service_key, streaming_callback)
        elif self.default_generation_mode == ELF_GENERATION_FORMAT.OLLAMA:
            return # To be implemented #self.ollama_generate_with_images(prompt, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, ELF_COMPLETION_FORMAT.Instruct, service_key, streaming_callback)
        elif self.default_generation_mode == ELF_GENERATION_FORMAT.LITELLM:
            return # To be implemented #self.litellm_generate_with_images(prompt, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, ELF_COMPLETION_FORMAT.Instruct, service_key, streaming_callback)


    def generate(self, prompt, n_predict=None, stream=False, temperature=0.1, top_k=50, top_p=0.95, repeat_penalty=0.8, repeat_last_n=40, seed=None, n_threads=8, service_key:str="", streaming_callback=None):
        if self.default_generation_mode == ELF_GENERATION_FORMAT.LOLLMS:
            return self.lollms_generate(prompt, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, service_key, streaming_callback)
        elif self.default_generation_mode == ELF_GENERATION_FORMAT.OPENAI:
            return self.openai_generate(prompt, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, ELF_COMPLETION_FORMAT.Instruct, service_key, streaming_callback)
        elif self.default_generation_mode == ELF_GENERATION_FORMAT.OLLAMA:
            return self.ollama_generate(prompt, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, ELF_COMPLETION_FORMAT.Instruct, service_key, streaming_callback)
        elif self.default_generation_mode == ELF_GENERATION_FORMAT.LITELLM:
            return self.litellm_generate(prompt, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, ELF_COMPLETION_FORMAT.Instruct, service_key, streaming_callback)
        elif self.default_generation_mode == ELF_GENERATION_FORMAT.TRANSFORMERS:
            return self.transformers_generate(prompt, self.host_address, self.model_name, -1, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, service_key, streaming_callback)


    def generate_text(self, prompt, host_address=None, model_name=None, personality=None, n_predict=None, stream=False, temperature=0.1, top_k=50, top_p=0.95, repeat_penalty=0.8, repeat_last_n=40, seed=None, n_threads=8, service_key:str="", streaming_callback=None):
        return self.lollms_generate(prompt, host_address, model_name, personality, n_predict, stream, temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads, service_key, streaming_callback)

    def lollms_generate(self, prompt, host_address=None, model_name=None, personality=None, n_predict=None, stream=False, temperature=0.1, top_k=50, top_p=0.95, repeat_penalty=0.8, repeat_last_n=40, seed=None, n_threads=8, service_key:str="", streaming_callback=None):
        # Set default values to instance variables if optional arguments are None
        host_address = host_address if host_address else self.host_address
        model_name = model_name if model_name else self.model_name
        n_predict = n_predict if n_predict else self.n_predict
        personality = personality if personality is not None else self.personality
        # Set temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads to the instance variables if they are not provided or None
        temperature = temperature if temperature is not None else self.temperature
        top_k = top_k if top_k is not None else self.top_k
        top_p = top_p if top_p is not None else self.top_p
        repeat_penalty = repeat_penalty if repeat_penalty is not None else self.repeat_penalty
        repeat_last_n = repeat_last_n if repeat_last_n is not None else self.repeat_last_n
        seed = seed or self.seed  # Use the instance seed if not provided
        n_threads = n_threads if n_threads else self.n_threads


        url = f"{host_address}/lollms_generate"
        if service_key!="":
            headers = {
                'Content-Type': 'application/json;',
                'Authorization': f'Bearer {service_key}',
            }
        else:
            headers = {
                'Content-Type': 'application/json',
            }
        data = {
            "prompt": prompt,
            "model_name": self.model_name,
            "personality": self.personality,
            "n_predict": n_predict,
            "stream": stream,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "repeat_penalty": repeat_penalty,
            "repeat_last_n": repeat_last_n,
            "seed": seed,
            "n_threads": n_threads
        }

        response = requests.post(url, json=data, headers=headers, stream=stream)
        if not stream:
            if response.status_code == 200:
                try:
                    text = response.text.strip().rstrip('!')
                    return text
                except Exception as ex:
                    return {"status": False, "error": str(ex)}
            else:
                return {"status": False, "error": response.text}
        else:
            text = ""
            if response.status_code==200:
                try:
                    for line in response.iter_lines():
                        chunk = line.decode("utf-8")
                        text += chunk
                        if streaming_callback:
                            streaming_callback(chunk, MSG_TYPE.MSG_TYPE_CHUNK)
                    return text.rstrip('!')
                except Exception as ex:
                    return {"status": False, "error": str(ex)}
            else:
                return {"status": False, "error": response.text}
            

    def lollms_generate_with_images(
        self,
        prompt: str,
        images: List[str],
        host_address: Optional[str] = None,
        model_name: Optional[str] = None,
        personality: Optional[str] = None,
        n_predict: Optional[int] = None,
        stream: bool = False,
        temperature: float = 0.1,
        top_k: int = 50,
        top_p: float = 0.95,
        repeat_penalty: float = 0.8,
        repeat_last_n: int = 40,
        seed: Optional[int] = None,
        n_threads: int = 8,
        service_key: str = "",
        streaming_callback: Optional[Callable[[str, int], None]] = None
    ) -> Union[str, dict]:
        """
        Generates text based on a prompt and a list of images using a specified model.

        Args:
            prompt (str): The text prompt to generate responses for.
            images (List[str]): A list of file paths to images to be included in the generation.
            host_address (Optional[str]): The host address for the service. Defaults to instance variable.
            model_name (Optional[str]): The model name to use. Defaults to instance variable.
            personality (Optional[str]): The personality setting for the generation. Defaults to instance variable.
            n_predict (Optional[int]): The number of tokens to predict. Defaults to instance variable.
            stream (bool): Whether to stream the response. Defaults to False.
            temperature (float): Sampling temperature. Defaults to 0.1.
            top_k (int): Top-k sampling parameter. Defaults to 50.
            top_p (float): Top-p (nucleus) sampling parameter. Defaults to 0.95.
            repeat_penalty (float): Penalty for repeating tokens. Defaults to 0.8.
            repeat_last_n (int): Number of last tokens to consider for repeat penalty. Defaults to 40.
            seed (Optional[int]): Random seed for generation. Defaults to instance variable.
            n_threads (int): Number of threads to use. Defaults to 8.
            service_key (str): Optional service key for authorization.
            streaming_callback (Optional[Callable[[str, int], None]]): Callback for streaming responses.

        Returns:
            Union[str, dict]: The generated text if not streaming, or a dictionary with status and error if applicable.
        """
        
        # Set default values to instance variables if optional arguments are None
        host_address = host_address if host_address else self.host_address
        model_name = model_name if model_name else self.model_name
        n_predict = n_predict if n_predict else self.n_predict
        personality = personality if personality is not None else self.personality
        
        # Set parameters to instance variables if they are not provided or None
        temperature = temperature if temperature is not None else self.temperature
        top_k = top_k if top_k is not None else self.top_k
        top_p = top_p if top_p is not None else self.top_p
        repeat_penalty = repeat_penalty if repeat_penalty is not None else self.repeat_penalty
        repeat_last_n = repeat_last_n if repeat_last_n is not None else self.repeat_last_n
        seed = seed or self.seed  # Use the instance seed if not provided
        n_threads = n_threads if n_threads else self.n_threads

        def encode_image_to_base64(image_path: str) -> str:
            """Encodes an image file to a base64 string."""
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            return encoded_string

        # Encode images in base64
        encoded_images = [encode_image_to_base64(image) for image in images]

        url = f"{host_address}/lollms_generate_with_images"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {service_key}' if service_key else '',
        }

        data = {
            "prompt": prompt,
            "model_name": model_name,
            "personality": personality,
            "n_predict": n_predict,
            "stream": stream,
            "temperature": temperature,
            "top_k": top_k,
            "top_p": top_p,
            "repeat_penalty": repeat_penalty,
            "repeat_last_n": repeat_last_n,
            "seed": seed,
            "n_threads": n_threads,
            "images": encoded_images  # Add encoded images to the request payload
        }

        response = requests.post(url, json=data, headers=headers, stream=stream)
        if not stream:
            if response.status_code == 200:
                try:
                    text = response.text.rstrip('!')
                    return text
                except Exception as ex:
                    return {"status": False, "error": str(ex)}
            else:
                return {"status": False, "error": response.text}
        else:
            text = ""
            if response.status_code == 200:
                try:
                    for line in response.iter_lines():
                        chunk = line.decode("utf-8")
                        text += chunk
                        if streaming_callback:
                            streaming_callback(chunk, MSG_TYPE.MSG_TYPE_CHUNK)
                    if text[0] == '"':
                        text = text[1:]
                    if text[-1] == '"':
                        text = text[:-1]
                    return text
                except Exception as ex:
                    return {"status": False, "error": str(ex)}
            else:
                return {"status": False, "error": response.text}

    
    def transformers_generate(self, prompt, host_address=None, model_name=None, personality=None, n_predict=None, stream=False, temperature=0.1, top_k=50, top_p=0.95, repeat_penalty=0.8, repeat_last_n=40, seed=None, n_threads=8, service_key:str="", streaming_callback=None):
        # Set default values to instance variables if optional arguments are None
        model_name = model_name if model_name else self.model_name
        n_predict = n_predict if n_predict else self.n_predict
        personality = personality if personality is not None else self.personality
        # Set temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads to the instance variables if they are not provided or None
        temperature = temperature if temperature is not None else self.temperature
        top_k = top_k if top_k is not None else self.top_k
        top_p = top_p if top_p is not None else self.top_p
        repeat_penalty = repeat_penalty if repeat_penalty is not None else self.repeat_penalty
        repeat_last_n = repeat_last_n if repeat_last_n is not None else self.repeat_last_n
        seed = seed or self.seed  # Use the instance seed if not provided
        n_threads = n_threads if n_threads else self.n_threads

        self.generation_config.max_new_tokens = int(n_predict)
        self.generation_config.temperature = float(temperature)
        self.generation_config.top_k = int(top_k)
        self.generation_config.top_p = float(top_p)
        self.generation_config.repetition_penalty = float(repeat_penalty)
        self.generation_config.do_sample = True if float(temperature)>0 else False
        self.generation_config.pad_token_id = self.tokenizer.pad_token_id
        self.generation_config.eos_token_id = self.tokenizer.eos_token_id
        self.generation_config.output_attentions = False

        try:
            input_ids = self.tokenizer(prompt, add_special_tokens=False, return_tensors='pt').input_ids.to(self.model_device)
            class StreamerClass:
                def __init__(self, callback):
                    self.output = ""
                    self.callback = callback
                def put(self, value):
                    """
                    Recives tokens, decodes them, and prints them to stdout as soon as they form entire words.
                    """
                    if len(value.shape)==1 and (value[0] == self.tokenizer.eos_token_id or value[0] == self.tokenizer.bos_token_id):
                        print("eos detected")
                        return
                    if len(value.shape) > 1 and value.shape[0] > 1:
                        raise ValueError("TextStreamer only supports batch size 1")
                    elif len(value.shape) > 1:
                        value = value[0]
                    
                    if self.skip_prompt and self.next_tokens_are_prompt:
                        self.next_tokens_are_prompt = False
                        return
                    
                    # Add the new token to the cache and decodes the entire thing.
                    self.token_cache.extend(value.tolist())
                    text = self.tokenizer.decode(self.token_cache, **self.decode_kwargs)
                    
                    # After the symbol for a new line, we flush the cache.
                    if text.endswith("\n"):
                        printable_text = text[self.print_len :]
                        self.token_cache = []
                        self.print_len = 0
                    # If the last token is a CJK character, we print the characters.
                    elif len(text) > 0 and self._is_chinese_char(ord(text[-1])):
                        printable_text = text[self.print_len :]
                        self.print_len += len(printable_text)
                    # Otherwise, prints until the last space char (simple heuristic to avoid printing incomplete words,
                    # which may change with the subsequent token -- there are probably smarter ways to do this!)
                    else:
                        printable_text = text[self.print_len : text.rfind(" ") + 1]
                        self.print_len += len(printable_text)
                    
                    self.output += printable_text
                    if  self.callback:
                        if not self.callback(printable_text, MSG_OPERATION_TYPE.MSG_OPERATION_TYPE_ADD_CHUNK):
                            raise Exception("canceled")    
                    
                    def _is_chinese_char(self, cp):
                        """Checks whether CP is the codepoint of a CJK character."""
                        # This defines a "chinese character" as anything in the CJK Unicode block:
                        #   https://en.wikipedia.org/wiki/CJK_Unified_Ideographs_(Unicode_block)
                        #
                        # Note that the CJK Unicode block is NOT all Japanese and Korean characters,
                        # despite its name. The modern Korean Hangul alphabet is a different block,
                        # as is Japanese Hiragana and Katakana. Those alphabets are used to write
                        # space-separated words, so they are not treated specially and handled
                        # like the all of the other languages.
                        if (
                            (cp >= 0x4E00 and cp <= 0x9FFF)
                            or (cp >= 0x3400 and cp <= 0x4DBF)  #
                            or (cp >= 0x20000 and cp <= 0x2A6DF)  #
                            or (cp >= 0x2A700 and cp <= 0x2B73F)  #
                            or (cp >= 0x2B740 and cp <= 0x2B81F)  #
                            or (cp >= 0x2B820 and cp <= 0x2CEAF)  #
                            or (cp >= 0xF900 and cp <= 0xFAFF)
                            or (cp >= 0x2F800 and cp <= 0x2FA1F)  #
                        ):  #
                            return True
                        
                        return False
                    def end(self):
                        """Flushes any remaining cache and prints a newline to stdout."""
                        # Flush the cache, if it exists
                        if len(self.token_cache) > 0:
                            text = self.tokenizer.decode(self.token_cache, **self.decode_kwargs)
                            printable_text = text[self.print_len :]
                            self.token_cache = []
                            self.print_len = 0
                        else:
                            printable_text = ""
                        
                        self.next_tokens_are_prompt = True
                        if  self.callback:
                            if self.callback(printable_text, 0):
                                raise Exception("canceled")    
            streamer = StreamerClass()
            self.model.generate(
                        inputs=input_ids, 
                        generation_config=self.generation_config,
                        streamer = streamer,
                        )
            return streamer.output.rstrip('!')
        except Exception as ex:
            return {"status": False, "error": str(ex)}
                
    def openai_generate(self, 
                        prompt, 
                        host_address=None, 
                        model_name=None, 
                        personality=None, 
                        n_predict=None, 
                        stream=False, 
                        temperature=0.1, 
                        top_k=50, 
                        top_p=0.95, 
                        repeat_penalty=0.8, 
                        repeat_last_n=40, 
                        seed=None, 
                        n_threads=8, 
                        completion_format: ELF_COMPLETION_FORMAT = ELF_COMPLETION_FORMAT.Instruct, 
                        service_key: str = "", 
                        streaming_callback=None):
        """
        Generates text using the OpenAI API based on the provided prompt and parameters.

        Parameters:
            prompt (str): The input text prompt to generate completions for.
            host_address (str, optional): The API host address. Defaults to instance variable.
            model_name (str, optional): The model to use for generation. Defaults to instance variable.
            personality (str, optional): The personality setting for the model. Defaults to instance variable.
            n_predict (int, optional): The number of tokens to predict. Defaults to instance variable.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            temperature (float, optional): Sampling temperature. Higher values mean more randomness. Defaults to 0.1.
            top_k (int, optional): The number of highest probability vocabulary tokens to keep for top-k filtering. Defaults to 50.
            top_p (float, optional): The cumulative probability of parameter options to keep for nucleus sampling. Defaults to 0.95.
            repeat_penalty (float, optional): The penalty for repeating tokens. Defaults to 0.8.
            repeat_last_n (int, optional): The number of last tokens to consider for repeat penalty. Defaults to 40.
            seed (int, optional): Random seed for reproducibility. Defaults to instance variable.
            n_threads (int, optional): The number of threads to use for generation. Defaults to 8.
            completion_format (ELF_COMPLETION_FORMAT, optional): The format of the completion request (Instruct or Chat). Defaults to ELF_COMPLETION_FORMAT.Instruct.
            service_key (str, optional): The API service key for authorization. Defaults to an empty string.
            streaming_callback (callable, optional): A callback function to handle streaming responses.

        Returns:
            str: The generated text response from the OpenAI API.
        """
        # Set default values to instance variables if optional arguments are None
        host_address = host_address if host_address else self.host_address
        model_name = model_name if model_name else self.model_name
        n_predict = n_predict if n_predict else self.n_predict
        personality = personality if personality is not None else self.personality
        # Set temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads to the instance variables if they are not provided or None
        temperature = temperature if temperature is not None else self.temperature
        top_k = top_k if top_k is not None else self.top_k
        top_p = top_p if top_p is not None else self.top_p
        repeat_penalty = repeat_penalty if repeat_penalty is not None else self.repeat_penalty
        repeat_last_n = repeat_last_n if repeat_last_n is not None else self.repeat_last_n
        seed = seed or self.seed  # Use the instance seed if not provided
        n_threads = n_threads if n_threads else self.n_threads

        if service_key != "":
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {service_key}',
            }
        else:
            headers = {
                'Content-Type': 'application/json',
            }

        if completion_format == ELF_COMPLETION_FORMAT.Instruct:
            data = {
                'model': model_name,  # self.config.model_name,
                'prompt': prompt,
                "stream": True,
                "temperature": float(temperature),
                "max_tokens": n_predict
            }
            completion_format_path = "/v1/completions"
        elif completion_format == ELF_COMPLETION_FORMAT.Chat:
            data = {
                'model': model_name,
                'messages': [{
                    'role': "user",
                    'content': prompt
                }],
                "stream": True,
                "temperature": float(temperature),
                "max_tokens": n_predict
            }
            completion_format_path = "/v1/chat/completions"

        if host_address.endswith("/"):
            host_address = host_address[:-1]
        url = f'{host_address}{completion_format_path}'

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 400:
            try:
                content = response.content.decode("utf8")
                content = json.loads(content)
                self.error(content["error"]["message"])
                return
            except:
                content = response.content.decode("utf8")
                content = json.loads(content)
                self.error(content["message"])
                return
        elif response.status_code == 404:
            ASCIIColors.error(response.content.decode("utf-8", errors='ignore'))
        
        text = ""
        for line in response.iter_lines():
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                try:
                    json_data = json.loads(decoded[5:].strip())
                    if completion_format == ELF_COMPLETION_FORMAT.Chat:
                        try:
                            chunk = json_data["choices"][0]["delta"]["content"]
                        except:
                            chunk = ""
                    else:
                        chunk = json_data["choices"][0]["text"]
                    # Process the JSON data here
                    text += chunk
                    if streaming_callback:
                        if not streaming_callback(chunk, MSG_TYPE.MSG_TYPE_CHUNK):
                            break
                except:
                    break
            else:
                if decoded.startswith("{"):
                    for line_ in response.iter_lines():
                        decoded += line_.decode("utf-8")
                    try:
                        json_data = json.loads(decoded)
                        if json_data["object"] == "error":
                            self.error(json_data["message"])
                            break
                    except:
                        self.error("Couldn't generate text, verify your key or model name")
                else:
                    text += decoded
                    if streaming_callback:
                        if not streaming_callback(decoded, MSG_TYPE.MSG_TYPE_CHUNK):
                            break
        return text
    
    
    
    def openai_generate_with_images(self, 
                        prompt,
                        images,
                        host_address=None, 
                        model_name=None, 
                        personality=None, 
                        n_predict=None, 
                        stream=False, 
                        temperature=0.1, 
                        top_k=50, 
                        top_p=0.95, 
                        repeat_penalty=0.8, 
                        repeat_last_n=40, 
                        seed=None, 
                        n_threads=8,
                        max_image_width=-1, 
                        service_key: str = "", 
                        streaming_callback=None,):
        """Generates text out of a prompt

        Args:
            prompt (str): The prompt to use for generation
            n_predict (int, optional): Number of tokens to prodict. Defaults to 128.
            callback (Callable[[str], None], optional): A callback function that is called everytime a new text element is generated. Defaults to None.
            verbose (bool, optional): If true, the code will spit many informations about the generation process. Defaults to False.
        """
        # Set default values to instance variables if optional arguments are None
        host_address = host_address if host_address else self.host_address
        model_name = model_name if model_name else self.model_name
        n_predict = n_predict if n_predict else self.n_predict
        personality = personality if personality is not None else self.personality
        # Set temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads to the instance variables if they are not provided or None
        temperature = temperature if temperature is not None else self.temperature
        top_k = top_k if top_k is not None else self.top_k
        top_p = top_p if top_p is not None else self.top_p
        repeat_penalty = repeat_penalty if repeat_penalty is not None else self.repeat_penalty
        repeat_last_n = repeat_last_n if repeat_last_n is not None else self.repeat_last_n
        seed = seed or self.seed  # Use the instance seed if not provided
        n_threads = n_threads if n_threads else self.n_threads
        if service_key != "":
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {service_key}',
            }
        else:
            headers = {
                'Content-Type': 'application/json',
            }

        
        data = {
            'model': model_name,
            'messages': [            
                    {
                        "role": "user", 
                        "content": [
                            {
                                "type":"text",
                                "text":prompt
                            }
                        ]+[
                            {
                                "type": "image_url",
                                "image_url": {
                                "url": f"data:image/jpeg;base64,{encode_image(image_path, max_image_width)}"
                                }                                    
                            }
                            for image_path in images
                        ]
                    }
            ],
            "stream": True,
            "temperature": float(temperature),
            "max_tokens": n_predict
        }

        completion_format_path = "/v1/chat/completions"

        if host_address.endswith("/"):
            host_address = host_address[:-1]
        url = f'{host_address}{completion_format_path}'

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 400:
            try:
                content = response.content.decode("utf8")
                content = json.loads(content)
                self.error(content["error"]["message"])
                return
            except:
                content = response.content.decode("utf8")
                content = json.loads(content)
                self.error(content["message"])
                return
        elif response.status_code == 404:
            ASCIIColors.error(response.content.decode("utf-8", errors='ignore'))
        
        text = ""
        for line in response.iter_lines():
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                try:
                    json_data = json.loads(decoded[5:].strip())
                    try:
                        chunk = json_data["choices"][0]["delta"]["content"]
                    except:
                        chunk = ""
                    # Process the JSON data here
                    text += chunk
                    if streaming_callback:
                        if not streaming_callback(chunk, MSG_TYPE.MSG_TYPE_CHUNK):
                            break
                except:
                    break
            else:
                if decoded.startswith("{"):
                    for line_ in response.iter_lines():
                        decoded += line_.decode("utf-8")
                    try:
                        json_data = json.loads(decoded)
                        if json_data["object"] == "error":
                            self.error(json_data["message"])
                            break
                    except:
                        self.error("Couldn't generate text, verify your key or model name")
                else:
                    text += decoded
                    if streaming_callback:
                        if not streaming_callback(decoded, MSG_TYPE.MSG_TYPE_CHUNK):
                            break
        return text


    def ollama_generate(self, prompt, host_address=None, model_name=None, personality=None, n_predict=None, stream=False, temperature=0.1, top_k=50, top_p=0.95, repeat_penalty=0.8, repeat_last_n=40, seed=None, n_threads=8, completion_format:ELF_COMPLETION_FORMAT=ELF_COMPLETION_FORMAT.Instruct, service_key:str="", streaming_callback=None):
        # Set default values to instance variables if optional arguments are None
        host_address = host_address if host_address else self.host_address
        model_name = model_name if model_name else self.model_name
        n_predict = n_predict if n_predict else self.n_predict
        personality = personality if personality is not None else self.personality
        # Set temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads to the instance variables if they are not provided or None
        temperature = temperature if temperature is not None else self.temperature
        top_k = top_k if top_k is not None else self.top_k
        top_p = top_p if top_p is not None else self.top_p
        repeat_penalty = repeat_penalty if repeat_penalty is not None else self.repeat_penalty
        repeat_last_n = repeat_last_n if repeat_last_n is not None else self.repeat_last_n
        seed = seed or self.seed  # Use the instance seed if not provided
        n_threads = n_threads if n_threads else self.n_threads

        if service_key!="":
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {service_key}',
            }
        else:
            headers = {
                'Content-Type': 'application/json',
            }

        data = {
            'model':model_name,
            'prompt': prompt,
            "stream":stream,
            "temperature": float(temperature),
            "max_tokens": n_predict
        }
        completion_format_path = "/api/generate"
        if host_address.endswith("/"):
            host_address = host_address[:-1]
        url = f'{host_address}{completion_format_path}'

        response = requests.post(url, json=data, headers=headers)

        if response.status_code==404:
            ASCIIColors.error(response.content.decode("utf-8", errors='ignore'))
        text = ""
        if stream:
            for line in response.iter_lines():
                decoded = line.decode("utf-8")
                json_data = json.loads(decoded)
                chunk = json_data["response"]
                ## Process the JSON data here
                text +=chunk
                if streaming_callback:
                    if not streaming_callback(chunk, MSG_TYPE.MSG_TYPE_CHUNK):
                        break            
                return text
        else:
            return response.content["response"]
    def litellm_generate(self, prompt, host_address=None, model_name=None, personality=None, n_predict=None, stream=False, temperature=0.1, top_k=50, top_p=0.95, repeat_penalty=0.8, repeat_last_n=40, seed=None, n_threads=8, completion_format:ELF_COMPLETION_FORMAT=ELF_COMPLETION_FORMAT.Instruct, service_key:str="", streaming_callback=None):
        # Set default values to instance variables if optional arguments are None
        host_address = host_address if host_address else self.host_address
        model_name = model_name if model_name else self.model_name
        n_predict = n_predict if n_predict else self.n_predict
        personality = personality if personality is not None else self.personality
        # Set temperature, top_k, top_p, repeat_penalty, repeat_last_n, seed, n_threads to the instance variables if they are not provided or None
        temperature = temperature if temperature is not None else self.temperature
        top_k = top_k if top_k is not None else self.top_k
        top_p = top_p if top_p is not None else self.top_p
        repeat_penalty = repeat_penalty if repeat_penalty is not None else self.repeat_penalty
        repeat_last_n = repeat_last_n if repeat_last_n is not None else self.repeat_last_n
        seed = seed or self.seed  # Use the instance seed if not provided
        n_threads = n_threads if n_threads else self.n_threads

        if service_key!="":
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {service_key}',
            }
        else:
            headers = {
                'Content-Type': 'application/json',
            }

        data = {
            'model':model_name,
            'prompt': prompt,
            "stream":True,
            "temperature": float(temperature),
            "max_tokens": n_predict
        }
        completion_format_path = "/api/generate"
        if host_address.endswith("/"):
            host_address = host_address[:-1]
        url = f'{host_address}{completion_format_path}'

        response = requests.post(url, json=data, headers=headers)

        if response.status_code==404:
            ASCIIColors.error(response.content.decode("utf-8", errors='ignore'))
        text = ""
        for line in response.iter_lines():
            decoded = line.decode("utf-8")
            if decoded.startswith("{"):
                json_data = json.loads(decoded)
                if "error" in json_data:
                    self.error(json_data["error"]["message"])
                    break
            else:
                text +=decoded
                if streaming_callback:
                    if not streaming_callback(decoded, MSG_TYPE.MSG_TYPE_CHUNK):
                            break
       
            return text



####

    def listMountedPersonalities(self, host_address:str=None):
        host_address = host_address if host_address else self.host_address
        url = f"{host_address}/list_mounted_personalities"

        response = requests.get(url)

        if response.status_code == 200:
            try:
                text = json.loads(response.content.decode("utf-8"))
                return text
            except Exception as ex:
                return {"status": False, "error": str(ex)}
        else:
            return {"status": False, "error": response.text}

    def listModels(self, host_address:str=None):
        host_address = host_address if host_address else self.host_address
        url = f"{host_address}/list_models"

        response = requests.get(url)

        if response.status_code == 200:
            try:
                text = json.loads(response.content.decode("utf-8"))
                return text
            except Exception as ex:
                return {"status": False, "error": str(ex)}
        else:
            return {"status": False, "error": response.text}

if __name__=="__main__":
    lc = LollmsClient("http://localhost:9600")
    print(lc.listMountedPersonalities())
    print(lc.listModels())
