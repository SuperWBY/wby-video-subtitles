#!/usr/bin/env python3
"""Portable subtitle pipeline. Run --help; all output is JSON, diagnostics on stderr."""
import argparse, hashlib, json, math, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from datetime import datetime, timezone

VERSION='1.3.0'
SKILL_ROOT=Path(__file__).resolve().parent.parent
BUNDLED_FONT=SKILL_ROOT/'assets/fonts/NotoSansCJKsc-Regular.otf'
STYLE_PRESETS={
    'compact':dict(font_size_ratio=.040,min_font_size_ratio=.032,translation_font_scale=.76),
    'standard':dict(font_size_ratio=.045,min_font_size_ratio=.035,translation_font_scale=.78),
    'emphasis':dict(font_size_ratio=.052,min_font_size_ratio=.040,translation_font_scale=.80),
}
def emit(x): print(json.dumps(x,ensure_ascii=False,indent=2))
def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def save(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def run(cmd,**kw):
    p=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,**kw)
    if p.returncode: raise RuntimeError(p.stderr[-6000:] or p.stdout[-2000:])
    return p

def machine():
    p=Path.home()/'.local/share/wby-video-subtitles/machine.json'
    return read(p) if p.exists() else {}
def default_font_path():
    configured=machine().get('font_path')
    if configured and Path(configured).expanduser().is_file():return str(Path(configured).expanduser())
    if BUNDLED_FONT.is_file():return str(BUNDLED_FONT)
    return ''
def stylepreset(name):
    if name not in STYLE_PRESETS:raise ValueError(f'Unknown style preset: {name}')
    return dict(STYLE_PRESETS[name])
def normalizelanguage(value):
    value=(value or 'auto').strip()
    if value.casefold()=='auto':return None
    if not re.fullmatch(r'[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*',value):raise ValueError('Language must be auto or a backend-supported language code such as en, fr, zh, ja, or pt')
    return value
def transcriptionprompt(terms):
    return 'Names and terminology: '+', '.join(terms) if terms else None
def ffmpeg():
    p=os.environ.get('SUBTITLE_FFMPEG') or shutil.which('ffmpeg')
    if p:return p
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()
def probe(p):
    p=Path(p).resolve()
    if not p.is_file():raise ValueError(f'Video missing: {p}')
    s=subprocess.run([ffmpeg(),'-hide_banner','-i',str(p)],capture_output=True,text=True).stderr
    d=re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)',s)
    video=next((l for l in s.splitlines() if 'Video:' in l),'')
    size=re.search(r'\b(\d{2,5})x(\d{2,5})\b',video)
    if not d or not size:raise ValueError('Cannot determine video duration/dimensions')
    duration=int(d[1])*3600+int(d[2])*60+float(d[3]);w,h=map(int,size.groups())
    rot=re.search(r'rotation of\s+(-?[\d.]+)',s)
    rotation=float(rot[1]) if rot else 0
    if abs(rotation)%180 > 1:w,h=h,w
    return dict(path=str(p),width=w,height=h,duration=duration,rotation=rotation,audio='Audio:' in s)

def loadjob(p):
    job=Path(p).resolve();m=read(job/'manifest.json')
    if sha(m['video']['path'])!=m['video_sha256']:raise ValueError('Video changed: create a new job; refusing stale captions/cache')
    return job,m

def init(a):
    video=probe(a.video);digest=sha(video['path']);job=Path(a.job).resolve()
    if job.exists() and any(job.iterdir()):raise ValueError('Job directory must be empty; existing jobs are never overwritten')
    job.mkdir(parents=True,exist_ok=True)
    save(job/'manifest.json',dict(version=VERSION,video=video,video_sha256=digest,created=datetime.now(timezone.utc).isoformat()))
    preset=stylepreset(a.preset)
    language=normalizelanguage(a.language)
    save(job/'config.json',dict(font_path=a.font or default_font_path(),style_preset=a.preset,**preset,text_color='#FFFFFF',background_color='#000000',background_opacity=0,outline_color='#000000',outline_px=3,margin_x_ratio=0.06,margin_y_ratio=0.06,position='bottom',max_lines=2,max_cps=17,min_duration=0.5,max_duration=6,language=language,terms=[],translation_color='#D6E4FF',backend='mlx',model=machine().get('model','mlx-community/whisper-large-v3-turbo')))
    emit(dict(job=str(job),video=video,preset=a.preset,source_language=language or 'auto',font_path=a.font or default_font_path(),next='Edit config.json; transcribe or import SRT, then prepare'))

def transcribe(a):
    job,m=loadjob(a.job);c=read(job/'config.json')
    if not m['video']['audio']:raise ValueError('Video has no audio; import existing subtitles instead')
    raw=job/'raw.json'
    if (job/'captions.json').exists():raise ValueError('captions.json exists; refusing to retranscribe over reviewed captions')
    if raw.exists():raise ValueError('raw.json exists. Keep it and edit captions.json, or create a new job to retranscribe')
    backend=c.get('backend','mlx')
    prompt=transcriptionprompt(c.get('terms',[]))
    with tempfile.TemporaryDirectory(prefix='audio-',dir=job) as td:
        wav=Path(td)/'audio.wav'
        run([ffmpeg(),'-v','error','-i',m['video']['path'],'-map','0:a:0','-vn','-ac','1','-ar','16000','-c:a','pcm_s16le',wav])
        if backend=='mlx':
            import mlx_whisper, wave, numpy as np
            with wave.open(str(wav),'rb') as audio:
                samples=np.frombuffer(audio.readframes(audio.getnframes()),dtype=np.int16).astype(np.float32)/32768.0
            from contextlib import redirect_stdout
            with redirect_stdout(sys.stderr):
                result=mlx_whisper.transcribe(samples,path_or_hf_repo=c['model'],language=c.get('language') or None,word_timestamps=True,initial_prompt=prompt,condition_on_previous_text=False,verbose=False)
        elif backend=='faster-whisper':
            from faster_whisper import WhisperModel
            model=WhisperModel(c['model'],device='cpu',compute_type='int8')
            segs,info=model.transcribe(str(wav),language=c.get('language') or None,word_timestamps=True,initial_prompt=prompt,vad_filter=True,condition_on_previous_text=False)
            result={'segments':[dict(start=s.start,end=s.end,text=s.text,avg_logprob=s.avg_logprob,no_speech_prob=s.no_speech_prob,words=[dict(word=w.word,start=w.start,end=w.end,probability=w.probability) for w in (s.words or [])]) for s in segs]}
        else:raise ValueError('Supported backends: mlx, faster-whisper')
    save(raw,result)
    cues=[dict(start=s['start'],end=s['end'],text=s['text'].strip(),words=s.get('words',[])) for s in result['segments'] if s['text'].strip()]
    # Manual captions remain authoritative; never replace them.
    if (job/'captions.json').exists():raise ValueError('captions.json exists; raw saved, manual captions preserved')
    save(job/'captions.json',cues)
    save(job/'transcription-run.json',dict(backend=backend,model=c['model'],terms=c.get('terms',[]),video_sha256=m['video_sha256']))
    emit(dict(cues=len(cues),raw=str(raw),next='Review captions.json using audio; then prepare'))

def secs(s):
    h,m,v=s.replace(',','.').split(':');return int(h)*3600+int(m)*60+float(v)
def importsrt(a):
    job,m=loadjob(a.job)
    if (job/'captions.json').exists():raise ValueError('captions.json already exists; manual captions preserved')
    text=Path(a.srt).read_text(encoding='utf-8-sig').replace('\r\n','\n').strip();cues=[]
    for block in re.split(r'\n\s*\n',text):
        lines=block.splitlines();k=next((i for i,l in enumerate(lines) if '-->' in l),None)
        if k is None:raise ValueError('Invalid SRT block')
        t=lines[k].split('-->')
        cues.append(dict(start=secs(t[0].strip()),end=secs(t[1].strip()),text=' '.join(lines[k+1:]).strip()))
    shutil.copyfile(a.srt,job/'original.srt');save(job/'captions.json',cues);emit(dict(imported=len(cues)))

def importtranslations(a):
    job,m=loadjob(a.job);captions=read(job/'captions.json');target=job/'translations.json'
    if target.exists():raise ValueError('translations.json exists; refusing overwrite')
    data=read(a.json)
    if data.get('version')!=1 or not isinstance(data.get('target_language'),str) or not data['target_language'].strip():
        raise ValueError('Translation file needs version 1 and target_language')
    rows=data.get('cues')
    if not isinstance(rows,list) or len(rows)!=len(captions):raise ValueError('Provide exactly one translated row for every source cue')
    seen=set();clean=[]
    for row in rows:
        ix=row.get('source_cue');translated=row.get('text')
        if not isinstance(ix,int) or not 1<=ix<=len(captions) or ix in seen:raise ValueError('Invalid or duplicate source_cue in translation')
        if not isinstance(translated,str) or not translated.strip():raise ValueError(f'Empty translation for source cue {ix}')
        if row.get('source_text') is not None and row['source_text'].strip()!=captions[ix-1]['text'].strip():raise ValueError(f'Source text mismatch at cue {ix}')
        if any(x in translated for x in ['{','}','\\','\x00']):raise ValueError(f'Translation {ix}: ASS control characters require cleanup')
        clean.append(dict(source_cue=ix,source_text=captions[ix-1]['text'].strip(),text=translated.strip()));seen.add(ix)
    clean.sort(key=lambda x:x['source_cue'])
    save(target,dict(version=1,target_language=data['target_language'].strip(),source_captions_sha256=sha(job/'captions.json'),cues=clean))
    emit(dict(imported=len(clean),target_language=data['target_language'].strip(),next='Review translations.json, then prepare'))

def applyterms(a):
    job,m=loadjob(a.job);caption_path=job/'captions.json';captions=read(caption_path);config=read(job/'config.json');data=read(a.json)
    rows=data.get('corrections')
    if data.get('version')!=1 or not isinstance(rows,list) or not rows:raise ValueError('Correction file needs version 1 and a non-empty corrections array')
    allowed={str(t).casefold() for t in config.get('terms',[])};edits=[]
    for row in rows:
        ix=row.get('source_cue');old=row.get('from');new=row.get('to');evidence=row.get('evidence')
        if not isinstance(ix,int) or not 1<=ix<=len(captions):raise ValueError('Invalid source_cue in correction')
        if not all(isinstance(x,str) and x.strip() for x in [old,new,evidence]):raise ValueError(f'Correction {ix} needs from, to, and evidence')
        if new.casefold() not in allowed:raise ValueError(f'Correction target must be listed in config.terms: {new}')
        text=captions[ix-1]['text']
        if text.count(old)!=1:raise ValueError(f'Correction source must occur exactly once in cue {ix}: {old}')
        captions[ix-1]['text']=text.replace(old,new,1);edits.append(dict(source_cue=ix,old=old,new=new,evidence=evidence))
    backups=job/'backups';backups.mkdir(exist_ok=True);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=backups/(stamp+'-captions-before-term-correction.json');shutil.copyfile(caption_path,backup);save(caption_path,captions)
    history=read(job/'edits.json') if (job/'edits.json').exists() else []
    history.append(dict(timestamp=stamp,kind='reviewed_term_correction',edits=edits));save(job/'edits.json',history)
    emit(dict(applied=len(edits),backup=str(backup),next='Review captions.json, then prepare'))

def color(s,opacity=1):
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',s):raise ValueError('Colors must be #RRGGBB')
    return f'&H{round((1-opacity)*255):02X}{s[5:7]}{s[3:5]}{s[1:3]}'.upper()
def override_color(s):return '&H'+color(s)[4:]+'&'
def timestamp(s,ass=False):
    n=round(s*(100 if ass else 1000));h,n=divmod(n,360000 if ass else 3600000);m,n=divmod(n,6000 if ass else 60000);v,n=divmod(n,100 if ass else 1000)
    return f'{h}:{m:02}:{v:02}.{n:02}' if ass else f'{h:02}:{m:02}:{v:02},{n:03}'
def fontdata(path,size):
    from PIL import ImageFont
    from fontTools.ttLib import TTFont
    p=Path(path).expanduser().resolve()
    if not p.is_file():raise ValueError('Set config.font_path to an existing .ttf/.otf font')
    tt=TTFont(str(p));cmap=tt.getBestCmap();family=tt['name'].getDebugName(1);tt.close()
    if not family or ',' in family:raise ValueError('Unsupported font family name')
    return ImageFont.truetype(str(p),size),cmap,family,p

def tokens(text):
    import jieba
    return [t for t in jieba.cut(text,HMM=False) if t]
def twolines(tok,font,width):
    text=''.join(tok).strip()
    if font.getlength(text)<=width:return [text]
    options=[]
    for i in range(1,len(tok)):
        l=''.join(tok[:i]).strip();r=''.join(tok[i:]).strip()
        if not l or not r or r[0] in '，。！？；：、,.!?;:)]）】':continue
        a,b=font.getlength(l),font.getlength(r)
        if max(a,b)<=width:options.append((abs(a-b),[l,r]))
    return min(options,key=lambda x:x[0])[1] if options else None

def boundaries(cue):
    """Use word spans only when their text still equals the reviewed caption."""
    text=cue['text'].strip();words=cue.get('words',[])
    compact=lambda s:re.sub(r'\s','',s)
    if not words or compact(''.join(w['word'] for w in words))!=compact(text):return None
    spans=[];offset=0
    for w in words:
        n=len(compact(w['word']))
        spans.append((offset,offset+n,float(w['start']),float(w['end'])));offset+=n
    return spans

def styleeffects(job,duration):
    p=job/'style-effects.json'
    if not p.exists():return []
    data=read(p);rows=data.get('effects')
    if data.get('version')!=1 or not isinstance(rows,list):raise ValueError('style-effects.json needs version 1 and an effects array')
    clean=[]
    for i,row in enumerate(rows,1):
        start=row.get('start');end=row.get('end');scale=row.get('font_scale',1);transition=row.get('transition_ms',120);tone=row.get('text_color')
        if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in [start,end,scale,transition]):raise ValueError(f'Invalid style effect {i}')
        if not 0<=start<end<=duration or not .5<=scale<=3 or not 0<=transition<=1000:raise ValueError(f'Out-of-range style effect {i}')
        if tone is not None:color(tone)
        clean.append(dict(start=float(start),end=float(end),font_scale=float(scale),transition_ms=float(transition),text_color=tone))
    return clean

def effecttags(cue,effects,base_color):
    tags=[]
    for row in effects:
        if row['end']<=cue['start'] or row['start']>=cue['end']:continue
        start=max(row['start'],cue['start']);end=min(row['end'],cue['end']);span=max(0,(end-start)*1000)
        transition=min(row['transition_ms'],span/2);s=max(0,(start-cue['start'])*1000);e=max(s,(end-cue['start'])*1000)
        target=f"\\fscx{round(row['font_scale']*100)}\\fscy{round(row['font_scale']*100)}"
        if row.get('text_color'):target+='\\1c'+override_color(row['text_color'])
        reset='\\fscx100\\fscy100\\1c'+override_color(base_color)
        if row['start']<=cue['start']:tags.append(target)
        elif transition:tags.append(f'\\t({round(s)},{round(s+transition)},{target})')
        else:tags.append(f'\\t({round(s)},{round(s+1)},{target})')
        if row['end']<cue['end']:
            if transition:tags.append(f'\\t({round(e-transition)},{round(e)},{reset})')
            else:tags.append(f'\\t({round(e)},{round(e+1)},{reset})')
    return ''.join(tags)

def prepare(a):
    job,m=loadjob(a.job);c=read(job/'config.json');rawcues=read(job/'captions.json');v=m['video'];warnings=[];out=[]
    translations=read(job/'translations.json') if (job/'translations.json').exists() else None
    if translations and translations.get('source_captions_sha256')!=sha(job/'captions.json'):raise ValueError('Captions changed after translation import; review and import translations again')
    translated={x['source_cue']:x['text'] for x in translations['cues']} if translations else {};effects=styleeffects(job,v['duration'])
    if c.get('max_lines')!=2:raise ValueError('max_lines must be exactly 2')
    for k in ('font_size_ratio','min_font_size_ratio','margin_x_ratio','margin_y_ratio'):
        if not isinstance(c.get(k),(float,int)) or not 0<c[k]<.4:raise ValueError(f'Invalid {k}')
    if c['min_font_size_ratio']>c['font_size_ratio']:raise ValueError('min font size exceeds chosen size')
    if not 0<=c['background_opacity']<=1:raise ValueError('Invalid opacity')
    if c['position'] not in ['top','bottom']:raise ValueError('position must be top or bottom')
    for k in ('max_cps','min_duration','max_duration'):
        if not isinstance(c.get(k),(int,float)) or not math.isfinite(c[k]) or c[k]<=0:raise ValueError(f'Invalid {k}')
    if not isinstance(c.get('outline_px'),(int,float)) or not 0<=c['outline_px']<=30:raise ValueError('Invalid outline_px')
    if not isinstance(c.get('terms'),list) or any(not isinstance(t,str) for t in c['terms']):raise ValueError('terms must be a string array')
    translation_scale=c.get('translation_font_scale',.78);translation_color=c.get('translation_color','#D6E4FF')
    if not isinstance(translation_scale,(int,float)) or not .5<=translation_scale<=1:raise ValueError('translation_font_scale must be 0.5..1')
    color(translation_color)
    size=max(1,round(v['height']*c['font_size_ratio']));minimum=max(1,round(v['height']*c['min_font_size_ratio']))
    font,cmap,family,fontpath=fontdata(c['font_path'],size)
    width=int(v['width']*(1-2*c['margin_x_ratio']))-max(12,c['outline_px']*4)
    ascent,descent=font.getmetrics()
    if 2*(ascent+descent)+c['outline_px']*4 > v['height']*(1-2*c['margin_y_ratio']):raise ValueError('Two-line font height exceeds safe area; reduce font or margins')
    previous=0
    for ix,cu in enumerate(rawcues):
        start,end=float(cu['start']),float(cu['end']);text=cu['text'].strip()
        if not all(map(math.isfinite,[start,end])) or start<previous-.001 or end<=start or end>v['duration']+.05:raise ValueError(f'Invalid/overlapping/out-of-range timing at cue {ix+1}')
        previous=end
        if not text:continue
        if any(x in text for x in ['{','}','\\','\x00']):raise ValueError(f'Cue {ix+1}: ASS control characters require explicit manual cleanup')
        second=translated.get(ix+1);checked_text=text+(second or '')
        if second and any(x in second for x in ['{','}','\\','\x00']):raise ValueError(f'Translation {ix+1}: ASS control characters require cleanup')
        missing=sorted({ch for ch in checked_text if not ch.isspace() and ord(ch) not in cmap})
        if missing:raise ValueError(f'Font missing glyphs in cue {ix+1}: {missing}')
        if translations:
            if second is None:raise ValueError(f'Missing translation for cue {ix+1}')
            chosen=None
            for small in range(size,minimum-1,-1):
                first_font,_,_,_=fontdata(fontpath,small);second_size=max(1,round(small*translation_scale));second_font,_,_,_=fontdata(fontpath,second_size)
                if first_font.getlength(text)<=width and second_font.getlength(second)<=width:chosen=(small,second_size);break
            if not chosen:raise ValueError(f'Bilingual cue {ix+1} cannot fit as two lines; split and retime the source cue and translation')
            length=len(re.sub(r'\s','',text));cps=length/max(end-start,.001)
            if cps>c['max_cps']:warnings.append(dict(cue=ix+1,start=start,kind='reading_speed',cps=round(cps,2)))
            if chosen[0]!=size:warnings.append(dict(cue=ix+1,start=start,kind='smaller_font',size=chosen[0]))
            out.append(dict(start=start,end=end,lines=[text,second],font_size=chosen[0],translation_font_size=chosen[1],source_cue=ix+1,bilingual=True));continue
        tok=tokens(re.sub(r'\s+',' ',text));groups=[];pending=[]
        for t in tok:
            if pending and not twolines(pending+[t],font,width):
                # Prefer a sentence/clause boundary; never orphan closing punctuation.
                choices=[i+1 for i,z in enumerate(pending) if re.search(r'[，。！？；：,.!?;:]$',z) and i+1<len(pending)]
                cut=choices[-1] if choices else len(pending)
                if t[:1] in '，。！？；：、,.!?;:)]）】':cut=min(cut,len(pending)-1)
                if cut<=0:raise ValueError(f'Cue {ix+1}: punctuation cannot fit; reduce font size or revise split')
                groups.append(pending[:cut]);pending=pending[cut:]
                if pending and not twolines(pending+[t],font,width):
                    groups.append(pending);pending=[]
            pending.append(t)
        if pending:groups.append(pending)
        spans=boundaries(cu);total=len(re.sub(r'\s','',text));offset=0
        for g in groups:
            lines=twolines(g,font,width);actual=size
            if lines is None:
                for small in range(size-1,minimum-1,-1):
                    f,_,_,_=fontdata(fontpath,small);lines=twolines(g,f,width)
                    if lines:actual=small;break
            if not lines:raise ValueError(f'Cue {ix+1}: unbreakable token exceeds two-line layout; adjust text/font/margins')
            length=len(re.sub(r'\s','',''.join(g)))
            if len(groups)==1:s,e=start,end
            elif spans:
                overlap=[w for w in spans if w[1]>offset and w[0]<offset+length]
                s,e=(overlap[0][2],overlap[-1][3]) if overlap else (start,end)
                if out and s<out[-1]['end']-.001:raise ValueError('Word timing overlaps; review caption boundaries')
            else:
                s=start+(end-start)*offset/max(total,1);e=start+(end-start)*(offset+length)/max(total,1)
                warnings.append(dict(cue=ix+1,start=s,kind='estimated_split_timing',message='Split timing interpolated; listen and correct before final delivery'))
            offset+=length
            cps=length/max(e-s,.001)
            if cps>c['max_cps']:warnings.append(dict(cue=ix+1,start=s,kind='reading_speed',cps=round(cps,2)))
            if e-s<c['min_duration'] or e-s>c['max_duration']:warnings.append(dict(cue=ix+1,start=s,kind='duration',seconds=e-s))
            if re.search(r'\d', ''.join(g)):warnings.append(dict(cue=ix+1,start=s,kind='check_numbers'))
            if actual!=size:warnings.append(dict(cue=ix+1,start=s,kind='smaller_font',size=actual))
            out.append(dict(start=s,end=e,lines=lines,font_size=actual,source_cue=ix+1))
    if not out:raise ValueError('No subtitles')
    for i,x in enumerate(out):
        if not all(math.isfinite(x[k]) for k in ['start','end']) or x['start']<0 or x['end']>v['duration']+.05:raise ValueError('Word timing outside source video')
        if round(x['end']*100)<=round(x['start']*100):raise ValueError('Cue too short for ASS centisecond precision')
        if i and x['start']<out[i-1]['end']-.001:raise ValueError('Layout time overlap')
    raw=read(job/'raw.json') if (job/'raw.json').exists() else {}
    for s in raw.get('segments',[]):
        for w in s.get('words',[]):
            if w.get('probability',1)<.5:warnings.append(dict(start=w['start'],kind='word_uncertain',text=w['word']))
        if s.get('avg_logprob',0)<-.65 or s.get('no_speech_prob',0)>.5:warnings.append(dict(start=s['start'],kind='asr_uncertain',text=s['text']))
    for i in range(1,len(rawcues)):
        if rawcues[i]['text'].strip()==rawcues[i-1]['text'].strip():warnings.append(dict(cue=i+1,start=rawcues[i]['start'],kind='repeated_text'))
    for term in c.get('terms',[]):
        if term.casefold() not in ' '.join(x['text'] for x in rawcues).casefold():warnings.append(dict(kind='term_not_found',term=term,message='Hint only; do not insert terms without audio evidence'))
    revisions=job/'revisions';revisions.mkdir(exist_ok=True)
    revision=revisions/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));revision.mkdir()
    shutil.copyfile(job/'captions.json',revision/'captions.json');shutil.copyfile(job/'config.json',revision/'config.json')
    for optional in ['translations.json','style-effects.json','edits.json']:
        if (job/optional).exists():shutil.copyfile(job/optional,revision/optional)
    (revision/'fonts').mkdir();shutil.copyfile(fontpath,revision/'fonts'/('font'+fontpath.suffix))
    mx=round(v['width']*c['margin_x_ratio']);my=round(v['height']*c['margin_y_ratio']);alignment=2 if c['position']=='bottom' else 8
    primary=color(c['text_color']);back=color(c['background_color'],c['background_opacity']);outline=color(c['outline_color'])
    boxed=c['background_opacity']>0
    ass=f'''[Script Info]
ScriptType: v4.00+
PlayResX: {v['width']}
PlayResY: {v['height']}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{family},{size},{primary},{primary},{back if boxed else outline},{back},0,0,0,0,100,100,0,0,{3 if boxed else 1},{c['outline_px']},0,{alignment},{mx},{mx},{my},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    for x in out:
        if x.get('bilingual'):text=x['lines'][0]+'\\N{\\fs'+str(x['translation_font_size'])+'\\1c'+override_color(translation_color)+'}'+x['lines'][1]
        else:text='\\N'.join(x['lines'])
        tag='{\\q2\\fs'+str(x['font_size'])+effecttags(x,effects,c['text_color'])+'}'
        ass+=f"Dialogue: 0,{timestamp(x['start'],True)},{timestamp(x['end'],True)},Default,,0,0,0,,{tag}{text}\n"
    (revision/'subtitles.ass').write_text(ass,encoding='utf-8')
    (revision/'subtitles.srt').write_text('\n\n'.join(f"{i}\n{timestamp(x['start'])} --> {timestamp(x['end'])}\n"+'\n'.join(x['lines']) for i,x in enumerate(out,1))+'\n',encoding='utf-8')
    save(revision/'layout.json',out)
    report=dict(version=VERSION,status='prepared_needs_visual_and_audio_review',max_lines=max(len(x['lines']) for x in out),cues=len(out),bilingual=bool(translations),target_language=translations.get('target_language') if translations else None,style_effects=len(effects),warnings=warnings,not_checked=['semantic_accuracy','translation_accuracy','full_audio_sync','silence_hallucinations_without_VAD','important_UI_occlusion','visual_render_bounds'],video_sha256=m['video_sha256'],captions_sha256=sha(revision/'captions.json'),translations_sha256=sha(revision/'translations.json') if translations else None,style_effects_sha256=sha(revision/'style-effects.json') if effects else None,font_sha256=sha(revision/'fonts'/('font'+fontpath.suffix)))
    save(revision/'report.json',report);save(job/'latest.json',{'revision':str(revision)})
    emit(dict(revision=str(revision),cues=len(out),warnings=len(warnings),next='preview; inspect images and listen, then render if requested'))

def render(a):
    job,m=loadjob(a.job);rev=Path(read(job/'latest.json')['revision']);v=m['video'];full=a.command=='render'
    destination=rev/('video.mp4' if full else f'preview-{a.start:g}.mp4')
    if destination.exists():raise ValueError(f'Output exists, refusing overwrite: {destination}')
    start=0 if full else a.start;duration=v['duration'] if full else min(a.seconds,v['duration']-start)
    if start<0 or duration<=0:raise ValueError('Invalid preview range')
    cmd=[ffmpeg(),'-hide_banner','-v','warning','-nostdin','-i',v['path'],'-map','0:v:0','-map','0:a:0?','-vf','ass=subtitles.ass:fontsdir=fonts']
    # Output seek is deliberately after subtitles so ASS remains on source timestamps.
    if not full:cmd+=['-ss',str(start),'-t',str(duration)]
    cmd+=['-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(destination)]
    logfile=destination.with_suffix('.log')
    with logfile.open('w') as log:
        result=subprocess.run(cmd,cwd=rev,stdout=log,stderr=log)
    if result.returncode:raise RuntimeError(f'Render failed; inspect {logfile}; partial output is not complete')
    output=probe(destination)
    if abs(output['duration']-duration)>.3 or output['audio']!=v['audio']:raise ValueError('Output duration/audio-presence check failed')
    run([ffmpeg(),'-v','error','-i',destination,'-f','null','-'])
    if not full:
        for i,fraction in enumerate([.1,.5,.9]):
            run([ffmpeg(),'-v','error','-ss',str(duration*fraction),'-i',destination,'-frames:v','1',rev/f'preview-{start:g}-{i}.png'])
    verification=dict(status='decoded_metadata_passed_visual_audio_review_required',output=output,source_start=start,source_duration=duration,not_checked=['human_audio_sync','full_visual_bounds','semantic_accuracy'],audio_reencoded=True)
    save(destination.with_suffix('.verification.json'),verification);emit(verification)

def doctor(a):
    import importlib.util
    x={k:importlib.util.find_spec(k) is not None for k in ['PIL','fontTools','jieba','mlx_whisper','faster_whisper']}
    filters=run([ffmpeg(),'-hide_banner','-filters']).stdout
    emit(dict(version=VERSION,python=sys.executable,ffmpeg=ffmpeg(),ass_filter=bool(re.search(r'\bass\s',filters)),packages=x,machine_config=machine(),default_font=default_font_path(),bundled_font=BUNDLED_FONT.is_file(),style_presets=STYLE_PRESETS))

def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor')
    q=sub.add_parser('init');q.add_argument('--video',required=True);q.add_argument('--job',required=True);q.add_argument('--font');q.add_argument('--preset',choices=sorted(STYLE_PRESETS),default='standard');q.add_argument('--language',default='auto')
    for name in ['transcribe','prepare','preview','render','import-srt','import-translations','apply-terms']:
        q=sub.add_parser(name);q.add_argument('--job',required=True)
        if name=='import-srt':q.add_argument('--srt',required=True)
        if name in ['import-translations','apply-terms']:q.add_argument('--json',required=True)
        if name=='preview':q.add_argument('--start',type=float,default=0);q.add_argument('--seconds',type=float,default=8)
    a=p.parse_args()
    try:{'doctor':doctor,'init':init,'transcribe':transcribe,'import-srt':importsrt,'import-translations':importtranslations,'apply-terms':applyterms,'prepare':prepare,'preview':render,'render':render}[a.command](a)
    except Exception as e:emit({'ok':False,'error':str(e)});sys.exit(1)
if __name__=='__main__':main()
