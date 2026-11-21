#!/usr/bin/python3
''' Dictbase for google
'''
import json
import os
import zipfile
from typing import Any, cast, override

from src.components.classbases.dictbase import DictBase
from src.components.classbases.ziparchive import ZipArchive


class GDictBase(DictBase):
    # TODO: autodetect zip format
    def __init__(self):
        super().__init__()
        self._dictzip: ZipArchive = ZipArchive()

    def _extract_all_zip(self, zip_path: str, target_dir: str) -> None:
        """
        Extract all files from a ZIP archive to a target directory.
        
        Args:
            zip_path: Path to the ZIP file (e.g., "data.zip")
            target_dir: Directory to extract files to (created if it doesn't exist)
        
        Raises:
            FileNotFoundError: If the ZIP file doesn't exist
            zipfile.BadZipFile: If the file is not a valid ZIP archive
            PermissionError: If access to the directory/file is denied
        """
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)

        # Open the ZIP file and extract all contents (use 'with' for safe file handling)
        try:
            with zipfile.ZipFile(zip_path, mode="r") as zip_ref:
                # Extract all files/folders to the target directory
                zip_ref.extractall(path=target_dir)
                print(f"Successfully extracted all files to: {os.path.abspath(target_dir)}")

                # Optional: List all extracted files for verification
                # print("\nExtracted files:")
                # for file in zip_ref.namelist():
                #     print(f"- {file}")
        except FileNotFoundError:
            print(f"Error: ZIP file '{zip_path}' not found.")
        except zipfile.BadZipFile:
            print(f"Error: '{zip_path}' is not a valid ZIP file (or it's corrupted).")
        except PermissionError:
            print(f"Error: Permission denied to access '{zip_path}' or '{target_dir}'.")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

    @override
    def open(self, name: str, src: str) -> tuple[int, str]:
        _ = super().open(name, src)
        filepath, filename = os.path.split(self._src)
        name, _ = os.path.splitext(filename)
        stylesrc = os.path.join(filepath, name + "-style.zip")

        self._extract_all_zip(stylesrc, self._tempdir)

        if self._download is not None:
            self._download["SavePath"] = os.path.join(self._tempdir, "{}.json")

        return self._dictzip.open(self._src)

    @override
    def close(self) -> bool:
        _ = self._dictzip.close()
        return super().close()

    @override
    def query_word(self, word: str) -> tuple[int, str]:
        htmlfile = os.path.join(self._tempdir, word + ".html")
        if os.path.isfile(htmlfile):
            return 1, htmlfile

        dictjson = ""
        msg = ""
        # filename = os.path.join(word[0], word + ".json")
        filename = word[0].lower() + "/" + word + ".json"
        if self._dictzip.has_file(filename):
            dictjson = str(self._dictzip.read_file(filename),'utf-8')
        elif self._download is not None:
            json_url = (self._download["URL"]).format(word)
            json_url = json_url.replace(" ", "%20")
            return 0, str(json_url)
        else:
            msg = f"no word '{word}' in '{self._name}'"
            return -1, msg

        if dictjson:
            inword = self._get_inword(dictjson)

            if inword:
                if inword != word:
                    msg = f"word '{word}', wrong word '{inword}' in '{self._name}'"
                    return -1, msg
            else:
                msg = f"no word '{word}' in '{self._name}'"
                return -1, msg

        else:
            msg = f"Fail to read json '{word}' in '{self._name}'"
            return -1, msg

        # print("%s = %s" %(word, dict))

        if dictjson:
            dictdata = cast(dict[str, object], json.loads(dictjson, strict=False))
            if dictdata["ok"]:
                info = cast(str,dictdata["info"])
                ret = self._parse_json(info, htmlfile)
                # print("%s = %s" %(word, dict))
                if ret:
                    return 1, htmlfile
                return -1, f"Fail to parse '{word}' in '{self._name}'"
        else:
            msg = f"Fail to read word '{word}' in '{self._name}'"
            return -1, msg

        msg = "Unknown error!"
        return -1, msg

    def _get_inword(self, dictjson: str) -> str:

        data = cast(dict[str, object], json.loads(dictjson, strict=False))

        if data["ok"]:
            info: str = cast(str, data["info"])
            # print(info)
            # GetApp().log("info", info)
            # regex = re.compile(r'\\(?![/u"])')
            # info_fixed = regex.sub(r"\\\\", info)
            # GetApp().log("info", info_fixed)
            # data = json.loads(info_fixed, strict = False)
            # info = info.replace('\\"', '"')
            # info = info.replace('/', '')
            info = info.replace('\\', '\\\\')
            data = json.loads(info, strict=True)
            return data["primaries"][0]["terms"][0]["text"]

        return ""

    def _process_primaries(self, primaries: list[dict[str, Any]] | str, level: int) -> str:
        htmls: str = ""
        html: str = ""
        # is_meaning = False
        # tabalign = "\t" * level
        if isinstance(primaries, list):
            for primary in primaries:
                html = self._process_primary(primary, level)
                # console.log("html1: " + html + "")
                # if html[0] == "<":
                    # htmls += "\n" + tabalign
                    # htmls += "\n"
                htmls += html
        else:
            html = self._process_primaries(json.loads(primaries, strict=False), level + 1)
            # console.log("html3: " + html + "")
            htmls += html
        return htmls

    def _process_primary(self, primary: dict[str, Any], level: int) -> str:
        htmls: str = ""
        # html: str = ""
        # is_meaning = False
        tabalign = "\t" * level
        # let hasChild = false
        # let hastyp = false
        primary_type = ""
        # if "type" in primary:
        #     # hastyp = True
        #     primary_type = cast(str, primary["type"])
        primary_type = cast(str, primary.pop("type", ""))
        if primary_type == "headword":
            htmls = f"{tabalign}<div class='headword'>"
        for item in primary:
            match item:
                case "terms":
                    htmls += self._process_terms(primary["terms"], primary_type, level + 1)
                case "entries":
                    htmls += self._process_entries(primary["entries"], level + 1)
                case _:
                    raise KeyError(f"unkown item: {item} in primary")
        if primary_type == "headword":
            htmls += f"\n{tabalign}</div>"
        return htmls

    def _process_entries(self, entries: list[dict[str, Any]], level: int) -> str:
        htmls: str = ""
        html: str = ""
        # is_meaning = False
        # tabalign = "\t" * level
        for entry in entries:
            html = self._process_entry(entry, level)
            # console.log("html1: " + html + "")
            if html[0] == "<":
                # htmls += "\n" + tabalign
                htmls += "\n"
            htmls += html
        return htmls

    def _process_entry(self, entry: dict[str, Any], level: int):
        htmls: str = ""
        html: str = ""
        is_meaning = False
        tabalign = "\t" * level
        # let hasChild = false
        # let hastyp = false
        if "type" in entry:
            # hastyp = True
            entry_type = cast(str, entry["type"])
            if entry_type == "container":
                # print(primary)
                htmls += f'\n{tabalign}<div class="wordtyp">{entry["labels"][0]["text"]}: </div>'
                htmls += f"\n{tabalign}<div class='container1'>"
            else:
                if "labels" in entry:
                    # if(htmls.substr(-1, 1) == ">"){
                    # htmls += "\n"
                    # }
                    htmls += f"\n{tabalign}<div class='{entry_type}'>"
                    # tabalign += "\t"
                    htmls += f"\n{tabalign}\t<div class='labels'>{entry['labels'][0]['text']}</div>"
                    html = self._process_terms(entry["terms"], entry_type, level + 1)
                    if html[0] == "<":
                        htmls += "\n" + tabalign
                    else:
                        htmls += " "
                    htmls += html
                else:
                    if entry_type == "meaning":
                        is_meaning = True
                    if entry_type == "example" and is_meaning:
                        htmls += "\n"
                        is_meaning = False
                    htmls += f"\n{tabalign}<div class='{entry_type}'>"
                    # tabalign += "\t"
                    html = self._process_terms(entry["terms"], entry_type, level + 1)
                    if html[0] == "<":
                        htmls += "\n" + tabalign
                    # console.log("html4: " + html + "")
                    htmls += html
            if "entries" in entry:
                html = self._process_entries(entry["entries"], level + 1)
                # console.log("html: " + html + "")
                # console.log("htmls: " + htmls + "")
                # console.log("html2: " + html + "")
                if html[0] == "<":
                    htmls += "\n" + tabalign + "Q: "
                htmls += html
            # htmls += tabalign + "</div>\n"
            # tabalign = tabalign[0] ?
            # console.log(htmls.substr(-3, 3))
            if htmls[-3] == ">":
                htmls += tabalign
            if htmls[-1] == ">":
                htmls += "\n" + tabalign
            htmls += "</div>"
            # tabalign = tabalign.slice(0, -2)
        return htmls

    def _process_terms(self, terms: list[dict[str, Any]], primary_type: str, level: int):
        htmls: str = ""
        html: str = ""
        # tabalign = "\t" * level
        html_list: list[str] = []
        for term in terms:
            # data = terms[i]
            # html = self._process_terms(data, typ, level + 1)
            html = self._process_term(term, primary_type, level)
            # if(html.slice(0,1) == "<"){
            # htmls += "\n" + tabalign
            # }
            html_list.append(html)
        htmls += " ".join(html_list)
        return htmls

    def _process_term(self, term: dict[str, Any], primary_type: str, level: int):
        htmls: str = ""
        tabalign = "\t" * level

        # let hastyp = false
        if "type" in term:
            term_type = cast(str, term["type"])
            # if term_type != "text" or primary_type == "related":
            if term_type != "text" or primary_type == "headword":
                if term["type"] == "sound":
                    htmls += self._get_sound(tabalign, term["text"])
                elif term_type == "phonetic":
                    phoetic_type = cast(str, term['labels'][0]['text'])
                    phoetic_class = "US" if phoetic_type == "KK" else "UK"
                    htmls += f"\n{tabalign}<div class='{term_type}'>{phoetic_class}: {term['text']}</div>"
                else:
                    # console.log("P: " + htmls)
                    # if(htmls.substr(-1, 1) == ">"){
                    # htmls += "\n" + tabalign
                    # }
                    htmls += f"\n{tabalign}<div class='{term_type}'>{term['text']}</div>"
            else:
                # print(primary_type)
                # print(terms)
                if "labels" in term:
                    htmls += f"\n{tabalign}<div class='labels'></div>"
                    label_list: list[str] = []
                    for label in term["labels"]:
                        # htmls += f"\n{tabalign}<div class='text'>{{{label['text']}}}</div>"
                        label_list.append(cast(str, label['text']))
                    labels = ", ".join(label_list)
                    htmls += f"\n{tabalign}<div class='text'>&lt;{labels}&gt; {term["text"]}</div>"
                else:
                    htmls += f"\n{tabalign}<div class='text'>{term["text"]}</div>"
        return htmls

    def _get_sound(self, tabalign: str, url: str) -> str:
        sound = \
            '\n' + \
            tabalign + "<div class='sound' id='Player'>\n" + \
            tabalign +'\t' + "<button class='jp-play' id='playpause' title='Play'></button>\n" + \
            tabalign + '\t' + "<audio id='myaudio'>\n" + \
            tabalign + '\t' + '\t' + '<source src=' + url + " typ='audio/mpeg'>\n" + \
            tabalign +  '\t' +  '\t' +  'Your browser does not support the audio tag.\n' + \
            tabalign +  '\t' +  '</audio>\n' + \
            tabalign +  '</div>'
        return sound

    def _parse_json(self, json_str: str, htmlfile: str) -> bool:
        # regex = re.compile(r'\\(?![/u"])')
        # info_fixed = regex.sub(r"\\\\", info)
        # dict = info_fixed
        # info = str(info).replace(/\\x/g, "\\u00")
        jsonstr = json_str.replace("\\x", "\\u00")
        obj = json.loads(jsonstr, strict = True)
        level = 2
        tabalign = '\t' * level

        jsname = "google-toggle.js"
        cssname = "google.css"

        html = "<!DOCTYPE html>\n" + \
            "<html>\n" + \
            "\t<body>\n" + \
            tabalign + '<link rel="stylesheet" href="./player.css">\n' + \
            tabalign + f"<link rel='stylesheet' typ='text/css' href='{cssname}'>\n" + \
            tabalign + '<script src="./player.js"></script>\n' + \
            tabalign + f"<script src='{jsname}'></script>\n" + \
            tabalign + '<div id="toggle_example" align="right">- Hide Examples</div>\n' + \
            self._process_primaries(obj["primaries"], level) + "\n" + \
                .replace("<div class='meaning'>", "<div class='webmeaning'>") + "\n" + \
            "\t</body>\n" + \
            "</html>"

        with open(htmlfile, 'w', encoding="UTF-8") as f:
            _ = f.write(html)
        return True

    @override
    def check_addword(self, localfile: str) -> tuple[int, str]:
        basename = os.path.basename(localfile)
        word, _ = os.path.splitext(basename)
        filename = word[0].lower() + "/" + word + ".json"

        if self._dictzip.has_file(filename):
            return 0, f"The '{basename}' already exists in the '{self._name}.zip'."
        if os.path.isfile(localfile):
            with open(localfile, "r", encoding="utf-8") as f:
                dictjson = f.read()
                inword = self._get_inword(dictjson)

                # os.remove(localfile)

                if inword != "":
                    if inword == word:
                        _ = self._dictzip.add_file(filename, dictjson)
                        return 1, f"OK to add '{basename}' to {self._name}.zip"
                    return 0, f"expected word '{word}', inword '{inword}'"
                return -1, f"No valid data in {localfile}"

        return -1, f"No file {localfile}"

    @override
    def get_wordlist(self, word: str, limit: int = 100):
        word_list: list[str] = []
        # filename = word[0] + "/" + word + ".*\.json"
        pattern = "^" + word + ".*"
        # print("Going to find: " + fileName)
        _ = self._dictzip.search_file(pattern, word_list)

        for i in range(len(word_list)):
            word_list[i] = word_list[i][2: -5]
            if i > limit:
                break

        return word_list

    @override
    def del_word(self, word: str) -> bool:
        filename = word[0] + "/" + word + ".json"
        return self._dictzip.del_file(filename)
