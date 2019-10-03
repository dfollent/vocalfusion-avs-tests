from __future__ import print_function
import os
import argparse
import glob
import time
import json
import hashlib
import pyaudio


UTTERANCES = [
	{"name": "_P01_01_M", "request": "alexa what time is it in little rock", "response": ".*time in Little Rock.*", "sha1hash":["5907b77e392ca7f4a55ee068153a27725965523a", "1028525c5ebab8f54f44865f5d2e12fc1e3ab2a2"]},
	{"name": "_P01_02_M", "request": "alexa what is the capital of india", "response": ".*New Delhi.*", "sha1hash":["c1fe5e7486004330f8811c901accd84a0f01920d", "d7012fdf4c069ab8d3372fccb3072fe50d8c2e35"]},
	{"name": "_P01_04_M", "request": "alexa who wrote moby dick", "response": ".*Herman Melville.*", "sha1hash":["0dc961f27eb4dd50fee5af849ea62d31b2791940", "2aa418e9eaad007fb99708f99aecaf54225caf82", "b525acee418646eb4d34607e4527133608df4d49", "dfe2f15b13b8edba03121c5ff39bda9838dab758", "b2ca282381570c3d84335020bfbf0d9cadb673f3", "9b6b9759279ffcf22b5afb1f3c3ff68e001341db"]},
	{"name": "_P02_01_M", "request": "alexa what time is it in boston", "response": ".*time in Boston.*", "sha1hash":["1651553791e856c95070430ab4e9dabe3cf9c14f"]},
	{"name": "_P02_02_F", "request": "alexa what is the capital of bolivia", "response": ".*Sucre.*", "sha1hash":["7369b92b2994dc22b3ee3c58cc53c450140d0889", "42713da9e8096c1613e94081c2e98dbf20fe39ad", "f49c8ff5c6ff1d4bf5da575710d9f08c950e0c14"]},
	{"name": "_P02_04_M", "request": "alexa who wrote to kill a mockingbird", "response": ".*Harper Lee.*", "sha1hash":["d45966b98abfda1b1f105f4855acec10257891ce", "685585c15f8cabdb64cac42a9e24c87d211b3a48", "1b7ac6862050a06b1ad81895752431e8f7d19908", "d758b48753fcea6f4d3b1afda2c599d2e82b2d5f"]},
	{"name": "_P03_01_F", "request": "alexa what time is it in washington", "response": ".*time in Washington.*", "sha1hash":["f00fa3218400d7f34cde449f859f7e997ea16bef"]},
	{"name": "_P03_05_F", "request": "alexa how do you spell zoo", "response": ".*Zoo.*spelled.*", "sha1hash":["d5a1bc44f66e7050fe23509820c02fd7436fbe21", "a42c63a45328c3952402c3513c5247c972f96e78", "1e59481d7f391e09e3601179b2c1982fb8601229", "0e9d8dc234f7947e6dc4e1122cca4b4816be0bb4", "78d83892dfe297c57bf51b3712cf1ab1ed0d6e70", "135395b6603e4b61429015318c4725b30a0bc2e0", "e4bc58d3df05fe85c748fbcd50dec910044fd90b"]},
	{"name": "_P04_01_F", "request": "alexa what time is it in saint paul", "response": ".*time in Saint Paul.*", "sha1hash":["12b4dc5b425142230231c1bef78898214f08e0fb", "bc7eee0fb81e11d1beafa39f55aeab677084503f"]},
	{"name": "_P04_02_F", "request": "alexa what is the capital of south korea", "response": ".*Seoul.*", "sha1hash":["a6a54ae6025dd81c65e47c36aa6833c8d420ffba", "14339ae5b2529664c63184c1d461f1713ad676fe", "1c50dfe7c911be6a0efd5421c187ded3991d83c1", "65373cc1c2ec1af773bdefff3f969963e54466fa"]},
	{"name": "_P04_04_F", "request": "alexa who wrote crime and punishment", "response": ".*Fyodor Dostoevsky.*", "sha1hash":["78bae9499fbea1e28e18d6e296e4e6fd5b255396", "aa16cd20ca7e8702449428e35b3dbd4365cdf04c", "400968e3185d212d5bb393833a9f0f98ddd09944", "dfde582675c796d688b967728150d3ce6cc40dd7", "73cf27acb16ebc6d3559e9463fe4732ead705141", "846783bb36db2794a2e83f899f98cb53f2b93246", "e13d2346d50bc2645715a696948b2cf483a03fd7", "82d5cfb7fc39131e7106fdfe5e34cca91d3be177", "34867d8420f67da58976f07ac538e9aa497dea2a"]},
	{"name": "_P06_01_F", "request": "alexa what time is it in las vegas nevada", "response": ".*time in Las Vegas.*", "sha1hash":["063f994d3763640253d61a7fe486e461883a17c5"]},
	{"name": "_P06_02_F", "request": "alexa what is the capital of cuba", "response": ".*Havana.*", "sha1hash":["35d76a26403619f3f16ccfec430c199150f78855", "710385e2412cc809180d510125d1bfc9eef38989"]},
	{"name": "_P07_01_M", "request": "alexa what time is it in honolulu", "response": ".*time in Honolulu.*", "sha1hash":["c638bc99cb701d4ca9fd007d0fd16744a48426fd"]},
	{"name": "_P07_02_M", "request": "alexa what is the capital of finland", "response": ".*Helsinki.*", "sha1hash":["f5184581b13461afc44f8a455f069116c1dfcddd", "dc59a069d29bf478bfa688ff4f52c97d45dadadc"]},
	{"name": "_P07_04_M", "request": "alexa who wrote the canterbury tales", "response": ".*Geoffrey Chaucer.*", "sha1hash":["fa0d2d4b94fd988b32c485afe3681aafb05c6865", "96eef66b8fa7dac42332be1733bd1daacc947e3b", "2e007b7e946ca765ad8b1b6192ff8b2e1e5d8445", "08d0cc26a492783ef1f2e8c479f13f295b55d5f6"]},
	{"name": "_P08_01_M", "request": "alexa what time is it in charleston", "response": ".*time in Charleston.*", "sha1hash":["b063bf101e55c9ea55c0eab37a9fac0a012cd407", "b04bdffab3da6707d7cf218fcd64472fcf6d4457"]},
	{"name": "_P08_02_M", "request": "alexa what is the capital of bulgaria", "response": ".*Sofia.*", "sha1hash":["b6cc88034166e90cb0c47827d8886d4d9f796873", "51849197cd7dd14bd45d7386650cd0fb8e09b670"]},
	{"name": "_P08_04_M", "request": "alexa who wrote walden", "response": ".*Henry David Thoreau.*", "sha1hash":["e1c8c003280bbb4cc679285a063bbe59d8e9f40b", "ec723fd037c7f32b6aa796416b55db65ee6e977a", "469e5ca6814f812b178f93de0f53e3248818556e", "2b419d20ff84f4375cd088ae86de0fcfbef49620"]},
	{"name": "_P09_02_M", "request": "alexa what is the capital of australia", "response": ".*Canberra.*", "sha1hash":["6a326bff24cfd61acad05e0abf4a2820b81ca3e5", "2dec046a95b5957f84aa3c9edeb3bf71bb7e0d79", "cd431e36b51c59a3014639c41509c2122df48bea", "e7809d0ec0875c9eb9b38c0f0697beaaa6444355", "216fcbd28a435b727661917b0d0a0aba2fb69613", "4151f16073a959a1d043ad86a74983db2253400f", "e26000e444b2a235b9c6a5375f811d161ed16814", "46eca763a852484082555e9af53188b336788f6a"]},
	{"name": "_P09_05_M", "request": "alexa how do you spell bar", "response": ".*Bar.*spelled.*", "sha1hash":["250ab1fda55b13b05a027b11034ef52a470330fa", "f3f61a32a943b97a1a3204652ecb99cfe5001904"]},
	{"name": "_P10_01_M", "request": "alexa what time is it in hartford", "response": ".*time in Hartford.*", "sha1hash":["9b50d50067fa33062f140c6cc9fe5d005d8395cf"]},
	{"name": "_P10_02_M", "request": "alexa what is the capital of el salvador", "response": ".*San Salvador.*", "sha1hash":["b1d4c1f65e41f1df071b0618edad296fe125b6aa", "182863976ca5806224a1ac0efe49ccf81b6c1fac"]},
	{"name": "_P10_04_M", "request": "alexa who wrote alice in wonderland", "response": ".*(Louis|Lewis) Carroll.*", "sha1hash":["08e21f92fd1caae39e582860e8949fc1ed845165", "4e3db2e02f7167e0f9220a18be680701e92b7cf6", "551be1bec3eb9ce253ed4fe405d124cf320d3891", "25e212d4c47e9a07050f513adab3c01b2d0e084c", "10a723e7e77e9e91d4cb393c5e4955a3aae2530d"]},
	{"name": "_P11_01_F", "request": "alexa what time is it in harrisburg", "response": ".*time in Harrisburg.*", "sha1hash":["38902d91a9eaf622c1182c6438b1c472368546e2"]},
	{"name": "_P11_04_F", "request": "alexa who wrote great expectations", "response": ".*Charles Dickens.*", "sha1hash":["56bd921c8cdbdbcc6aee9f2343c339609454ce15", "ff435b58c5a5741ac9e8bb7d2e4dc61c161c749e", "4a4265e1bb642c5ae6a9f7393c718af608b8b402", "e00808ca3e382a8e1d3cf319cf33aa86d5cfee0e", "d2adad354969607f73b1697b2e55c72f5f02b807", "e103b1a4c44910fb55aebc0e3a4a148abef8c113"]},
	{"name": "_P12_01_F", "request": "alexa what time is it in trenton", "response": ".*time in Trenton.*", "sha1hash":["9951077c08bbc800c9015383ac8c1ee63f3bf9e6", "28526cf78457ad6f2a84c0de6b2835528abdd554"]},
	{"name": "_P12_02_F", "request": "alexa what is the capital of malta", "response": ".*Valletta.*", "sha1hash":["15c2ba5530fe53ca97d7034ea1102d7cedb0e4b1", "15c2ba5530fe53ca97d7034ea1102d7cedb0e4b1"]},
	{"name": "_P12_04_F", "request": "alexa who wrote the history of the decline and fall of the roman empire", "response": ".*Edward Gibbon.*", "sha1hash":["a30ef0bc358fb70b3a0f4e31dd51a88354bbcd29", "17967f08d50ea285b1dac7eb5de35af49167a932", "69f401576cc008bc3e3c4f094ad2d25c85b9d9c7", "5c55fc5c82684a7b930b5fb938866f7aa3681268", "9ddf046c986ebaa11d9e3b44268a7911d2525d73", "243e06fc6db8e064ae35026085aaeede466c9fc9"]},
	{"name": "_P13_02_M", "request": "alexa what is the capital of brazil", "response": ".*(Brasilia|Bras??lia).*", "sha1hash":["f5455b6c287aec06575cf42b0581dbee9df036ee", "80c8b2c9f65be265c34da1432ecf31d0d4855144"]},
	{"name": "_P13_04_M", "request": "alexa who wrote ulysses", "response": ".*James Joyce.*", "sha1hash":["ee9e635ae1b2d088dc0b844730385fb3adeda05f", "69f9620192ed586659acdf1e2d54f84c05128ac0", "ac25cbf16b7eb84aa45d75a235636ed56755c9f9"]},
	{"name": "_P14_01_M", "request": "alexa what time is it in pierre", "response": ".*time in Pierre.*", "sha1hash":[]},
	{"name": "_P14_02_M", "request": "alexa what's the capital of spain", "response": ".*Madrid.*", "sha1hash":["8d6ead38cb13dfd42480b2cb2efbfc1476e6481e", "2a81f910b8e5b24f4f81e5ffd09458a1a0a251fb", "74afc6a381ac37dfd3b9c9c5f8b61bba6c5a99af"]},
	{"name": "_P14_04_M", "request": "alexa who wrote the picture of dorian gray", "response": ".*Oscar Wilde.*", "sha1hash":["ee837a7285ee6eb0c90da86c1bcdc166f88d645c", "20028733b7c2b1ee0fedb9118051512eddf0bf84", "efd369647b83b46c3b6d9861a4a1455f5c373ca0", "5a0773fab221399440204b56579ae8e874ba90b2", "12c58cff8aba3279cab232e0ad94f5d8f03f558c"]},
	{"name": "_P14_05_M", "request": "alexa how would you spell ram", "response": ".*ram.*spelled.*", "sha1hash":["849f08eb52e359cd529ff4ae6814b35c5f900319", "865d96edb1abdac8a77f16645f7d5d68c00911b8"]},
	{"name": "_P15_01_M", "request": "alexa what time is it in augusta", "response": ".*time in Augusta.*", "sha1hash":["b4f69b7cca8cd1f16d8a171c22475c23761a001b", "0eb22296c22e6a0b47a90ecbedb86df03ef923e4"]},
	{"name": "_P15_02_M", "request": "alexa what is the capital of argentina", "response": ".*Buenos Aires.*", "sha1hash":["79ce6d1f046d7697f7a8f869bfa63d85b2059469", "c67f33830750482ddbf3d705930db63d8599c96d"]},
	{"name": "_P16_01_M", "request": "alexa what time is it in san luis obispo california", "response": ".*time in San Luis Obispo.*", "sha1hash":["e2111ee8ee0afd448f479e6f6991cd56ebce48d2", "d9c29703a1de872b0df7225eea0c6763c269ad5e", "ba1ad1809f01d84ad812d62caee5b83831a81bed", "23f450e5d4e4a52340d0b061ba64b5a24b8c40c6"]},
	{"name": "_P16_02_M", "request": "alexa what is the capital of canada", "response": ".*Ottawa.*", "sha1hash":["0114d2b577989b514ed66b7efdb455cc7577b552", "94a19dd6d961f6faf0d34dc641a5bce587eacc57"]},
	{"name": "_P16_04_M", "request": "alexa who wrote twenty thousand leagues under the sea", "response": ".*Jules Verne.*", "sha1hash":["f53c12ff0a6e809972e2ac027d1b72bd0f2ce0c4", "3dda0a9c8f02eebd377a5112e0b827979c4c9368", "206cb15d19ff7b20c13e6266db4f1d280f79329a", "153067c92137fa3b7d95176c16f2ab1135cde96d", "d0abeabead57f47c73c900c6e77653b190038e38", "c252be534ad8103c2cac778f1b61b6eac3098d86", "89cd11efafa4e5b67616ce99fd664ba0cdf52ac0", "a98b74a1b0a41817c21830b3dc82975ac952c35c"]},
	{"name": "_P17_01_F", "request": "alexa what time is it in tucson", "response": ".*time in Tucson.*", "sha1hash":["5dfc11034274f63e4c9d3a87f57ced058dbf782d"]},
	{"name": "_P17_02_F", "request": "alexa what is the capital of bolivia", "response": ".*Sucre.*", "sha1hash":["7369b92b2994dc22b3ee3c58cc53c450140d0889", "42713da9e8096c1613e94081c2e98dbf20fe39ad", "f49c8ff5c6ff1d4bf5da575710d9f08c950e0c14"]},
	{"name": "_P17_04_F", "request": "alexa who wrote the secret garden", "response": ".*Frances Hodgson Burnett.*", "sha1hash":["959188a20380d709ced67e95aa89ca4ea235e62f", "a7c962de0da849519be2a7f164078f810ed84dee", "40502ae4d09c5c6a83055998e58309aa83616516"]},
	{"name": "_P18_01_M", "request": "alexa what time is it in concord", "response": ".*time in Concord.*", "sha1hash":["3323ecd3be60461379a9ef02813eeacdc563969a", "275a44b07eb053a804a82ed64a031e57465fa3ff"]},
	{"name": "_P18_02_M", "request": "alexa what is the capital of costa rica", "response": ".*San Jos.*", "sha1hash":["b9509139ee6b1668da675484ac62b96e46e7ed05", "f0d1f21fb4f59dae20b8a6be6f46749858e5f1bd"]},
	{"name": "_P18_04_M", "request": "alexa who wrote the book the time machine", "response": ".*H. G. Wells.*", "sha1hash":["70762283b58a4fa77dec843849a67ace99a4924d", "a2da457f263b4f21a3704d220043a2b685d24923", "cb3ae4be65e46a9cf4344b0f6380518b78ad89ea"]},
	{"name": "_P19_01_M", "request": "alexa what time is it in springfield", "response": ".*time in Springfield.*", "sha1hash":["feeb81a1e59fc0c31a50393254735f634b6ecdf2"]},
	{"name": "_P19_02_M", "request": "alexa what is the capital of luxembourg", "response": ".*Luxembourg.*", "sha1hash":["9bd7b8ee069945405f0971231d6007dd40b82f8c", "36b0ccb683534e7b0d2894328206a355b895b355", "d3a772644f0b8e5c8dc9e82862c342a9904f833c", "e7bf2f281ca2d11208a2ed98d60aa4e4c405d4b7"]},
	{"name": "_P20_01_M", "request": "alexa what time is it in phoenix", "response": ".*time in Phoenix.*", "sha1hash":["145689dbb8d161226f215440bedb60fb375acc02"]},
	{"name": "_P20_02_M", "request": "alexa what is the capital of jamaica", "response": ".*Kingston.*", "sha1hash":["c4bffdfaea72316b3467829e3e3ae70b3639d0dc", "2b165d32a16ba27ae6972cd41b246bb927e8ba0f"]},
	{"name": "_P20_04_M", "request": "alexa who wrote war and peace", "response": ".*Leo Tolstoy.*", "sha1hash":["47cf0f45ef15b5aedebe3e8dbab480d10a111148", "b050139a29b38c92decdc76e7f181662453ca747", "aafb275a87d62ffe93837803e1e817d591d3d464"]}
]

INCORRECT_RESPONSES = [
	"155837b83afbf9288f74774de55ab53504fd1154", # Here's something I found on reference.com...
	"f05c02349d5eaef8dadbeb0482e0540a80161efd", # I didn't catch that.
	"afce4f24f5e9331f3db5741cd7b6c15c3f8e54f9", # I didn't get that.
	"26aef65cf87675dbe530414756c0ed5391e63364", # [Switch off]
	"c72f12118c398d00743e5577e830afe0a4dab819",	# Sorry, I didn't catch that.
	"2625ff6c737872b607a24668e0a691f084c02555",	# Sorry, I'm not sure.
	"08e32acd7df59a307daac9af9b237d272d930372",	# Sorry, I didn't get that.
	"f782441f5ec678a68733742d8d26cb3c64c1125a",	# Hmm, I don't know that one.
	"466e9694416abf139055aa3e66648f6329200762",	# Sorry, I'm not sure about that.
	"eba4255b03739de29fbb56dfffc2fcb469805ad2",	# Thanks for letting me know.
	"2ec6b18ad1ad36b3205d19702723e6cabe05a89f",	# Sorry, I don't know that one.
	"2625ff6c737872b607a24668e0a691f084c02555",	# Sorry, I'm not sure.
	"92cb6d582a0bcc11c56836bcb6e39cc1e9e40d28", # Sorry, what word?
	"135395b6603e4b61429015318c4725b30a0bc2e0",
	"c0a754294ee3bfd469b6180f510402f9ca5242a4", # Hmm I don't know that
	"5422d2ae07b7f9376a813201ada12b21cb13df30",
	"aff227b78ed02d2966eaee1c8c5af2a5dcd9925e", # Here's something I found on...
	"eedebe7e06323f51fe1b4a559e7b9fa0269ecd50", # Alice is a young girl...
	"91dec225848adf5c95a404a586948411262c574b", # I think you're asking about Alice...
	"da44fd816d807266e25c65131cbc5142651f9645", # I found something about Alice...
	"ce35daa215220bf49837945ad0081ce79f77e5ee", # It sounds like you're asking about Alice...
	"bae3b9a863c7da7a10dcdc34dc324fef822a0e38", # Sorry, I don't know that one
	"0799ec9b8d3c6a1a0f97daede3802a0e2aebaccf", # Sorry, I didn't get that
	"bbd8426c5b7450796040334b35d105ddbceced57", # I think I missed part of your question
	"fce65cd5aa03425a4f55af4de81d70b800045f03", # Sorry, can you repeat the word?
	"5f176f8426860948bf9af6bf8dadfc71296f9854", # I didn't catch that
	"487c88a714bac5961ed1a87165b0d75991340dcf" # I'm not sure I heard your full question
]


RESPONSE_01_BLOCKSIZE = (18000*2)


def get_args():
	description = 'Score a directory of AVS responses.  Results are stored in a JSON file.'
	argparser = argparse.ArgumentParser(description=description)
	argparser.add_argument('in_dir', help='Input directory')
	argparser.add_argument('out_json', help='Output JSON file')
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
		while user_input not in ["n", "y", "r", "u"]:
			user_input = raw_input("Correct response? y/n/r(eplay)/u(nsure): ")
		
		if user_input is "n":
			response_result = {"file": file, "sha1hash":file_hash, "wake":1, "response":0}
			break
		if user_input is "y":
			response_result = {"file": file, "sha1hash":file_hash, "wake":1, "response":1}
			break
		if user_input is "u":
			response_result = {"file": file, "sha1hash":file_hash, "wake":1, "response":-1}
			break
		if user_input is "r":
			user_input = ""
		
	return response_result


def get_file_hash(file):
	BLOCKSIZE = 65536
	hasher = hashlib.sha1()
	with open(file, 'rb') as read_file:
		buf = read_file.read(BLOCKSIZE)
		while len(buf) > 0:
			hasher.update(buf)
			buf = read_file.read(BLOCKSIZE)
	return hasher.hexdigest()
	

def get_file_block_hash(file, blocksize):
	hasher = hashlib.sha1()
	with open(file, 'rb') as read_file:
		buf = read_file.read(blocksize)
		hasher.update(buf)
		# p = pyaudio.PyAudio()
		# stream = p.open(format=pyaudio.paInt16,
		# 				channels=1,
		# 				rate=24000,
		# 				output=True)
		# 
		# stream.write(buf)
		# stream.stop_stream()
		# stream.close()
		# p.terminate()


	return hasher.hexdigest()


def main():
	args = get_args()
	response_results = []	
	utterances = UTTERANCES
	for utterance in utterances:
		response_files = glob.glob("{}/*{}*raw".format(args.in_dir, utterance["name"]))
		for file in response_files:
			response_result = {}
			if os.path.getsize(file) == 0:
				# No wakeword detected
				response_result = {"file": file, "wake":0, "response":0, "sha1hash":""}

			else:
				file_hash = get_file_hash(file)
				print("\nFile response hash: {}".format(file_hash))
				if file_hash in INCORRECT_RESPONSES:
					response_result = {"file": file, "wake":1, "response":0, "sha1hash":file_hash}
				else:
					response_hash = ""
					if "_01_" in utterance["name"]:
						response_hash = get_file_block_hash(file, RESPONSE_01_BLOCKSIZE)
						print("\nShort response hash: {}".format(response_hash))
					else:
						response_hash = file_hash
					
					if not utterance["sha1hash"] or response_hash not in utterance["sha1hash"]:
						print("\nPlaying {}".format(file))
						print("Request: '{}'".format(utterance["request"]))
						print("Expected response: '{}'".format(utterance["response"]))
						time.sleep(1)
						
						response_result = get_response_result(file, response_hash)
						
					elif response_hash in utterance["sha1hash"]:
						response_result = {"file": file, "wake":1, "response":1, "sha1hash":response_hash}
					
					else:
						print("ERROR: unexpected file '{}'".format(file))
						sys.exit(1)
				
			response_results.append(response_result)

	with open(args.out_json, 'w') as outfile:
		json.dump(response_results, outfile, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == '__main__':
	main()
