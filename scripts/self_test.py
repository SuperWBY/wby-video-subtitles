"""Regression checks for isolation, text preservation, two-line layout and fail-closed behavior."""
import argparse, contextlib, io, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
import subtitles as s

class Pipeline(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.job=Path(self.temp.name)
        self.video=self.job/'input.mp4';self.video.write_bytes(b'unique input fingerprint')
        s.save(self.job/'manifest.json',{'video':dict(path=str(self.video),width=720,height=1280,duration=30,audio=True),'video_sha256':s.sha(self.video)})
        self.config=dict(font_path=s.machine()['font_path'],font_size_ratio=.045,min_font_size_ratio=.035,text_color='#FFFFFF',background_color='#000000',background_opacity=.55,outline_color='#181818',outline_px=2,margin_x_ratio=.06,margin_y_ratio=.06,position='bottom',max_lines=2,max_cps=12,min_duration=.5,max_duration=6,terms=[])
        s.save(self.job/'config.json',self.config)
        self.text='这是一段用于测试的长字幕，我们希望完整保留所有文字，并且任何时候最多只能显示两行，同时让不同的视频使用独立的配置。'
        s.save(self.job/'captions.json',[dict(start=0,end=20,text=self.text)])
        self.arg=SimpleNamespace(job=str(self.job))
    def tearDown(self):self.temp.cleanup()
    def prep(self):
        with contextlib.redirect_stdout(io.StringIO()):s.prepare(self.arg)
        return Path(s.read(self.job/'latest.json')['revision'])
    def test_preserve_text_and_two_lines(self):
        r=self.prep();layout=s.read(r/'layout.json')
        self.assertGreater(len(layout),1)
        self.assertEqual(''.join(''.join(c['lines']) for c in layout),self.text)
        self.assertTrue(all(1<=len(c['lines'])<=2 for c in layout))
        self.assertTrue(any(w['kind']=='estimated_split_timing' for w in s.read(r/'report.json')['warnings']))
        for c in layout:
            font,_,_,_=s.fontdata(self.config['font_path'],c['font_size'])
            self.assertTrue(all(font.getlength(l)<=720*.88 for l in c['lines']))
    def test_no_orphan_punctuation(self):
        self.config['font_size_ratio']=.05
        s.save(self.job/'config.json',self.config)
        text='这是一段专门用于测试字幕排版的文字，它不是原视频的口播内容。我们用较长的句子检查字体、背景颜色以及自动分行，确保文字没有丢失，而且每一条字幕最多只能显示两行。'
        s.save(self.job/'captions.json',[dict(start=0,end=20,text=text)])
        r=self.prep()
        for cue in s.read(r/'layout.json'):
            self.assertNotIn(cue['lines'][0][0],'，。！？；：、')
    def test_changes_preserve_previous_revision(self):
        r=self.prep();before=(r/'subtitles.ass').read_bytes();captions=(self.job/'captions.json').read_bytes()
        self.config['text_color']='#FFFF00';s.save(self.job/'config.json',self.config)
        r2=self.prep();self.assertNotEqual(r,r2);self.assertEqual((r/'subtitles.ass').read_bytes(),before)
        self.assertEqual((self.job/'captions.json').read_bytes(),captions)
        self.assertNotEqual((r2/'subtitles.ass').read_bytes(),before)
    def test_video_mutation_refused(self):
        self.video.write_bytes(b'another video')
        with self.assertRaisesRegex(ValueError,'Video changed'):self.prep()
    def test_three_lines_refused(self):
        self.config['max_lines']=3;s.save(self.job/'config.json',self.config)
        with self.assertRaisesRegex(ValueError,'exactly 2'):self.prep()
    def test_overlapping_time_refused(self):
        s.save(self.job/'captions.json',[dict(start=0,end=4,text='你好'),dict(start=3,end=5,text='世界')])
        with self.assertRaisesRegex(ValueError,'overlapping'):self.prep()
    def test_long_unbreakable_word_refused(self):
        s.save(self.job/'captions.json',[dict(start=0,end=10,text='a'*180)])
        with self.assertRaisesRegex(ValueError,'unbreakable'):self.prep()
    def test_missing_glyph_refused(self):
        s.save(self.job/'captions.json',[dict(start=0,end=10,text='\U0010ffff')])
        with self.assertRaisesRegex(ValueError,'missing glyphs'):self.prep()
    def test_import_preserves_manual_captions(self):
        with self.assertRaisesRegex(ValueError,'already exists'):s.importsrt(SimpleNamespace(job=str(self.job),srt='/does/not/exist'))
    def test_ass_control_refused(self):
        s.save(self.job/'captions.json',[dict(start=0,end=10,text='{\\fs200}hello')])
        with self.assertRaisesRegex(ValueError,'control characters'):self.prep()

    def test_dynamic_scale_and_color_effects(self):
        s.save(self.job/'captions.json',[dict(start=0,end=5,text='看字幕变大，再变成黄色')])
        s.save(self.job/'style-effects.json',{'version':1,'effects':[{'start':1,'end':3,'font_scale':1.6,'text_color':'#FFFF00','transition_ms':120}]})
        ass=(self.prep()/'subtitles.ass').read_text()
        self.assertIn('\\fscx160\\fscy160',ass)
        self.assertIn('\\1c&H00FFFF&',ass)
        self.assertIn('\\t(',ass)
        self.assertTrue((Path(s.read(self.job/'latest.json')['revision'])/'style-effects.json').exists())

    def test_bilingual_import_and_two_line_layout(self):
        s.save(self.job/'captions.json',[dict(start=0,end=5,text='字幕可以自动适配画布')])
        source=self.job/'translated-input.json'
        s.save(source,{'version':1,'target_language':'en','cues':[{'source_cue':1,'source_text':'字幕可以自动适配画布','text':'Subtitles adapt to the video canvas.'}]})
        with contextlib.redirect_stdout(io.StringIO()):s.importtranslations(SimpleNamespace(job=str(self.job),json=str(source)))
        r=self.prep();layout=s.read(r/'layout.json');report=s.read(r/'report.json')
        self.assertEqual(2,len(layout[0]['lines']))
        self.assertEqual('Subtitles adapt to the video canvas.',layout[0]['lines'][1])
        self.assertTrue(report['bilingual']);self.assertEqual('en',report['target_language'])
        self.assertTrue((r/'translations.json').exists())

    def test_reviewed_term_correction_is_logged_and_backed_up(self):
        s.save(self.job/'captions.json',[dict(start=0,end=5,text='我使用飞个马制作海报')])
        self.config['terms']=['Figma'];s.save(self.job/'config.json',self.config)
        source=self.job/'corrections.json'
        s.save(source,{'version':1,'corrections':[{'source_cue':1,'from':'飞个马','to':'Figma','evidence':'listened to source audio'}]})
        with contextlib.redirect_stdout(io.StringIO()):s.applyterms(SimpleNamespace(job=str(self.job),json=str(source)))
        self.assertEqual('我使用Figma制作海报',s.read(self.job/'captions.json')[0]['text'])
        self.assertEqual('reviewed_term_correction',s.read(self.job/'edits.json')[0]['kind'])
        self.assertEqual(1,len(list((self.job/'backups').glob('*-captions-before-term-correction.json'))))

    def test_canvas_height_controls_base_font_size(self):
        manifest=s.read(self.job/'manifest.json');manifest['video']['width']=1920;manifest['video']['height']=1080;s.save(self.job/'manifest.json',manifest)
        s.save(self.job/'captions.json',[dict(start=0,end=5,text='横版视频字幕')]);landscape=self.prep()
        self.assertEqual(round(1080*self.config['font_size_ratio']),s.read(landscape/'layout.json')[0]['font_size'])

if __name__=='__main__':unittest.main()
