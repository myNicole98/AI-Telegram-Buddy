from tqdm import tqdm
import requests
import os

print("""\
   __   __    ____   __   _  _  __ _  __     __    __   ____  ____  ____ 
 / _\ (  )  (    \ /  \ / )( \(  ( \(  )   /  \  / _\ (    \(  __)(  _ )
/    \ )(    ) D ((  O )\ /\ //    // (_/\(  O )/    \ ) D ( ) _)  )   /
\_/\_/(__)  (____/ \__/ (_/\_)\_)__)\____/ \__/ \_/\_/(____/(____)(__\_)
    """)

# Check if directory exists
if not os.path.exists('models/'):
    os.makedirs('models/')


# Model choice
while True:
    try:
        choice = int(input("Please select the model you want to download from the following list:\n" \
            "1. Vicuna 7B \n"\
            "2. Vicuna 7B UNCENSORED (Recommended)\n"\
            "3. Vicuna 13B\n"\
            "4. MPT 7B\n"\
            "5. GPT4All 13B\n"\
            "6. dolly-v2 3B\n"\
            "7. dolly-v2 7B\n"\
            "8. LLaMa 7B\n"\
            "9. LLaMa 7B UNCENSORED\n"\
            "10. LLaMA 13B UNCENSORED (Recommended)\n\n"\
            "Choice: "))
        if 1 <= choice <= 10:
            break
        else: print("\nInvalid range, please try again.\n")
    except ValueError:
        print("\nUnknown value, please enter a valid number.\n")

# Model mapping
model_map = {
    1: "https://huggingface.co/TheBloke/wizardLM-7B-GGML/resolve/main/wizardLM-7B.ggmlv3.q4_1.bin",
    2: "https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGML/resolve/main/Wizard-Vicuna-7B-Uncensored.ggmlv3.q4_1.bin",
    3: "https://huggingface.co/TheBloke/wizard-vicuna-13B-GGML/resolve/main/wizard-vicuna-13B.ggmlv3.q4_1.bin",
    4: "https://huggingface.co/TheBloke/MPT-7B-Instruct-GGML/resolve/main/mpt-7b-instruct.ggmlv3.q4_1.bin",
    5: "https://huggingface.co/TheBloke/GPT4All-13B-snoozy-GGML/resolve/main/GPT4All-13B-snoozy.ggmlv3.q4_1.bin",
    6: "https://huggingface.co/mverrilli/dolly-v2-3b-ggml/resolve/main/ggml-model-q5_0.bin",
    7: "https://huggingface.co/mverrilli/dolly-v2-7b-ggml/resolve/main/ggml-model-q5_0.bin",
    8: "https://huggingface.co/Jahaz/multi-lora-llama-7b-ggml-q5-1/resolve/main/7B-ggml-WizardLM-unsensored-model-q5_1.bin",
    9: "https://huggingface.co/Jahaz/multi-lora-llama-7b-ggml-q5-1/resolve/main/7B-ggml-model-wizard-finnish-itlaian-germany-esjokeq5_1.bin",
    10: "https://huggingface.co/Jahaz/multi-lora-llama-7b-ggml-q5-1/resolve/main/13B-ggml-model-WizardVicunaUnsensored-StarCoderq5_1.bin"
}
destination_map = {
    1: "Vicuna-7B",
    2: "Vicuna-7B-UNCENSORED",
    3: "Vicuna-13B",
    4: "MPT-7B",
    5: "GPT4All-13B",
    6: "dolly-v2-3B",
    7: "dolly-v2-7B",
    8: "LLaMa-7B",
    9: "LLaMa-7B-UNCENSORED",
    10: "LLaMa-13B-UNCENSORED"
}
url = model_map[choice]
destination_path = "models/" + destination_map[choice] + ".bin"

# Model download
response = requests.get(url, stream=True)

total_size = int(response.headers.get('content-length', 0))
block_size = 1024

progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)

with open(destination_path, 'wb') as file:
    for data in response.iter_content(block_size):
        progress_bar.update(len(data))
        file.write(data)

progress_bar.close()
print("Model download complete.")