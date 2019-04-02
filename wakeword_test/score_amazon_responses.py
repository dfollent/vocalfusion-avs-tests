import os
import argparse
import glob
import subprocess
import time

import hashlib
import pyaudio
    
UTTERANCES = [
	{"name": "US_P01_01_M", "response": ".*time in Little Rock.*", "hash":[]},
	{"name": "US_P01_02_M", "response": ".*New Delhi.*", "hash":["d7012fdf4c069ab8d3372fccb3072fe50d8c2e35"]},
	{"name": "US_P01_04_M", "response": ".*Herman Melville.*", "hash":["dfe2f15b13b8edba03121c5ff39bda9838dab758"]},
	{"name": "US_P02_01_M", "response": ".*time in Boston.*", "hash":[]},
	{"name": "US_P02_02_F", "response": ".*Sucre.*", "hash":["f49c8ff5c6ff1d4bf5da575710d9f08c950e0c14"]},
	{"name": "US_P02_04_M", "response": ".*Harper Lee.*", "hash":["1b7ac6862050a06b1ad81895752431e8f7d19908", "d758b48753fcea6f4d3b1afda2c599d2e82b2d5f"]},
	{"name": "US_P03_01_F", "response": ".*time in Washington.*", "hash":[]},
	{"name": "US_P03_05_F", "response": ".*Zoo.*spelled.*", "hash":["78d83892dfe297c57bf51b3712cf1ab1ed0d6e70", "135395b6603e4b61429015318c4725b30a0bc2e0", "e4bc58d3df05fe85c748fbcd50dec910044fd90b"]},
	{"name": "US_P04_01_F", "response": ".*time in Saint Paul.*", "hash":[]},
	{"name": "US_P04_02_F", "response": ".*Seoul.*", "hash":["1c50dfe7c911be6a0efd5421c187ded3991d83c1"]},
	{"name": "US_P04_04_F", "response": ".*Fyodor Dostoevsky.*", "hash":[]},
	{"name": "US_P06_01_F", "response": ".*time in Las Vegas.*", "hash":[]},
	{"name": "US_P06_02_F", "response": ".*Havana.*", "hash":["710385e2412cc809180d510125d1bfc9eef38989"]},
	{"name": "US_P07_01_M", "response": ".*time in Honolulu.*", "hash":[]},
	{"name": "US_P07_02_M", "response": ".*Helsinki.*", "hash":["dc59a069d29bf478bfa688ff4f52c97d45dadadc"]},
	{"name": "US_P07_04_M", "response": ".*Geoffrey Chaucer.*", "hash":["08d0cc26a492783ef1f2e8c479f13f295b55d5f6"]},
	{"name": "US_P08_01_M", "response": ".*time in Charleston.*", "hash":[]},
	{"name": "US_P08_02_M", "response": ".*Sofia.*", "hash":["51849197cd7dd14bd45d7386650cd0fb8e09b670"]},
	{"name": "US_P08_04_M", "response": ".*Henry David Thoreau.*", "hash":["469e5ca6814f812b178f93de0f53e3248818556e", "2b419d20ff84f4375cd088ae86de0fcfbef49620"]},
	{"name": "US_P09_02_M", "response": ".*Canberra.*", "hash":["216fcbd28a435b727661917b0d0a0aba2fb69613", "4151f16073a959a1d043ad86a74983db2253400f", "e26000e444b2a235b9c6a5375f811d161ed16814", "46eca763a852484082555e9af53188b336788f6a"]},
	{"name": "US_P09_05_M", "response": ".*Bar.*spelled.*", "hash":[]},
	{"name": "US_P10_01_M", "response": ".*time in Hartford.*", "hash":[]},
	{"name": "US_P10_02_M", "response": ".*San Salvador.*", "hash":["182863976ca5806224a1ac0efe49ccf81b6c1fac"]},
	{"name": "US_P10_04_M", "response": ".*(Louis|Lewis) Carroll.*", "hash":["25e212d4c47e9a07050f513adab3c01b2d0e084c", "10a723e7e77e9e91d4cb393c5e4955a3aae2530d"]},
	{"name": "US_P11_01_F", "response": ".*time in Harrisburg.*", "hash":[]},
	{"name": "US_P11_04_F", "response": ".*Charles Dickens.*", "hash":["d2adad354969607f73b1697b2e55c72f5f02b807", "e103b1a4c44910fb55aebc0e3a4a148abef8c113"]},
	{"name": "US_P12_01_F", "response": ".*time in Trenton.*", "hash":[]},
	{"name": "US_P12_02_F", "response": ".*Valletta.*", "hash":["15c2ba5530fe53ca97d7034ea1102d7cedb0e4b1"]},
	{"name": "US_P12_04_F", "response": ".*Edward Gibbon.*", "hash":[]},
	{"name": "US_P13_02_M", "response": ".*(Brasilia|Bras??lia).*", "hash":["80c8b2c9f65be265c34da1432ecf31d0d4855144"]},
	{"name": "US_P13_04_M", "response": ".*James Joyce.*", "hash":["ac25cbf16b7eb84aa45d75a235636ed56755c9f9"]},
	{"name": "US_P14_01_M", "response": ".*time in Pierre.*", "hash":[]},
	{"name": "US_P14_02_M", "response": ".*Madrid.*", "hash":["2a81f910b8e5b24f4f81e5ffd09458a1a0a251fb", "74afc6a381ac37dfd3b9c9c5f8b61bba6c5a99af"]},
	{"name": "US_P14_04_M", "response": ".*Oscar Wilde.*", "hash":["5a0773fab221399440204b56579ae8e874ba90b2", "12c58cff8aba3279cab232e0ad94f5d8f03f558c"]},
	{"name": "US_P15_01_M", "response": ".*time in Augusta.*", "hash":[]},
	{"name": "US_P15_02_M", "response": ".*Buenos Aires.*", "hash":["c67f33830750482ddbf3d705930db63d8599c96d"]},
	{"name": "US_P16_01_M", "response": ".*time in San Luis Obispo.*", "hash":[]},
	{"name": "US_P16_02_M", "response": ".*Ottawa.*", "hash":["94a19dd6d961f6faf0d34dc641a5bce587eacc57"]},
	{"name": "US_P16_04_M", "response": ".*Jules Verne.*", "hash":["89cd11efafa4e5b67616ce99fd664ba0cdf52ac0", "a98b74a1b0a41817c21830b3dc82975ac952c35c"]},
	{"name": "US_P17_01_F", "response": ".*time in Tucson.*", "hash":[]},
	{"name": "US_P17_02_F", "response": ".*Sucre.*", "hash":["f49c8ff5c6ff1d4bf5da575710d9f08c950e0c14"]},
	{"name": "US_P17_04_F", "response": ".*Frances Hodgson Burnett.*", "hash":["a7c962de0da849519be2a7f164078f810ed84dee"]},
	{"name": "US_P18_01_M", "response": ".*time in Concord.*", "hash":[]},
	{"name": "US_P18_02_M", "response": ".*San Jos.*", "hash":["f0d1f21fb4f59dae20b8a6be6f46749858e5f1bd"]},
	{"name": "US_P18_04_M", "response": ".*H. G. Wells.*", "hash":["cb3ae4be65e46a9cf4344b0f6380518b78ad89ea"]},
	{"name": "US_P19_01_M", "response": ".*time in Springfield.*", "hash":[]},
	{"name": "US_P19_02_M", "response": ".*Luxembourg.*", "hash":["e7bf2f281ca2d11208a2ed98d60aa4e4c405d4b7"]},
	{"name": "US_P20_01_M", "response": ".*time in Phoenix.*", "hash":[]},
	{"name": "US_P20_02_M", "response": ".*Kingston.*", "hash":["2b165d32a16ba27ae6972cd41b246bb927e8ba0f"]},
	{"name": "US_P20_04_M", "response": ".*Leo Tolstoy.*", "hash":["b050139a29b38c92decdc76e7f181662453ca747"]}
]

def get_args():
    description = 'Run a directory of raw files through the AVS SDK on a pi'
    argparser = argparse.ArgumentParser(description=description)
    argparser.add_argument('in_dir', default=None, help='Input directory')
    
    return argparser.parse_args()


def play_raw_file(filepath):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=24000,
                    output=True)

    file_to_play = open(filepath, 'rb')

    data = file_to_play.read()

    stream.write(data)

    stream.stop_stream()
    stream.close()

    p.terminate()



def get_response_result(file, file_hash):
    response_result = {}
    user_input = ""
    while True:
        play_raw_file(file)
        while user_input not in ["n", "y", "r"]:
            user_input = raw_input("Correct response? y/n/r(eplay): ")
        
        if user_input is "n":
            response_result = {"file": file, "hash":file_hash, "wake":1, "response":0}
            break
        if user_input is "y":
            response_result = {"file": file, "hash":file_hash, "wake":1, "response":1}
            break
        if user_input is "r":
            user_input = ""
            
    return response_result




def main():

    args = get_args()

    response_results = []    
    utterances = UTTERANCES
    for utterance in utterances:
        response_files = glob.glob("{}/*{}*raw".format(args.in_dir, utterance["name"]))
        for file in response_files:
            response_result = {}
                        
            # Check if no response
            if os.path.getsize(file) == 0:
                response_result = {"file": file, "wake":0, "response":0, "hash":""}
            
            else:
                BLOCKSIZE = 65536
                hasher = hashlib.sha1()
                with open(file, 'rb') as read_file:
                    buf = read_file.read(BLOCKSIZE)
                    while len(buf) > 0:
                        hasher.update(buf)
                        buf = read_file.read(BLOCKSIZE)
                file_hash = hasher.hexdigest()

                if not utterance["hash"] or file_hash not in utterance["hash"]:
                    print("Playing {}".format(file))
                    print("Expected response: '{}'".format(utterance["response"]))
                    time.sleep(1)
                    
                    response_result = get_response_result(file, file_hash)
                    
                elif file_hash in utterance["hash"]:
                    response_result = {"file": file, "wake":1, "response":1, "hash":file_hash}
                    
                else:
                    print "ERROR: {}".format(file)
                
            print response_result
            response_results.append(response_result)

            
    for result in response_results:
        print result




if __name__ == '__main__':
	main()
