import csv
import json
import re
import os

def katakana_to_hiragana(text):
    # Simple conversion for Katakana to Hiragana
    # Unicode range: Katakana 30A1-30F6, Hiragana 3041-3096
    # Difference is 0x60 (96)
    result = ""
    for char in text:
        code = ord(char)
        if 0x30A1 <= code <= 0x30F6:
            result += chr(code - 0x60)
        else:
            result += char
    return result

def clean_text(text):
    # Remove ～
    text = text.replace('～', '')
    # Remove content inside parentheses （） and ()
    text = re.sub(r'（.*?）', '', text)
    text = re.sub(r'\(.*?\)', '', text)
    # Remove other potential noise symbols if necessary
    return text.strip()

def process_csv():
    input_path = r'c:\Users\kawas\大学用\workspace\プログラミング勉強用\word_basket\word_basket_app\data\voc_list.csv'
    output_path = r'c:\Users\kawas\大学用\workspace\プログラミング勉強用\word_basket\word_basket_app\data\words.json'
    
    words_list = []
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 4:
                    continue
                
                # col:3 (index 2) -> Kanji/Display
                # col:4 (index 3) -> Reading (Kana)
                raw_display = row[2]
                raw_reading = row[3]
                
                # Clean texts
                display_base = clean_text(raw_display)
                reading_base = clean_text(raw_reading)
                
                if not reading_base:
                    continue

                # Handle multiple readings separated by ／ or /
                readings = re.split(r'[／/]', reading_base)
                displays = re.split(r'[／/]', display_base)
                
                # If displays count doesn't match readings, use the full display for all, or try to match?
                # Usually safely, use the base display for all readings if counts don't match
                
                for i, reading in enumerate(readings):
                    reading = reading.strip()
                    if not reading:
                        continue
                        
                    # Convert to Hiragana for consistency
                    reading_hiragana = katakana_to_hiragana(reading)
                    
                    # Determine display text
                    if len(displays) == len(readings):
                        display = displays[i].strip()
                    else:
                        display = display_base
                    
                    if not display:
                        display = reading_hiragana

                    words_list.append({
                        "text": display,
                        "kana": reading_hiragana
                    })
                    
    except UnicodeDecodeError:
        # Fallback to Shift-JIS if UTF-8 fails
        print("UTF-8 failed, trying Shift-JIS...")
        with open(input_path, 'r', encoding='shift_jis') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 4:
                    continue
                
                raw_display = row[2]
                raw_reading = row[3]
                
                display_base = clean_text(raw_display)
                reading_base = clean_text(raw_reading)
                
                if not reading_base:
                    continue

                readings = re.split(r'[／/]', reading_base)
                displays = re.split(r'[／/]', display_base)
                
                for i, reading in enumerate(readings):
                    reading = reading.strip()
                    if not reading:
                        continue
                    
                    reading_hiragana = katakana_to_hiragana(reading)
                    
                    if len(displays) == len(readings):
                        display = displays[i].strip()
                    else:
                        display = display_base
                    
                    if not display:
                        display = reading_hiragana

                    words_list.append({
                        "text": display,
                        "kana": reading_hiragana
                    })

    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(words_list, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully processed {len(words_list)} words.")

if __name__ == "__main__":
    process_csv()
