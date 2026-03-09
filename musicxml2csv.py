#First of all, please change the extension from .py to .ipynb.
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MusicXML to CSV Converter
"""

import os
import re
import pandas as pd
import xml.etree.ElementTree as ET
from music21 import converter, note, chord, tempo as m21_tempo
from typing import List, Dict, Tuple, Optional
from pathlib import Path

RH_SET = {"p", "i", "m", "a", "c"}

def _accidental_string(alter):
    if alter is None:
        return ""
    try:
        a = int(alter)
    except Exception:
        return ""
    if a > 0:
        return "#" * a
    if a < 0:
        return "b" * (-a)
    return ""

def _round5(x):
    return round(float(x), 5)

def _safe_int(x, default=None):
    try:
        return int(x)
    except Exception:
        return default


def xml_notes_with_timing(xml_path):
    """XMLから音符情報を抽出（時系列順）"""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    ns = {"m": root.tag.split("}")[0].strip("{")} if "}" in root.tag else {}
    def tag(name): return f"{{{ns['m']}}}{name}" if ns else name

    notes = []
    current_measure = 0
    divisions = 1

    for measure in root.iter(tag("measure")):
        current_measure = _safe_int(measure.get("number"), default=(current_measure + 1))
        
        attr = measure.find(tag("attributes"))
        if attr is not None:
            div_tag = attr.find(tag("divisions"))
            if div_tag is not None and div_tag.text and div_tag.text.isdigit():
                divisions = int(div_tag.text)
        
        if divisions is None or divisions == 0:
            divisions = 1
        
        current_time = 0
        
        for elem in measure:
            if elem.tag == tag("backup"):
                dur_tag = elem.find(tag("duration"))
                if dur_tag is not None and dur_tag.text:
                    backup_dur = _safe_int(dur_tag.text, 0)
                    current_time -= backup_dur
                continue
            
            if elem.tag == tag("forward"):
                dur_tag = elem.find(tag("duration"))
                if dur_tag is not None and dur_tag.text:
                    forward_dur = _safe_int(dur_tag.text, 0)
                    current_time += forward_dur
                continue
            
            if elem.tag == tag("note"):
                if elem.find(tag("rest")) is not None:
                    is_chord = (elem.find(tag("chord")) is not None)
                    if not is_chord:
                        dur_tag = elem.find(tag("duration"))
                        dur_div = _safe_int(dur_tag.text, 0) if dur_tag is not None and dur_tag.text else 0
                        current_time += dur_div
                    continue
                
                pitch_tag = elem.find(tag("pitch"))
                if pitch_tag is None:
                    continue
                
                is_chord = (elem.find(tag("chord")) is not None)
                is_grace = (elem.find(tag("grace")) is not None)
                
                offset_q = (current_time / divisions) if divisions and divisions != 0 else 0.0
                
                step = pitch_tag.findtext(tag("step")) or ""
                alter = pitch_tag.findtext(tag("alter"))
                octave = pitch_tag.findtext(tag("octave")) or ""
                acc = _accidental_string(alter)
                
                try:
                    from music21 import pitch as m21_pitch
                    pitch_str = m21_pitch.Pitch(f"{step}{acc}{octave}").nameWithOctave
                    pitch_midi = m21_pitch.Pitch(f"{step}{acc}{octave}").midi
                except Exception:
                    pitch_str = f"{step}{acc}{octave}"
                    pitch_midi = None
                
                tech = elem.find(f"{tag('notations')}/{tag('technical')}")
                left_list, string_list, pluck_list = [], [], []
                if tech is not None:
                    for f in tech.findall(tag("fingering")):
                        if f.text:
                            v = f.text.strip()
                            if re.fullmatch(r"[0-4Tt]", v) or v.isdigit():
                                left_list.append(v)
                    for s in tech.findall(tag("string")):
                        if s.text and s.text.strip().isdigit():
                            sn = int(s.text.strip())
                            if 1 <= sn <= 6:
                                string_list.append(str(sn))
                    for p in tech.findall(tag("pluck")):
                        if p.text:
                            q = p.text.strip().lower()
                            if q in RH_SET:
                                pluck_list.append(q)
                
                notes.append({
                    "measure": current_measure,
                    "offset_q": _round5(offset_q),
                    "pitch": pitch_str,
                    "pitch_midi": pitch_midi,
                    "pluck": "+".join(pluck_list) if pluck_list else "",
                    "fingering": "+".join(left_list) if left_list else "",
                    "string": "+".join(string_list) if string_list else "",
                    "used": False  # マッチング済みフラグ
                })
                
                if not is_chord and not is_grace:
                    dur_tag = elem.find(tag("duration"))
                    dur_div = _safe_int(dur_tag.text, 0) if dur_tag is not None and dur_tag.text else 0
                    current_time += dur_div
    
    # 時系列順にソート（小節 → offset のみ、和音内の順序は保持）
    notes.sort(key=lambda n: (n["measure"], n["offset_q"]))
    
    return notes


class MusicXMLProcessor:
    
    def __init__(self, input_path: str, expand_repeats: bool = False):
        self.input_path = input_path
        self.score = converter.parse(input_path)
        self.current_tempo = 120.0
        self.expand_repeats = expand_repeats
        
        # XML音符リストを取得（繰り返し展開なし）
        self.xml_notes = xml_notes_with_timing(input_path)
    
    def get_xml_note_by_pitch(self, measure: int, offset_q: float, pitch_midi: int) -> Optional[Dict]:
        """
        同じ位置でピッチが一致するXML音符を検索（ピッチベースマッチング）
        
        Parameters:
        -----------
        measure : int
            小節番号
        offset_q : float
            小節内のオフセット（四分音符単位）
        pitch_midi : int
            MIDIピッチ番号
        
        Returns:
        --------
        Dict or None
            マッチした音符情報、見つからない場合はNone
        """
        # まず厳密マッチを試みる
        for note in self.xml_notes:
            if (note["measure"] == measure and 
                abs(note["offset_q"] - offset_q) < 0.01 and
                note["pitch_midi"] == pitch_midi and
                not note.get("used", False)):
                note["used"] = True
                return note
        
        # 厳密マッチが失敗した場合、小節番号を±1で緩和して再検索
        for note in self.xml_notes:
            if (abs(note["measure"] - measure) <= 1 and 
                abs(note["offset_q"] - offset_q) < 0.1 and
                note["pitch_midi"] == pitch_midi and
                not note.get("used", False)):
                note["used"] = True
                return note
        
        # それでも見つからない場合、ピッチのみでマッチング（近い位置優先）
        candidates = [
            n for n in self.xml_notes 
            if n["pitch_midi"] == pitch_midi and not n.get("used", False)
        ]
        if candidates:
            # 位置が最も近いものを選択
            best = min(candidates, key=lambda n: (abs(n["measure"] - measure), abs(n["offset_q"] - offset_q)))
            best["used"] = True
            return best
        
        return None
    
    def reset_xml_notes_usage(self):
        """XML音符の使用フラグをリセット"""
        for note in self.xml_notes:
            note["used"] = False
        
    def extract_tempo_map(self) -> List[Tuple[float, float]]:
        tempo_map = []
        for element in self.score.flatten():
            if isinstance(element, m21_tempo.MetronomeMark):
                tempo_map.append((element.offset, element.number))
        
        if not tempo_map:
            tempo_map.append((0.0, 120.0))
        
        return tempo_map
    
    def offset_to_seconds(self, offset: float, tempo_map: List[Tuple[float, float]]) -> float:
        if not tempo_map:
            return 0.0
        
        current_tempo = tempo_map[0][1]
        if current_tempo is None or current_tempo == 0:
            current_tempo = 120.0
            
        current_offset = 0.0
        accumulated_time = 0.0
        
        for i, (tempo_offset, tempo_value) in enumerate(tempo_map):
            if offset < tempo_offset:
                break
            
            if i > 0:
                offset_delta = tempo_offset - current_offset
                accumulated_time += (offset_delta * 60.0) / current_tempo
            
            current_offset = tempo_offset
            current_tempo = tempo_value if tempo_value else 120.0
        
        offset_delta = offset - current_offset
        accumulated_time += (offset_delta * 60.0) / current_tempo
        
        return accumulated_time
    
    def get_expanded_score(self):
        if self.expand_repeats:
            try:
                expanded = self.score.expandRepeats()
                return expanded
            except:
                return self.score
        else:
            return self.score
    
    def extract_notes_with_timing(self) -> pd.DataFrame:
        expanded_score = self.get_expanded_score()
        tempo_map = self.extract_tempo_map()
        
        # 使用フラグをリセット
        self.reset_xml_notes_usage()
        
        notes_data = []
        note_index = 0
        
        # 全音符を時系列順に取得
        all_notes = []
        for element in expanded_score.flatten().notesAndRests:
            if isinstance(element, note.Note):
                all_notes.append((element, [element], False))  # (element, notes, is_chord)
            elif isinstance(element, chord.Chord):
                # 和音はまとめて処理するためにリストで保持
                all_notes.append((element, list(element.notes), True))
        
        # 時系列順に処理
        i = 0
        while i < len(all_notes):
            element, notes_to_process, is_chord_element = all_notes[i]
            
            # 【修正】小節番号はelementから取得（Chord/Note共通）
            meas = element.getContextByClass('Measure')
            measure_number = meas.number if meas else 1
            
            # 小節内のオフセットを計算
            if meas:
                measure_offset = element.offset - meas.offset
            else:
                measure_offset = element.offset
            
            for n in notes_to_process:
                # タイ処理: tie-stopやtie-continueの音符
                if n.tie is not None and n.tie.type in ['continue', 'stop']:
                    # XML情報を消費（ピッチベースで検索）
                    self.get_xml_note_by_pitch(measure_number, measure_offset, n.pitch.midi)
                    continue
                
                # タイ開始の処理
                if n.tie is not None and n.tie.type == 'start':
                    tied_notes = [n]
                    total_duration = n.duration.quarterLength
                    start_offset = element.offset
                    current_pitch_midi = n.pitch.midi
                    
                    # 【修正】XMLからピッチベースで音符情報を取得
                    xml_match = self.get_xml_note_by_pitch(measure_number, measure_offset, n.pitch.midi)
                    
                    # 後続の音符を探す
                    j = i + 1
                    while j < len(all_notes):
                        next_element, next_notes_list, _ = all_notes[j]
                        
                        for next_n in next_notes_list:
                            if (next_n.pitch.midi == current_pitch_midi and 
                                next_n.tie is not None and 
                                next_n.tie.type in ['continue', 'stop']):
                                tied_notes.append(next_n)
                                total_duration += next_n.duration.quarterLength
                                if next_n.tie.type == 'stop':
                                    break
                        
                        if tied_notes[-1].tie.type == 'stop':
                            break
                        j += 1
                    
                    first_note = tied_notes[0]
                    pitch_name = first_note.nameWithOctave
                    pitch_midi = first_note.pitch.midi
                    octave = first_note.pitch.octave
                    absolute_offset = start_offset
                    abs_time = self.offset_to_seconds(absolute_offset, tempo_map)
                    
                    fingering = None
                    string_num = None
                    pluck = xml_match['pluck'] if xml_match and xml_match['pluck'] else None
                    
                    for articulation in first_note.articulations:
                        art_name = articulation.__class__.__name__
                        if art_name == 'Fingering':
                            fingering = articulation.fingerNumber
                        elif art_name == 'StringIndication':
                            string_num = articulation.number
                    
                    if xml_match:
                        if not fingering and xml_match['fingering']:
                            fingering = xml_match['fingering']
                        if not string_num and xml_match['string']:
                            string_num = xml_match['string']
                    
                    note_data = {
                        'note_id': note_index,
                        'measure': measure_number,
                        'offset': absolute_offset,
                        'absolute_time': abs_time,
                        'pitch': pitch_name,
                        'pitch_midi': pitch_midi,
                        'octave': octave,
                        'duration': total_duration,
                        'fingering': fingering,
                        'string': string_num,
                        'pluck': pluck
                    }
                    notes_data.append(note_data)
                    note_index += 1
                
                elif n.tie is not None and n.tie.type in ['continue', 'stop']:
                    # tie-continueやtie-stopは既に処理済みなのでスキップ
                    pass
                
                else:
                    # 通常の音符処理
                    pitch_name = n.nameWithOctave
                    pitch_midi = n.pitch.midi
                    octave = n.pitch.octave
                    duration_quarters = n.duration.quarterLength
                    absolute_offset = element.offset
                    abs_time = self.offset_to_seconds(absolute_offset, tempo_map)
                    
                    # 【修正】XMLからピッチベースで音符情報を取得
                    xml_match = self.get_xml_note_by_pitch(measure_number, measure_offset, pitch_midi)
                    
                    fingering = None
                    string_num = None
                    pluck = xml_match['pluck'] if xml_match and xml_match['pluck'] else None
                    
                    for articulation in n.articulations:
                        art_name = articulation.__class__.__name__
                        if art_name == 'Fingering':
                            fingering = articulation.fingerNumber
                        elif art_name == 'StringIndication':
                            string_num = articulation.number
                    
                    if xml_match:
                        if not fingering and xml_match['fingering']:
                            fingering = xml_match['fingering']
                        if not string_num and xml_match['string']:
                            string_num = xml_match['string']
                    
                    note_data = {
                        'note_id': note_index,
                        'measure': measure_number,
                        'offset': absolute_offset,
                        'absolute_time': abs_time,
                        'pitch': pitch_name,
                        'pitch_midi': pitch_midi,
                        'octave': octave,
                        'duration': duration_quarters,
                        'fingering': fingering,
                        'string': string_num,
                        'pluck': pluck
                    }
                    notes_data.append(note_data)
                    note_index += 1
            
            i += 1
        
        df = pd.DataFrame(notes_data)
        
        if len(df) > 0:
            # 数値列を明示的にfloatに変換（分数表記や日付解釈を避ける）
            df['duration'] = df['duration'].astype(float)
            df['offset'] = df['offset'].astype(float)
            
            df['time_to_next'] = df['absolute_time'].shift(-1) - df['absolute_time']
            df['time_to_next'] = df['time_to_next'].fillna(0)
            
            df['time_from_prev'] = df['absolute_time'] - df['absolute_time'].shift(1)
            df['time_from_prev'] = df['time_from_prev'].fillna(0)
            
            df['end_time'] = df.apply(
                lambda row: self.offset_to_seconds(
                    row['offset'] + row['duration'], tempo_map
                ), axis=1
            )
            
            df['beat'] = ((df['offset'] % 4) + 1).astype(float)
        
        column_order = [
            'note_id', 'measure', 'beat', 'offset', 'absolute_time', 'end_time',
            'pitch', 'pitch_midi', 'octave', 'duration',
            'time_from_prev', 'time_to_next',
            'fingering', 'string', 'pluck'
        ]
        
        existing_cols = [col for col in column_order if col in df.columns]
        df = df[existing_cols]
        
        return df


def add_fret_information(df_notes, fret_pitch_file=None):
    """
    fret-pitch.csvを参照して、各音符にfret情報を付与する
    
    Parameters:
    -----------
    df_notes : DataFrame
        音符データ
    fret_pitch_file : str, optional
        fret-pitch.csvのパス。Noneの場合は現在のディレクトリから探す
    
    Returns:
    --------
    DataFrame
        fret情報が追加されたDataFrame
    """
    # fret-pitch.csvを探す
    if fret_pitch_file is None:
        # 複数の場所を探す
        search_paths = [
            'fret-pitch.csv',
            './fret-pitch.csv',
            os.path.join(os.path.dirname(__file__), 'fret-pitch.csv') if '__file__' in globals() else None,
        ]
        
        fret_pitch_file = None
        for path in search_paths:
            if path and os.path.exists(path):
                fret_pitch_file = path
                break
    
    # fret-pitch.csvが見つからない場合はスキップ
    if fret_pitch_file is None or not os.path.exists(fret_pitch_file):
        print("    fret-pitch.csvが見つかりません。fret情報の付与をスキップします。")
        df_notes['fret'] = ''
        return df_notes
    
    try:
        # fret-pitch.csvを読み込む
        csv2 = pd.read_csv(fret_pitch_file)
        
        # fret列を初期化
        df_notes['fret'] = ''
        
        # 各音符にfret情報を付与
        for index, row in df_notes.iterrows():
            absolute_pitch = row['pitch_midi']
            string = row['string']

            try:
                # absolute_pitch に一致する行番号
                i = csv2.index[csv2['pitch_midi'] == absolute_pitch].tolist()[0]
                
                # string の値は列番号として使う
                j = int(string)
                
                value = csv2.iloc[i, j]
                
            except Exception:
                value = ''

            df_notes.at[index, 'fret'] = value
        
        return df_notes
        
    except Exception as e:
        print(f"    fret情報の付与中にエラー: {e}")
        df_notes['fret'] = ''
        return df_notes


def process_single_file(input_file, output_dir, expand_repeats=False, add_fret=True, fret_pitch_file=None):
    try:
        processor = MusicXMLProcessor(input_file, expand_repeats=expand_repeats)
        df_notes = processor.extract_notes_with_timing()
        
        # fret情報を付与
        if add_fret:
            df_notes = add_fret_information(df_notes, fret_pitch_file)
        
        output_filename = os.path.splitext(os.path.basename(input_file))[0] + "_notes.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        # durationを明示的にfloatとして保存（分数表記を避ける）
        if 'duration' in df_notes.columns:
            df_notes['duration'] = df_notes['duration'].apply(lambda x: float(x) if pd.notna(x) else x)
        
        df_notes.to_csv(output_path, index=False, encoding='utf-8-sig', float_format='%.4f')
        
        pluck_count = df_notes['pluck'].notna().sum()
        fret_count = 0
        if 'fret' in df_notes.columns:
            fret_count = df_notes['fret'].astype(str).str.strip().ne('').sum()
        return True, len(df_notes), pluck_count, fret_count
        
    except Exception as e:
        print(f"    Error: {e}")
        import traceback
        traceback.print_exc()
        return False, 0, 0, 0


def batch_process(input_dir, output_dir, expand_repeats=False, add_fret=True, fret_pitch_file=None):
    print("\n" + "="*60)
    print("MusicXML to CSV 一括変換 (修正版)")
    print("="*60)
    print(f"入力ディレクトリ: {input_dir}")
    print(f"出力ディレクトリ: {output_dir}")
    print(f"繰り返し展開: {'ON' if expand_repeats else 'OFF'}")
    print(f"fret情報付与: {'ON' if add_fret else 'OFF'}")
    print("="*60 + "\n")
    
    os.makedirs(output_dir, exist_ok=True)
    
    musicxml_extensions = ['.musicxml', '.xml', '.mxl']
    files = []
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"❌ ディレクトリが見つかりません: {input_dir}")
        return
    
    for ext in musicxml_extensions:
        files.extend(input_path.glob(f"*{ext}"))
    
    if not files:
        print(f"❌ MusicXMLファイルが見つかりません: {input_dir}")
        return
    
    print(f"📁 見つかったファイル: {len(files)}個\n")
    
    success_count = 0
    total_notes = 0
    total_plucks = 0
    total_frets = 0
    
    for i, file in enumerate(sorted(files), 1):
        print(f"[{i}/{len(files)}] {file.name}...", end=" ")
        
        success, note_count, pluck_count, fret_count = process_single_file(
            str(file), output_dir, expand_repeats=expand_repeats, add_fret=add_fret, fret_pitch_file=fret_pitch_file
        )
        
        if success:
            if add_fret:
                print(f"✅ OK ({note_count}音符, pluck:{pluck_count}, fret:{fret_count})")
            else:
                print(f"✅ OK ({note_count}音符, pluck:{pluck_count})")
            success_count += 1
            total_notes += note_count
            total_plucks += pluck_count
            total_frets += fret_count
        else:
            print(f"❌ ERROR")
    
    print("\n" + "="*60)
    print("処理完了")
    print("="*60)
    print(f"成功: {success_count}/{len(files)} ファイル")
    print(f"合計音符数: {total_notes}")
    print(f"pluck情報: {total_plucks}")
    if add_fret:
        print(f"fret情報: {total_frets}")
    print(f"出力先: {output_dir}")
    print("="*60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        input_path = sys.argv[1]
        output_path = sys.argv[2]
        expand = '--expand' in sys.argv
        no_fret = '--no-fret' in sys.argv
        
        if os.path.isdir(input_path):
            batch_process(input_path, output_path, expand_repeats=expand, add_fret=not no_fret)
        else:
            os.makedirs(output_path, exist_ok=True)
            success, count, pluck, fret = process_single_file(
                input_path, output_path, expand_repeats=expand, add_fret=not no_fret
            )
            if success:
                print(f"✅ 変換完了: {count}音符, pluck:{pluck}, fret:{fret}")
            else:
                print("❌ 変換失敗")
    else:
        print("使用方法:")
        print("  単一ファイル: python musicxml_to_csv_fixed.py input.musicxml output_dir/")
        print("  一括処理:     python musicxml_to_csv_fixed.py input_dir/ output_dir/")
        print("  オプション:   --expand (繰り返し展開), --no-fret (fret情報なし)")
