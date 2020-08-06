# coding=utf-8
import sys
import os,tempfile
sys.path.append(r'Tacotron')
import argparse
import tensorflow as tf
from .apps import TtsConfig as app
from Tacotron.infolog import log
from Tacotron.hparams import hparams
from Tacotron.tacotron.synthesizer import Synthesizer
from Tacotron.zh_cn import G2P
from CrystalTTS.text import TextAnalysis
import xml.etree.ElementTree as ElementTree
from tqdm import tqdm
import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from urllib import parse
import re
rule = re.compile('^[a-zA-Z ]{1}.*$')
rule_AZ = re.compile('^[A-Z]{1}.*$')
rule_az = re.compile('^[a-z]{1}.*$')
rule_digit = re.compile('^[0-9]{1}.*$')
alpha_list= ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z']
phone_list=['aye','bee','see','dee','ee','eff','jhee','eych','eye','jhey','key','ell','em','en','oh','pee','kyuw','are','ess','tea','you','vee','dahbulyuw','iykss','why','zee']
alpha_dict = dict(zip(alpha_list,phone_list))
digit_list0=['0','1','2','3','4','5','6','7','8','9']
digit_list=['零','一','二','三','四','五','六','七','八','九']
digit_dict = dict(zip(digit_list0,digit_list))
#from tensorflow.python.client import device_lib
#print(device_lib.list_local_devices())
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
parser.add_argument('--text_list', default='', help='Text file contains list of texts to be synthesized. Valid if mode=eval')
parser.add_argument('--speaker_id', default=None, help='Defines the speakers ids to use when running standalone Wavenet on a folder of mels. this variable must be a comma-separated list of ids')
args = parser.parse_args(args=[])
output_dir = 'media/tacotron_' + args.output_dir
eval_dir = os.path.join(output_dir, 'eval')
log_dir = os.path.join(output_dir, 'logs-eval')
os.makedirs(('media/TTS'),exist_ok=True)
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

ttsText = TextAnalysis()
ttsText.initialize('./CrystalTTS/cfgtext.xml')

def strQ2B(ustring):
    """把字符串全角转半角"""
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code==0x3000:
            inside_code=0x0020
        else:
            inside_code-=0xfee0
        if inside_code<0x0020 or inside_code>0x7e: #转完之后不是半角字符返回原来的字符
            rstring += uchar
        else:
            rstring += chr(inside_code)
    return rstring

def parseSSML(ssmlfile):
    # parse SSML file as XML ElementTree
    res = ''
    for event, elem in ElementTree.iterparse(ssmlfile):
        if event == 'end':
            if elem.tag == 'p':
                res=res.rstrip(',')
                res+= '.'
            elif elem.tag == 's':
                res += ','
            elif elem.tag == 'phoneme':
                pinyin = elem.attrib['ph']
                pinyin=pinyin.replace('/', '-')
                if pinyin.startswith('_'):
                    res+= elem.text
                else:
                    pinyin=pinyin.strip(' ')
                    res += pinyin+' '
            elif elem.tag == 'break':
                if elem.attrib.get('strength') == 'medium':
                    res += ' '
        elem.clear()  # discard the element
    # return
    res=strQ2B(res)
    res=res.lower()
    return res


def g2pChinese(txt, ssmlfile):
    # perform text analysis
    text = ""
    txt = txt.replace('-', ' ')
    txt = txt.replace('——', ' ')
    digit_flag = False
    for i in range(len(txt)):
        if rule_AZ.match(txt[i]) and not (rule_az.match(txt[i + 1])):
            text += alpha_dict[txt[i]] + ' '
            digit_flag = True
        elif rule_digit.match(txt[i]) and digit_flag:
            text += digit_dict[txt[i]]
        else:
            text += txt[i]
        if rule.match(txt[i]) and not (rule.match(txt[i + 1])):
            text += '  '
        if not (rule_digit.match(txt[i])) and not (rule.match(txt[i])):
            digit_flag = False

    ttsText.process(text, ssmlfile)


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
	#g2p=G2P()
	#sentences = [g2p.convert(i) for i in sentences]
	return sentences, speaker_labels, language_labels


def syn(sentence, wave):
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
            basenames = [wave]
            mel_filenames, speaker_ids = synth.synthesize(texts, speaker_labels[i], language_labels[i], basenames,
                                                          eval_dir, log_dir, None)

            for elems in zip(texts, mel_filenames, speaker_ids):
                file.write('|'.join([str(x) for x in elems]) + '\n')
    log('synthesized mel spectrograms at {}'.format(eval_dir))
    return sentences[0]

def getDataFilename():
    # get temp filename
    temp_name = 'random_' + next(tempfile._get_candidate_names())
    wavename = temp_name
    temp_name = os.path.join('media/'+app.name, temp_name)
    return temp_name, wavename

def TacotronProcess(txt, spk, lan):
    fname, wavename = getDataFilename()
    ssml = fname + '.ssml'
    if txt[-1]!='.':
        txt+='.'
    g2pChinese(txt, ssml)
    res = parseSSML(ssml)
    sentence = [res+'|'+spk+'|'+lan, ]
    syn(sentence, wavename)
    # return result
    wave ='media/tacotron_output/logs-eval/wavs/wav-'+wavename+'-linear.wav'
    ret = {'respCode': '0000', 'text': txt, 'pinyin': res, 'waveURL': wave}
    return ret

@csrf_exempt
def tts_api(request):
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

@csrf_exempt
def TTS(request):
    # get parameters
    if request.method == 'GET':
        text = request.GET.get('text', '')
        format = request.GET.get('format', '')
        sample_rate = request.GET.get('sample_rate','')
        voice = request.GET.get('voice','')
        volume = request.GET.get('volume','')
        speech_rate = request.GET.get('speech_rate','')
        pitch_rate = request.GET.get('pitch_rate','')
    elif request.method == 'POST':
        text = request.POST.get('text', '')
        format = request.POST.get('format', '')
        sample_rate = request.POST.get('sample_rate', '')
        voice = request.POST.get('voice', '')
        volume = request.POST.get('volume', '')
        speech_rate = request.POST.get('speech_rate', '')
        pitch_rate = request.POST.get('pitch_rate', '')

    lan = '1'  # language label 0-EN，1-CN
    ret = TacotronProcess(text, voice, lan)
    return JsonResponse(ret)

def index(request):
    return render(request, 'tts/index.html')

