import argparse
import json
from collections import Counter


NOISE_VOLUMES = ["45", "55", "65"]
SPEECH_VOLUMES = ["Normal", "Soft"]
NOISE_TYPES = ["Pink", "Brown", "Music", "Pub", "Cafeteria", "Living", "NPRnews", "Microwave"]
SILENCE_VOLS = ["47", "52", "57", "62", "67"]
BARGEIN_VOLS = ["55dBA_Ref_Silence_67dB", "65dBA_Ref_Silence_67dB", "55dBA_Ref_Silence_57dB", "65dBA_Ref_Silence_57dB"]


def get_json(file):
    with open(file, 'r') as f:
        return json.load(f)


def get_args():
    description = 'Parse JSON file of Amazon response scores to get aggregated results'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('input_json', help='Input JSON file')
    return argparser.parse_args()


def parse_data(input_data):
    for speech_vol in SPEECH_VOLUMES:
        for noise_vol in NOISE_VOLUMES:
            print("\n")
            for noise_type in NOISE_TYPES:
                responses = [response for response in input_data 
                                if "{}dB_{}".format(noise_vol, speech_vol) in response["file"]
                                and noise_type in response["file"]]
                # print len(responses)
                total_responses = len(responses)
                wake_responses = Counter(response['wake'] for response in responses)[1] + Counter(response['wake'] for response in responses)[-1]
                correct_responses = Counter(response['response'] for response in responses)[1]
                unknown_response = Counter(response['response'] for response in responses)[-1]
                
                test_name_str = "{}dB_{} {}".format(noise_vol, speech_vol, noise_type)
                detection_str = "Detection: {:>2} / {:>2}".format(wake_responses, total_responses)
                response_str = "Response: {:>2} / {:>2}".format(correct_responses, total_responses)
                unknown_str = "Unknown Responses: {:>2}".format(unknown_response)
                
                print("{:<25}  {:<25}  {:<25}  ({})".format(test_name_str, detection_str, response_str, unknown_str))


    print("\nSILENCE CASES")
    for speech_vol in SILENCE_VOLS:
        responses = [response for response in input_data 
                        if "response_Silence_{}".format(speech_vol) in response["file"]]

        total_responses = len(responses)
        wake_responses = Counter(response['wake'] for response in responses)[1] + Counter(response['wake'] for response in responses)[-1]
        correct_responses = Counter(response['response'] for response in responses)[1]
        unknown_response = Counter(response['response'] for response in responses)[-1]
        
        test_name_str = "Silence {}dB".format(speech_vol)
        detection_str = "Detection: {:>2} / {:>2}".format(wake_responses, total_responses)
        response_str = "Response: {:>2} / {:>2}".format(correct_responses, total_responses)
        unknown_str = "Unknown Responses: {:>2}".format(unknown_response)
        
        print("{:<25}  {:<25}  {:<25}  ({})".format(test_name_str, detection_str, response_str, unknown_str))


    print("\nBARGE IN")
    for vol in BARGEIN_VOLS:
        responses = [response for response in input_data 
                        if "response_{}".format(vol) in response["file"]]

        total_responses = len(responses)
        wake_responses = Counter(response['wake'] for response in responses)[1] + Counter(response['wake'] for response in responses)[-1]
        correct_responses = Counter(response['response'] for response in responses)[1]
        unknown_response = Counter(response['response'] for response in responses)[-1]
        
        test_name_str = "Barge In {}".format(vol)
        detection_str = "Detection: {:>2} / {:>2}".format(wake_responses, total_responses)
        response_str = "Response: {:>2} / {:>2}".format(correct_responses, total_responses)
        unknown_str = "Unknown Responses: {:>2}".format(unknown_response)
        
        print("{:<25}  {:<25}  {:<25}  ({})".format(test_name_str, detection_str, response_str, unknown_str))
    


def main():

    args = get_args()
    input_data = get_json(args.input_json)
    
    parse_data(input_data)




    


if __name__ == '__main__':
	main()

