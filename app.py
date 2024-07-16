import streamlit as st
from pydub import AudioSegment
from pydub.playback import play
from mutagen.id3 import ID3
from mutagen.id3 import ID3, TIT2, TLAN, TPE1, TALB, TDRC, TCON, COMM, TXXX, TCOP, TPUB, TXXX, WOAR, ID3, TIT2, TPE1, TALB, TCON, TYER, COMM, TCOP, TXXX, TPUB, WXXX
from mutagen.wave import WAVE

import os
import uuid
import subprocess
from pathlib import Path
import pympi
import re
import numpy as np
import pandas as pd


def open_directory(path):
    
    if os.path.isdir(path):
        if os.name == 'nt':  # For Windows
            os.startfile(path)
        elif os.name == 'posix':  # For macOS and Linux
            try:
                subprocess.run(['open', path], check=True)  # For macOS
            except FileNotFoundError:
                subprocess.run(['xdg-open', path], check=True)  # For Linux
    else:
        print(f"The path {path} is not a valid directory.")




st.set_page_config(
        page_title="ELK_Talk",
        page_icon="logo.jpg",
        layout="wide",  # "wide" layout adapts to different screen sizes
        initial_sidebar_state="collapsed"
    )


def add_wave_metadata(wav_file, title=None, language=None, artist=None, album=None, year=None, genre=None, subtitle=None, copyright=None, publisher=None, PublisherUrl=None, additional_tags=None):
    audiofile = WAVE(wav_file)
    
    # Add ID3 tags
    audiofile.add_tags()
    id3 = audiofile.tags

    if title:
        id3.add(TIT2(encoding=3, text=title))
    if language:
        id3.add(TLAN(encoding=3, text=u'eng'))
    if artist:
        id3.add(TPE1(encoding=3, text=artist))
    if album:
        id3.add(TALB(encoding=3, text=album))
    if year:
        id3.add(TDRC(encoding=3, text=str(year)))
    if genre:
        id3.add(TCON(encoding=3, text=genre))
    if subtitle:
        id3.add(COMM(encoding=3, lang=u'eng', desc=u'Subtitle', text=subtitle))
    if copyright:
        id3.add(TCOP(encoding=3, text=copyright))
    if publisher:
        id3.add(TPUB(encoding=3, text=publisher))
    if PublisherUrl:
        id3.add(WXXX(url=PublisherUrl))
    if additional_tags:
        for tag in additional_tags:
            id3.add(TXXX(encoding=3, desc=str(tag), text=str(additional_tags[tag])))

    # Save the tags
    audiofile.save()


def add_id3_metadata(mp3_file, title=None, language=None, artist=None, album=None, year=None, genre=None, comment=None, copyright=None, publisher=None, PublisherUrl=None, additional_tags=None):
    try:
        audiofile = ID3(mp3_file)
    except error:
        audiofile = ID3()
    
    if title:
        audiofile["TIT2"] = TIT2(encoding=3, text=title)
    if language:
        audiofile["TLAN"] = TLAN(encoding=3, text=language)
    if artist:
        audiofile["TPE1"] = TPE1(encoding=3, text=artist)
    if album:
        audiofile["TALB"] = TALB(encoding=3, text=album)
    if year:
        audiofile["TDRC"] = TDRC(encoding=3, text=str(year))
    if genre:
        audiofile["TCON"] = TCON(encoding=3, text=genre)
    if comment:
        audiofile["COMM"] = COMM(encoding=3, lang=u'eng', desc=comment, text= u''+comment+'')
    if copyright:
        audiofile["TCOP"] = TCOP(encoding=3, text=copyright)
    if publisher:
        audiofile["TPUB"] = TPUB(encoding=3, text=publisher)
    if PublisherUrl:
        audiofile["WOAR"] = WOAR(url=PublisherUrl)
    if additional_tags:
        for tag in additional_tags:
            audiofile["TXXX:{}".format(tag)] = TXXX(encoding=3, desc=str(tag), text=str(additional_tags[tag]))
    
    audiofile.save(mp3_file)


gray_css = """
        <style>
            .gray-text {
                color: gray;
            }
        </style>
    """

# CSS style for black text
black_css = """
        <style>
            .black-text {
                color: black;
            }
        </style>
    """

def convert_single_mp3_to_wav(input_dir, mp3_filename, output_dir):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Construct full file paths
    mp3_path = os.path.join(input_dir, mp3_filename)
    if not os.path.isfile(mp3_path):
        print(f"The file {mp3_path} does not exist.")
        return

    if not mp3_filename.endswith('.mp3'):
        print(f"The file {mp3_filename} is not an .mp3 file.")
        return
    
    wav_filename = os.path.splitext(mp3_filename)[0] + '.wav'
    wav_path = os.path.join(output_dir, wav_filename)
    
    # Convert mp3 to wav
    audio = AudioSegment.from_mp3(mp3_path)
    audio.export(wav_path, format='wav')

class wav_creation():
    def __init__(self, sample_rate=44100, size = 16):
        self.sample_rate = str(sample_rate)
        self.channels = str(st.session_state.channel)
        self.size = int(size)

    def audio_extraction(self, in_file_name, out_file_name, start, end, vol):

        # cmd = ['ffmpeg', '-i', in_file_name,
        #        '-ac', self.channels,
        #         '-ar', self.sample_rate,
        #         '-sample_fmt', 's{}'.format(self.size),
        #         '-ss', str(start),
        #         '-to', str(end),
        #         '-af', 'volume={}'.format(vol),
        #         out_file_name]
        
        cmd = [
                'ffmpeg',
                '-i', in_file_name,
                '-ac', str(self.channels),
                '-ar', str(self.sample_rate),
                '-ss', str(start),
                '-to', str(end),
                '-af', 'volume={}'.format(vol),
                '-c:a', 'libmp3lame',  # Specify the MP3 codec
                out_file_name
            ]
        exec1 = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, startupinfo = subprocess.STARTUPINFO())
        
        exec1.wait()

    def create_repeat_silence(self, in_file_dir, out_file_dir, start, end, repeats, silence_duration, vol, metadata = {}):

        random_name1 = str(uuid.uuid4())
        silence_file_name = str(random_name1 + ".mp3")
        random_name2 = str(uuid.uuid4())
        main_file_name = str(random_name2 + ".mp3")
        random_name3 = str(uuid.uuid4())
        text_file_name = str(random_name3 + ".txt")
        
        silence_file_dir = os.path.join(os.path.dirname(out_file_dir), silence_file_name)

        
        main_file_dir = os.path.join(os.path.dirname(out_file_dir), main_file_name)


        text_file_dir = os.path.join(os.path.dirname(out_file_dir), text_file_name)


        # silence_file_cmd = ['sox', '-n', '-r', str(self.sample_rate),
        #                     '-c', str(self.channels),
        #                     '-b', str(self.size),
        #                     silence_file_dir,
        #                     'trim', '0.0', str(silence_duration)
        #                     ]

        
        # exec2 = subprocess.Popen(silence_file_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo = subprocess.STARTUPINFO())
        # exec2.wait()


        silence_start = float(st.session_state.silenceStart)/1000.0
        # print(silence_start)
        silence_end = float(st.session_state.silenceStart)/1000.0 + 0.1
        # print(silence_end)
        self.audio_extraction(in_file_dir, silence_file_dir, silence_start, silence_end, vol)
    
        self.audio_extraction(in_file_dir, main_file_dir, start, end, vol)

        text = ""
        silence_repeats = int(float(st.session_state.silence_duration)/0.1)
        for repeat in range(repeats):
            for _ in range(silence_repeats):
                text += "file '{}'\n".format(silence_file_name)
            text += "file '{}'\n".format(main_file_name)
        
        for _ in range(silence_repeats):
                text += "file '{}'\n".format(silence_file_name)
        with open(text_file_dir, "w", encoding="utf-8") as f:
            f.write(text)

        silence_repeat_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', text_file_dir,
            '-c', 'copy',  # Copy the streams directly without re-encoding
            out_file_dir
        ]
        
        # for key in metadata:
        #     new_meta = metadata[key]
        #     silence_repeat_cmd += ['-metadata', "{}={}".format(key, new_meta)]
        # silence_repeat_cmd += [out_file_dir]
        #print(silence_repeat_cmd)
        silence_repeat = subprocess.Popen(silence_repeat_cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, startupinfo = subprocess.STARTUPINFO())
        silence_repeat.wait()
        


        os.remove(silence_file_dir)
        os.remove(text_file_dir)
        os.remove(main_file_dir)

def find_date_components(text):
    pattern = r"(\d{4})(\d{2})(\d{2})"
    match = re.search(pattern, text)
    if match:
        year = match.group(1)
        month = match.group(2)
        day = match.group(3)
        return year, month, day
    else:
        return None

def find_silence(data):
    for entry in data:
        if entry[2] == 'SILENCE':
            return entry[0], entry[1]
    return None

def eaf_process(eaf_dir, parent_names = ['Phrase'], item_number_tier = 'ALI item number'):
    #importing .eaf file
    eaf = pympi.Elan.Eaf(eaf_dir)
    error_box = {}
    # Find total dialects in eaf file
    dialects = [eaf.get_tier_ids_for_linguistic_type(di)[0] for di in parent_names]
    
    
    total_data = []
    for dialect in dialects:
      
        # getting tier ids
        translation_tier_id = "Gloss"
        #item_number_tier = eaf.get_tier_ids_for_linguistic_type(item_number_tier, parent_names[0])
        try:
            translation_tier_id = translation_tier_id
        except:
            error_box[dialect] = "Clip tier id is not defined for {}".format(dialect)
            continue
        # getting translations
        #translation_tier_id = eaf.get_tier_ids_for_linguistic_type(translation_name, dialect)
        # try:
        #     translation_tier_id = translation_tier_id[0]
        # except:
        #     error_box[dialect] = "Translation tier id is not defined for {}".format(dialect)
        # here we continue to process if translation does not exist
        translations = eaf.get_annotation_data_for_tier(dialect)
        st.session_state.silenceStart, _ = find_silence(translations)
        annotations_data = eaf.get_annotation_data_for_tier(translation_tier_id)
        item_numbers = eaf.get_annotation_data_for_tier(item_number_tier)
        url = eaf.get_linked_files()[0]['RELATIVE_MEDIA_URL']
        # year, month, day = find_date_components(url)
        for i in range(len(annotations_data)-1):
            s, e, n, _ = annotations_data[i+1] # here we get the starting point (s), ending point (e), number of clip (n), translation (t)
            _, _, t = translations[i+1]
            data = {}
            data['start'] = s
            data['end'] = e
            data['eng_translation'] = n
            data['ir_translation'] = t
            data['order'] = i
            data['url'] = url
            data['language'] = dialect
            data['year'] = st.session_state.QuestionnaireDate
            # st.session_state.Year = year
            _, _, data['item_number'], _ = item_numbers[i+1]
            
            total_data.append(data)
            
    return total_data

def print_id3_metadata(mp3_file):
    audiofile = ID3(mp3_file)
    
    for key in audiofile.keys():
        print(key, ":", audiofile[key])

# Usage example
#mp3_file_path = mp3_file_path

#print_id3_metadata(mp3_file_path)
def format_date(date_str):
    # Ensure the input is a string
    date_str = str(date_str)
    
    # Extract year, month, and day from the input
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:8]
    
    # Format the date as YYYY/MM/DD
    formatted_date = f"{year}/{month}/{day}"
    
    return formatted_date


def process_main(eaf_dir, saving_dir, sound_dir, vol=0.5, n_repeats = 1, silence_duration = 2, title = "translation"):

    res = eaf_process(eaf_dir)
    ex = wav_creation()
    progress_bar = st.progress(0)
    total_iterations = len(res)
    for i, ann in enumerate(res):
        ann_url = ann['url']
        sound_name = os.path.basename(ann_url)
        start = ann['start']
        start = float(start)/1000.0
        end = ann['end']
        end = float(end)/1000.0
        eng_trans = ann['eng_translation']
        ir_trans = ann['ir_translation']
        order = ann['order']

        language = ann['language']
        year = ann['year']
        ID = ann['item_number']
        sound_path = os.path.join(sound_dir, sound_name)
        if n_repeats == 1:
            out_name = str(st.session_state.UniquePlaceID + "-" + st.session_state.PlaceName + "_" + st.session_state.LanguageName +  "-" + st.session_state.ALILanguageCode + "_" + st.session_state.QuestionnaireDate + "-" + st.session_state.QuestionnaireInstance  ) + "-" +  str(ID) + "-" + str(eng_trans) + "-" + str(ir_trans) +".mp3"
            # print(out_name)
        else:
            out_name = str(st.session_state.UniquePlaceID + "-" + st.session_state.PlaceName + "_" + st.session_state.LanguageName +  "-" + st.session_state.ALILanguageCode + "_" + st.session_state.QuestionnaireDate + "-" + st.session_state.QuestionnaireInstance  )  + "-" +  str(ID) + "-" + str(eng_trans) + "-" + str(ir_trans) + '_' + str(n_repeats) + "rep" +".mp3"
        
        title_created = str(st.session_state.UniquePlaceID + "-" + st.session_state.PlaceName + "_" + st.session_state.LanguageName + "-" + st.session_state.ALILanguageCode ) + "_" + str(eng_trans) + "-" + str(ir_trans) + "-" +  str(ID)
        year_detected = st.session_state.CopyrightYear

        st.session_state.PublisherUrl = "http://iranatlas.net"
        st.session_state.ID = str(ID)
        if 'Title' not in st.session_state:
            st.session_state.Title = title_created
        if 'Language' not in st.session_state:
            st.session_state.Language = str(language)
        if 'Artist' not in st.session_state:
            st.session_state.Artist = "None"
        
        if 'Year' not in st.session_state:
            st.session_state.Year = int(year_detected)

        # st.session_state.Publisher = "Geomatics and Cartographic Research Centre (GCRC), Carleton University"
        # st.session_state.ProjectTitle = "Atlas of the Languages of Iran (ALI)"
        # st.session_state.PublisherPlace = "Ottawa"
        # st.session_state.AuthorURL = "http://iranatlas.net"
        # st.session_state.CopyrightType = "CC BY 4.0"
        # st.session_state.CopyrightHolder = "Consultant(s), Atlas of the Languages of Iran (ALI)"
        st.session_state.ALIReference = st.session_state.Researchers +  " " + st.session_state.ProjectTitle + ". " + st.session_state.PublisherPlace + " : " +  st.session_state.Publisher + "."
        
        formatted_date = format_date(st.session_state.QuestionnaireDate)
        Comments = "ALI lexical item " + str(ID[2:5]) + " /{}/ ".format(str(ir_trans)) + "'{}'".format(str(eng_trans)) + " in " + st.session_state.LanguageName + " ({})".format(st.session_state.ALILanguageCode)  + ". Source: " + str(st.session_state.Researchers) + ". " + str(st.session_state.Year) +". Linguistic data for " + st.session_state.LanguageName + " ({})".format(st.session_state.ALILanguageCode) + " in " + st.session_state.PlaceName + " " + "({})".format(st.session_state.UniquePlaceID) + ", {}".format(st.session_state.Province) + " Province, " + st.session_state.Country + ", " + formatted_date + ". " + "Consultant: " + st.session_state.ConsultantName + ". " + "In Erik Anonby, Mortaza Taheri-Ardali, et al., 2015-present" + ", " + st.session_state.ProjectTitle + ". " + st.session_state.PublisherPlace + ": {}".format(st.session_state.Publisher) + ". Available at: " + st.session_state.AuthorURL
        # if 'Comment' not in st.session_state:
        st.session_state.Comment = u"" + Comments + ""

        # st.session_state.Copyright =  "© 2021 (CC BY 4.0) Consultant(s), Atlas of the Languages of Iran (ALI)"
        st.session_state.Copyright = "© " + st.session_state.CopyrightYear + " " + st.session_state.CopyrightType + " " + "Consultant(s), Atlas of the Languages of Iran (ALI)"
        st.session_state.Album = st.session_state.ProjectTitle + ": {} Province".format(st.session_state.Province)
        #main
        
        st.session_state.Title = out_name[:-4]
        
        st.session_state.Artist = "Consultant: {}. Researchers: {}".format(st.session_state.ConsultantName, st.session_state.Researchers)
        # print(st.session_state.Researchers)
        
        # print(out_name)
        out_path = os.path.join(saving_dir, out_name)
        ex.create_repeat_silence(sound_path, out_path, float(start), float(end), n_repeats, silence_duration, vol)
        wave_dir = os.path.dirname(st.session_state.file_path)
        wave_dir = os.path.join(wave_dir, "wave_results")
        convert_single_mp3_to_wav(saving_dir, out_name, wave_dir)
        wave_name = os.path.splitext(out_name)[0] + '.wav'
        # print(wave_name)
        wave_out_path = os.path.join(wave_dir, wave_name)
        # print(wave_out_path)
        add_wave_metadata(wave_out_path, title=st.session_state.Title, language = st.session_state.Language,  artist=st.session_state.Artist, album = st.session_state.Album, year=st.session_state.CopyrightYear, genre = st.session_state.Genre,
                         subtitle = st.session_state.Comment, copyright = st.session_state.Copyright, publisher = st.session_state.Publisher, PublisherUrl = st.session_state.PublisherUrl)
        # type_audio_changer(out_path)
        # print(out_path)
        add_id3_metadata(out_path, title=st.session_state.Title, language = st.session_state.Language,  artist=st.session_state.Artist, album = st.session_state.Album, year=st.session_state.CopyrightYear, genre = st.session_state.Genre,
                         comment = st.session_state.Comment, copyright = st.session_state.Copyright, publisher = st.session_state.Publisher, PublisherUrl = st.session_state.PublisherUrl)
        progress_bar.progress((i + 1) / total_iterations)

import shutil


# def browse_file():
#     # root = tk.Tk()
#     # root.withdraw()
#     # file_path = filedialog.askopenfilename()
#     # root.destroy()  # Close the Tkinter window explicitly
#     return file_path

def play_audio(audio_path):
    sound = AudioSegment.from_file(audio_path)
    play(sound)


import streamlit as st


from PIL import Image
import time

# List of image paths or URLs in the desired order
image_paths = ['ELK-Talk-logos.jpeg', 'bd59e8a1-63fd-4a26-9abd-01719b8cac50.jpg']

# Placeholder for displaying images dynamically
image_placeholder = st.empty()

# Loop through the images and update the displayed image
counter = 0
# while(1):
#     image = Image.open(image_paths[counter%2])
#     counter += 1
#     image_placeholder.image(image, caption='Your Image Caption Here', use_column_width=True)
#     time.sleep(2)  # Add a delay to control the speed of image replacement

# Optionally, you can add captions and other customization as needed
page_bg_img = '''
<style>
body {
background-image: url('Elk-talk-logos.jpeg');
background-size: cover;
}
</style>
'''

st.markdown(page_bg_img, unsafe_allow_html=True)

def set_custom_styles():
    # External CSS link for Bootstrap
    bootstrap_css_link = """
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
    """
    
    # Custom styles
    custom_styles = """
        <style>
            body {
                font-family: 'Naum-Gothic', sans-serif;
                background-color: #f6f7ee;
                color: #333;
            }

            h1 {
                color: #73b2c9;
            }

            .sidebar .sidebar-content {
                background-color: #your-sidebar-color; /* Replace with your desired color */
                color: #your-text-color; /* Replace with your desired text color */
            }
        </style>
    """
    
    # Apply external CSS (Bootstrap) and custom styles
    st.markdown(bootstrap_css_link, unsafe_allow_html=True)
    st.markdown(custom_styles, unsafe_allow_html=True)

# Call the function to apply custom styles

# set_custom_styles()
if __name__ == '__main__':
    # Set page configuration for responsiveness
    # st.set_page_config(
    # page_title="ELK Talk", page_icon="Elk-talk-logos.jpeg", layout= "wide", initial_sidebar_state="expanded")  # Provide the path to your favicon image file

    # Title
    st.title("Welcome to ELK-Talk!")
    st.write("An open-source app for curating language documentation media files")

    # Sidebar and main content layout
    with st.container():
        # Sidebar
        st.sidebar.header('Audio output specifications')
        st.sidebar.markdown("&nbsp;")

        if 'file_path' not in st.session_state:
            st.session_state.file_path = "abc"

        # Help message for number of repeats
        st.sidebar.markdown("**Number of repeats:** Specify how many times the audio should be repeated.")
        n_repeats = int(st.sidebar.text_input(' ', value="1"))
        st.session_state.n_repeats = n_repeats
        st.sidebar.markdown("&nbsp;")

        # Help message for silence duration
        st.sidebar.markdown("**Silence duration:** Specify the duration of silence between repeated audio.")
        silence_duration = float(st.sidebar.slider('   ', 0.1, 3.0, 0.5, 0.1))
        st.session_state.silence_duration = silence_duration
        st.sidebar.markdown("&nbsp;")

        # Help message for volume adjustment
        st.sidebar.markdown("**Adjust volume:** Use the slider to adjust the volume of the audio.")
        vol = float(st.sidebar.slider('   ', 0.0, 1.0, 0.5, 0.01))
        st.session_state.vol = vol
        st.sidebar.markdown("&nbsp;")

        # Browse .eaf file

        def remove_file(file_path):
            # Check if the file exists
            if os.path.exists(file_path):
                # Remove the file
                shutil.rmtree(file_path)

        uploaded_file = st.file_uploader("Upload .eaf file", type=(".eaf"))
        # st.write(f"Directory of the selected file: {os.getcwd}")
        

        if uploaded_file:
                
                main_dir = os.getcwd()
                main_dir = os.path.join(main_dir, "results")
                # remove_file(main_dir)
                # os.mkdir(main_dir)

                #temp_dir = tempfile.mkdtemp()
                path = os.path.join(main_dir, uploaded_file.name)
                with open(path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                st.session_state.file_path = path
        uploaded_file_sound = st.file_uploader("Upload sound file", type=(".wav", ".mp3"))
        if uploaded_file_sound:
                
                main_dir = os.getcwd()
                main_dir = os.path.join(main_dir, "results")

                #temp_dir = tempfile.mkdtemp()
                path = os.path.join(main_dir, uploaded_file_sound.name)
                with open(path, "wb") as f:
                        f.write(uploaded_file_sound.getvalue())
                # st.session_state.file_path = path
        # uploaded_file_excel = st.file_uploader("Upload .csv file", type=("csv"))
        # if uploaded_file_excel:

        #     main_dir = os.getcwd()
        #     main_dir = os.path.join(main_dir, "results")

        #     path = os.path.join(main_dir, uploaded_file_excel.name)
        #     df = pd.read_csv(path)
        #     df
            # with open(path, "wb") as f:

        # if st.sidebar.button("Browse files"):
        #     with st.spinner("Loading file..."):
        #         file_path = browse_file()
        #         st.session_state.file_path = file_path
        #         st.success("File successfully loaded!")

    # Create files button and result display
    col1, col2 = st.columns([2, 1])  # Use columns for a responsive layout
    if st.button("Remove results"):
            main_dir = os.getcwd()
            main_dir = os.path.join(main_dir, "results")
            remove_file(main_dir)
            os.mkdir(main_dir)
    if st.button("Move to main results folder"):
            main_dir = os.getcwd()
            main_dir = os.path.join(main_dir, "results")
            main_folder_path = os.path.join(main_dir, "mp3_results")
            main_folder_path_wave = os.path.join(main_dir, "wave_results")
            dest_folder = os.path.join(os.getcwd(), 'main_results_mp3')
            dest_folder_wave = os.path.join(os.getcwd(), 'main_results_wave')
            if not os.path.exists(dest_folder):
                os.mkdir(dest_folder)
            if not os.path.exists(dest_folder_wave):
                os.mkdir(dest_folder_wave)
            files = os.listdir(main_folder_path)
            files_wave = os.listdir(main_folder_path_wave)
            if os.path.exists(main_folder_path):
                for file in files:
                    src_path = os.path.join(main_folder_path, file)
                    dest_path = os.path.join(dest_folder, file)
                    shutil.copy(src_path, dest_path)
                # remove_file(main_dir)
                # os.mkdir(main_dir)
            
            if os.path.exists(main_folder_path_wave):
                for file in files_wave:
                    src_path = os.path.join(main_folder_path_wave, file)
                    dest_path = os.path.join(dest_folder_wave, file)
                    shutil.copy(src_path, dest_path)
                remove_file(main_dir)
                os.mkdir(main_dir)
            current_path = os.getcwd()
            copy_path = os.path.join(current_path, "main_results_mp3")
            
            st.success("Files successfully moved to: {}".format(copy_path))
    

    with col1:
        with st.container():
            

            initial_UniquePlaceID = "e.g., 1130662"
            initial_PlaceName = "no special characters, e.g., Hamadan"
            initial_Province = "e.g., Hamadan"
            initial_Country = "Iran"
            initial_LanguageName = "no special characters, e.g., Hemedani"
            initial_ALILanguageCode = "e.g., PHem"
            initial_QuestionnaireDate = "e.g., 20210530"
            initial_QuestionnaireInstance = "for identical place, date, and language, e.g., 1"
            initial_ConsultantName ="no special characters, e.g., Firstname Lastname(, Firstname Lastname, etc.)"
            initial_Researchers = "includes field researcher, checkers, and editors, e.g., Firstname Lastname, Firstname Lastname, etc."
            initial_CopyrightYear = "based on date of data collection, e.g., 2021"
            initial_Genre = "e.g., Questionnaire / Oral text / Place name / etc."
            
            initial_ProjectTitle = "Atlas of the Languages of Iran (ALI)"
            initial_Publisher = "Geomatics and Cartographic Research Centre (GCRC), Carleton University"
            initial_PublisherPlace = "Ottawa"
            initial_AuthorURL = "http://iranatlas.net, https://github.com/atlas-of-the-languages-of-iran"
            initial_CopyrightType = "(CC BY 4.0)"
            initial_CopyrightHolder = "Consultant(s), Atlas of the Languages of Iran (ALI)"




            st.session_state.UniquePlaceID = st.text_input("Unique place ID", value=initial_UniquePlaceID, help="Unique place ID")
            st.session_state.PlaceName = st.text_input("Place name", value=initial_PlaceName, help="Place name")
            st.session_state.Province = st.text_input("Province or state", value=initial_Province, help="Province")
            st.session_state.Country = st.text_input("Country", value=initial_Country, help="Country")
            st.session_state.LanguageName = st.text_input("Language name", value=initial_LanguageName, help="Language name")
            st.session_state.ALILanguageCode = st.text_input("ALI language code", value=initial_ALILanguageCode, help="ALI language code")
            st.session_state.QuestionnaireDate = st.text_input("Questionnaire date", value=initial_QuestionnaireDate, help="Questionnaire date")
            st.session_state.QuestionnaireInstance = st.text_input("Questionnaire instance", value=initial_QuestionnaireInstance, help = "Questionnaire instance")
            st.session_state.ConsultantName = st.text_input("Consultant name", value=initial_ConsultantName, help="Consultant name")
            st.session_state.Researchers = st.text_input("Researchers", value=initial_Researchers, help="Researchers")
            st.session_state.CopyrightYear  = st.text_input("Copyright year ", value=initial_CopyrightYear , help="Copyright year ")
            st.session_state.Genre = st.text_input("Genre", value=initial_Genre, help="Genre")


            st.session_state.ProjectTitle = "Atlas of the Languages of Iran (ALI)"
            st.session_state.Publisher = "Geomatics and Cartographic Research Centre (GCRC), Carleton University"
            st.session_state.PublisherPlace = "Ottawa"
            st.session_state.AuthorURL = "http://iranatlas.net, and https://github.com/atlas-of-the-languages-of-iran"
            st.session_state.CopyrightType = "CC BY 4.0"
            st.session_state.CopyrightHolder = "Consultant(s), Atlas of the Languages of Iran (ALI)"

            st.session_state.ProjectTitle = st.text_input("Project title", value=initial_ProjectTitle, help="Project title")
            st.session_state.Publisher = st.text_input("Publisher", value=initial_Publisher, help="Publisher")
            st.session_state.PublisherPlace = st.text_input("Publisher place", value=initial_PublisherPlace, help="Publisher place")
            st.session_state.AuthorURL = st.text_input("Author URL", value=initial_AuthorURL, help="Author URL")
            st.session_state.CopyrightType = st.text_input("Copyright type", value=initial_CopyrightType, help="Copyright type")
            st.session_state.CopyrightHolder = st.text_input("Copyright holder", value=initial_CopyrightHolder, help="Copyright holder")
            

            st.markdown("""
                <style>
                    /* Style for the gray input */
                    div[data-baseweb="input"] input[value="e.g., 1130662"] {
                        color: gray !important;
                    }
                    
                    div[data-baseweb="input"] input[value="no special characters, e.g., Hamadan"] {
                        color: gray !important;
                    }
                        
                    div[data-baseweb="input"] input[value="e.g., Hamadan"] {
                        color: gray !important;
                    }
                    
                    div[data-baseweb="input"] input[value="Iran"] {
                        color: black !important;
                    }
                        
                    div[data-baseweb="input"] input[value="no special characters, e.g., Hemedani"] {
                        color: gray !important;
                    }
                    
                    div[data-baseweb="input"] input[value="e.g., PHem"] {
                        color: gray !important;
                    }
                        
                    div[data-baseweb="input"] input[value="e.g., 20210530"] {
                        color: gray !important;
                    }
                    
                    div[data-baseweb="input"] input[value="for identical place, date, and language, e.g., 1"] {
                        color: gray !important;
                    }
                    
                    div[data-baseweb="input"] input[value="no special characters, e.g., Firstname Lastname(, Firstname Lastname, etc.)"] {
                        color: gray !important;
                    }
                        
                    div[data-baseweb="input"] input[value="includes field researcher, checkers, and editors, e.g., Firstname Lastname, Firstname Lastname, etc."] {
                        color: gray !important;
                    }
                        
                    div[data-baseweb="input"] input[value="based on date of data collection, e.g., 2021"] {
                        color: gray !important;
                    }
                        
                    div[data-baseweb="input"] input[value="e.g., Questionnaire / Oral text / Place name / etc."] {
                        color: gray !important;
                    }
                        


                        
                    div[data-baseweb="input"] input[value="Atlas of the Languages of Iran (ALI)"] {
                        color: black !important;
                    }
                        
                    div[data-baseweb="input"] input[value="Geomatics and Cartographic Research Centre (GCRC), Carleton University"] {
                        color: black !important;
                    }
                        
                    div[data-baseweb="input"] input[value="Ottawa"] {
                        color: black !important;
                    }
                        
                    div[data-baseweb="input"] input[value="http://iranatlas.net, https://github.com/atlas-of-the-languages-of-iran"] {
                        color: black !important;
                    }
                        
                    div[data-baseweb="input"] input[value="(CC BY 4.0)"] {
                        color: black !important;
                    }
                        
                    div[data-baseweb="input"] input[value="Consultant(s), Atlas of the Languages of Iran (ALI)"] {
                        color: black !important;
                    }

                </style>
            """, unsafe_allow_html=True)
           

            # if not df:
            # UniquePlaceID = st.text_input("Unique place ID:", "1130662", key="gray_input")
            # PlaceName  = st.text_input("Place name:")
            # Province  = st.text_input("Province:")
            # Country = st.text_input("Country:")
            # LanguageName = st.text_input("Language name:")
            # ALILanguageCode = st.text_input("ALI language code:")
            # QuestionnaireDate = st.text_input("Questionnaire date:")
            # QuestionnaireInstance = st.text_input("Questionnaire instance:")
            # ConsultantName = st.text_input("Consultant name")
            # Researchers = st.text_input("Researchers")
            # CopyrightYear = st.text_input("Copyright year:")
            # Genre = st.text_input("Genre:") 
            
            # else:
            #     filed_names = df["Fieldname"]
            #     UniquePlaceIDIdx = np.where(filed_names == "unique_place_ID")
            #     UniquePlaceID = df["Data entry fields"][UniquePlaceIDIdx[0]]
            #     UniquePlaceID = UniquePlaceID[0]

            #     PlaceNameIdx = np.where(filed_names == "place_name_roman_simplified")
            #     PlaceName = df["Data entry fields"][PlaceNameIdx[0]]
            #     PlaceName = PlaceName[0]

            #     ProvinceIdx = np.where(filed_names == "province")
            #     Province = df["Data entry fields"][ProvinceIdx[0]]
            #     Province = Province[0]

            #     CountryIdx = np.where(filed_names == "country")
            #     Country = df["Data entry fields"][CountryIdx[0]]
            #     Country = Country[0]

            #     LanguageNameIdx = np.where(filed_names == "language_name_roman_simplified")
            #     LanguageName = df["Data entry fields"][LanguageNameIdx[0]]
            #     LanguageName = LanguageName[0]

            #     ALILanguageCodeIdx = np.where(filed_names == "unique_language_ID")
            #     ALILanguageCode = df["Data entry fields"][ALILanguageCodeIdx[0]]
            #     ALILanguageCode = ALILanguageCode[0]

            #     QuestionnaireDateIdx = np.where(filed_names == "questionnaire_date")
            #     QuestionnaireDate = df["Data entry fields"][QuestionnaireDateIdx[0]]
            #     QuestionnaireDate = QuestionnaireDate[0]

            #     QuestionnaireInstanceIdx = np.where(filed_names == "questionnaire_instance")
            #     QuestionnaireInstance = df["Data entry fields"][QuestionnaireInstanceIdx[0]]
            #     QuestionnaireInstance = QuestionnaireInstance[0]

            #     ConsultantNameIdx = np.where(filed_names == "consultant_name_roman_simplified")
            #     ConsultantName = df["Data entry fields"][ConsultantNameIdx[0]]
            #     ConsultantName = ConsultantName[0]

            #     ResearchersIdx = np.where(filed_names == "researchers")
            #     Researchers = df["Data entry fields"][ResearchersIdx[0]]
            #     Researchers = Researchers[0]

            #     CopyrightYearIdx = np.where(filed_names == "copyright_year")
            #     CopyrightYear = df["Data entry fields"][CopyrightYearIdx[0]]
            #     CopyrightYear = CopyrightYear[0]

            #     GenreIdx = np.where(filed_names == "genre")
            #     Genre = df["Data entry fields"][GenreIdx[0]]
            #     Genre = Genre[0]



            channel_layout = st.radio(
                "Select output:",
                ("Mono", "Stereo"))
            
            if channel_layout == "Mono":
                st.session_state.channel = 1
            else:
                st.session_state.channel = 2
            # st.write("You selected:", channel_layout)

            # Title = st.text_input("Title:")
            # Language = st.text_input("Language:")
            # Artist = st.text_input("*Artist:")
            # # Album = st.text_input("*Album:")
            # Year = st.text_input("Year:")
            # Genre = st.text_input("Genre:")
            # Comment = st.text_input("Comment:")
            # Copyright = st.text_input("Copyright:")
            # Publisher = st.text_input("Publisher:")
            # if st.button("Click to import metadata"):
                
                
                # st.session_state.Language = LanguageName
                
                # st.session_state.Artist = Artist

            st.session_state.Album = st.session_state.ProjectTitle + ", {} ".format(st.session_state.Province)
           
                # st.session_state.Year = st.session_state.CopyrightYear

                # st.session_state.Genre = st.session_state.Genre
                # st.session_state.Comment = u"" + Comment + ""
                # if Copyright:
                #     st.session_state.Copyright = Copyright
                # if Publisher:
                #     st.session_state.Publisher = Publisher
                

        # Create files button
        os.getcwd()
        if st.button("Generate audio files"):
            if not hasattr(st.session_state, 'file_path') or not os.path.exists(st.session_state.file_path):
                st.warning("Please browse and select a valid file before creating files.")
            else:
                with st.spinner("Creating files..."):
                    eaf_location = os.path.dirname(st.session_state.file_path)
                    sound_dir = eaf_location
                    saving_dir = os.path.join(sound_dir, "mp3_results")
                    st.session_state.saving_dir = saving_dir

                    if not os.path.exists(saving_dir):
                        os.mkdir(saving_dir)

                    process_main(st.session_state.file_path, saving_dir, sound_dir, vol=st.session_state.vol,
                                n_repeats=st.session_state.n_repeats, silence_duration=st.session_state.silence_duration,
                                title="translation")
                    file_path = os.getcwd()
                    file_path = os.path.join(file_path, "results", "mp3_results")
                    st.session_state.filePath = file_path
                    st.success("Files successfully created! Files are saved in: {}".format(file_path))
                    
                    # with col2:
                    #     # Display selected file
                    #     try:
                    #         sound_files = [file for file in os.listdir(st.session_state.saving_dir) if file.endswith((".mp3", ".wav"))]
                    #         selected_file = st.selectbox("Select a sound file", sound_files)
                    #         selected_file_path = os.path.join(st.session_state.saving_dir, selected_file)
                    #         st.audio(selected_file_path, format='audio/wav', start_time=0)
                    #     except:
                    #         pass
                    audio_placeholder = st.empty()

        if st.button("Open saving directory"):
            open_directory(st.session_state.filePath)

                    
    audio_placeholder1 = st.empty()
    audio_placeholder2 = st.empty()

    with col2:
        # Display selected file
        try:
            sound_files = [file for file in os.listdir(st.session_state.saving_dir) if file.endswith((".mp3", ".wav"))]
            selected_file = audio_placeholder1.selectbox("Select a sound file", sound_files)
            selected_file_path = os.path.join(st.session_state.saving_dir, selected_file)
            audio_placeholder2.audio(selected_file_path, format='audio/wav', start_time=0)
        except:
            pass



    st.markdown("<h5 style='text-align: center;'>About ELK-Talk</h5>", unsafe_allow_html=True)
    st.markdown("""
<div style='text-align: center;'>
    <p style='font-size: 17px;'>
        ELK-Talk is a production of the <a href='https://elk-tech.org/' target='_blank'>Endangered Language Knowledge and Technology (ELK-Tech)</a> research group at Carleton University, in partnership with the <a href='http://iranatlas.net/index.html' target='_blank'>Atlas of the Languages of Iran (ALI)</a>. Programmer: <a href='https://www.linkedin.com/in/mohsen-mozafari-417369147/' target='_blank'>Mohsen Mozafari</a>. 
    </p>
    <p style='font-size: 17px;'>
        This app is provided under a <a href='https://creativecommons.org/licenses/by/4.0/' target='_blank'>CC BY 4.0 licence</a>. The <a href='https://github.com/atlas-of-the-languages-of-iran' target='_blank'>app code</a> may be freely used as long as the source is specified: 
    </p>
    <p style='font-size: 17px;'>
        Mozafari, Mohsen, Erik Anonby, Tara Azin, Mahnaz Talebi-Dastenaei, Hamideh Poshtvan, et al. 2023-present.<em> ELK-Talk: An open-source app for curating language documentation media files.</em> Ottawa: Endangered Language and Technology (ELK-Tech) research group, Carleton University. Online at: <a href='https://github.com/atlas-of-the-languages-of-iran' target='_blank'>https://github.com/atlas-of-the-languages-of-iran</a>.
    </p>         
    
</div>
""", unsafe_allow_html=True)
