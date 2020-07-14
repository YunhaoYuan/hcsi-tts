# coding=utf-8
import sys
import os
sys.path.append(r'Tacotron')
import argparse
import tensorflow as tf
from Tacotron.infolog import log
from Tacotron.hparams import hparams
from Tacotron.tacotron.synthesizer import Synthesizer
from Tacotron.zh_cn import G2P
from tqdm import tqdm

import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from urllib import parse


#预加载Tacotron模型
parser = argparse.ArgumentParser()
parser.add_argument('--checkpoint', default='pretrained/', help='Path to model checkpoint')
parser.add_argument('--hparams', default='',
	help='Hyperparameter overrides as a comma-separated list of name=value pairs')
parser.add_argument('--name', help='Name of logging directory if the two models were trained together.')
parser.add_argument('--tacotron_name', help='Name of logging directory of Tacotron. If trained separately')
parser.add_argument('--wavenet_name', help='Name of logging directory of WaveNet. If trained separately')
parser.add_argument('--model', default='Tacotron')
parser.add_argument('--mels_dir', default='tacotron_output/eval/', help='folder to contain mels to synthesize audio from using the Wavenet')
parser.add_argument('--output_dir', default='output/', help='folder to contain synthesized mel spectrograms')
parser.add_argument('--GTA', default='True', help='Ground truth aligned synthesis, defaults to True, only considered in synthesis mode')
parser.add_argument('--text_list', default='web', help='Text file contains list of texts to be synthesized. Valid if mode=eval')
parser.add_argument('--speaker_id', default=None, help='Defines the speakers ids to use when running standalone Wavenet on a folder of mels. this variable must be a comma-separated list of ids')
args = parser.parse_args(args=[])
output_dir = 'media/tacotron_' + args.output_dir
eval_dir = os.path.join(output_dir, 'eval')
log_dir = os.path.join(output_dir, 'logs-eval')
os.makedirs(eval_dir, exist_ok=True)
os.makedirs(log_dir, exist_ok=True)
os.makedirs(os.path.join(log_dir, 'wavs'), exist_ok=True)
os.makedirs(os.path.join(log_dir, 'plots'), exist_ok=True)
#加载模型路径
checkpoint = os.path.join('Tacotron/logs-Tacotron', 'taco_' + args.checkpoint)
checkpoint_path = tf.train.get_checkpoint_state(checkpoint).model_checkpoint_path
log('loaded model at {}'.format(checkpoint_path))
synth = Synthesizer()
synth.load(checkpoint_path, hparams)

def get_sentences(websen):
	a_sentences = websen
	print(a_sentences)
	sentences=[]
	speaker_labels=[]
	language_labels=[]
	for i, line in enumerate(a_sentences):
		line = line.strip('\t\r\n').split('|')
		sentences.append(line[0])
		speaker_labels.append(int(line[1]))
		#0 denotes English, 1 denotes Chinese
		language_labels.append(int(line[2]))
    #执行中文到拼音转换，若不需要可注释掉下两行
	g2p=G2P()
	sentences = [g2p.convert(i) for i in sentences]
	return sentences, speaker_labels, language_labels


def syn(sentence):
    sentences, speaker_labels, language_labels = get_sentences(sentence)
    sentences = [sentences[i: i + hparams.tacotron_synthesis_batch_size] for i in
                 range(0, len(sentences), hparams.tacotron_synthesis_batch_size)]
    speaker_labels = [speaker_labels[i: i + hparams.tacotron_synthesis_batch_size] for i in
                      range(0, len(speaker_labels), hparams.tacotron_synthesis_batch_size)]
    language_labels = [language_labels[i: i + hparams.tacotron_synthesis_batch_size] for i in
                       range(0, len(language_labels), hparams.tacotron_synthesis_batch_size)]
    log('Starting Synthesis')
    with open(os.path.join(eval_dir, 'map.txt'), 'w') as file:
        for i, texts in enumerate(tqdm(sentences)):
            basenames = ['batch_{}_sentence_{}'.format(i, j) for j in range(len(texts))]
            mel_filenames, speaker_ids = synth.synthesize(texts, speaker_labels[i], language_labels[i], basenames,
                                                          eval_dir, log_dir, None)

            for elems in zip(texts, mel_filenames, speaker_ids):
                file.write('|'.join([str(x) for x in elems]) + '\n')
    log('synthesized mel spectrograms at {}'.format(eval_dir))

@csrf_exempt
def TacotronProcess(txt, spk, lan):
    sentence = [txt+'|'+spk+'|'+lan, ]
    syn(sentence)
    # return result
    wave ='media/tacotron_output/logs-eval/wavs/wav-batch_0_sentence_0-linear.wav'
    ret = {'respCode': '0000', 'text': txt, 'waveURL': wave}
    return ret

def index(request):
    if (request.method=='GET'):
        url=request.get_full_path()
        parameter = parse.parse_qs(parse.urlparse(url).query)
        appkey = parameter['appkey'][0]
        token = parameter['token'][0]
        text = parameter['text'][0]
        format = parameter['format'][0]
        sample_rate = int(parameter['sample_rate'][0])
        voice = parameter['voice'][0]
        volume = int(parameter['volume'][0])
        speech_rate = int(parameter['speech_rate'][0])
        pitch_rate = int(parameter['pitch_rate'][0])

    if (request.method=='POST'):
        parameter = json.loads(request.body)
        appkey = parameter['appkey']
        token = parameter['token']
        text = parameter['text']
        format = parameter['format']
        sample_rate = int(parameter['sample_rate'])
        voice = parameter['voice']
        volume = int(parameter['volume'])
        speech_rate = int(parameter['speech_rate'])
        pitch_rate = int(parameter['pitch_rate'])

    lan='1'#language label 0-EN，1-CN
    ret = TacotronProcess(text, voice, lan)
    fname=ret.get('waveURL')
    f=open(fname,'rb')
    response = HttpResponse()
    response.write(f.read())
    response['Content-Type'] = 'audio/wav'
    response['Content-Length'] = os.path.getsize(fname)
    return response



