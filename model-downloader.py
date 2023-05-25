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
            "1. Vicuna 7B CENSORED\n"\
            "2. Vicuna 7B UNCENSORED\n"\
            "3. Vicuna 13B CENSORED\n"\
            "4. MPT 7B UNCENSORED\n\n"\
            "Choice: "))
        if 1 <= choice <= 4:
            break
        else: print("\nInvalid range, please try again.\n")
    except ValueError:
        print("\nUnknown value, please enter a valid number.\n")

# Model mapping
model_map = {
    1: "https://huggingface.co/TheBloke/wizardLM-7B-GGML/resolve/main/wizardLM-7B.ggmlv3.q4_1.bin",
    2: "https://huggingface.co/TheBloke/Wizard-Vicuna-7B-Uncensored-GGML/resolve/main/Wizard-Vicuna-7B-Uncensored.ggmlv3.q4_1.bin",
    3: "https://huggingface.co/TheBloke/wizard-vicuna-13B-GGML/resolve/main/wizard-vicuna-13B.ggmlv3.q4_1.bin",
    4: "https://huggingface.co/TheBloke/MPT-7B-Instruct-GGML/resolve/main/mpt-7b-instruct.ggmlv3.q4_1.bin"
}
destination_map = {
    1: "vicuna-7B-CENSORED",
    2: "vicuna-7B-UNCENSORED",
    3: "vicuna-13B-CENSORED",
    4: "MPT-7B-UNCENSORED"
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