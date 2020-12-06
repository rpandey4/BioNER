import os
import random
import xml.etree.ElementTree as ET
from nltk.tokenize import sent_tokenize
import sys


def get_cdr_lines(file_path, title_list):
    sentences = []
    sentences_replaced = []
    cur_sent = []
    cur_sent_replaced = []
    cur_token = ""
    title_cnt = 0
    map_token_concepts = {"B-Disease": "disease", "B-Chemical": "chemical", "I-Disease": "disease", "I-Chemical": "chemical"}
    for lines in open(file_path):
        lines = lines.strip()
        if lines == "":
            if (cur_sent[0] == "Comparison"):
                print("".join(cur_sent))
            if "".join(cur_sent) in title_list:
                title_cnt += 1
                print("Found %d title " % (title_cnt))
                sentences.append("")
                sentences_replaced.append("")
                title_list.remove("".join(cur_sent))
            # print("Original:\t%s \t|\t Replaced:\t %s" % (" ".join(cur_sent), " ".join(cur_sent_replaced)))
            sentences.append(" ".join(cur_sent))
            sentences_replaced.append(" ".join(cur_sent_replaced))
            cur_sent = []
            cur_sent_replaced = []
            # if random.randint(0, 5) == 4:
            #     break
            continue
        lines = lines.split("\t")
        cur_sent.append(lines[0])
        if lines[1] == "O":
            if cur_token:
                cur_sent_replaced.append(cur_token)
                cur_token = ""
            cur_sent_replaced.append(lines[0])
        else:
            if lines[1].startswith("B-") and cur_token:
                cur_sent_replaced.append(cur_token)
            cur_token = map_token_concepts[lines[1]]
    # for i in range(len(sentences)):
    print(title_list)
    return


def get_cdr_masked_lm(file_path, output_folder, title_list, data_type, replace_type="all"):
    sentences = []
    sentences_replaced = []
    cur_sent = []
    cur_sent_replaced = []
    cur_token = ""
    title_cnt = 0
    map_token_concepts = {"B-Disease": "disease", "B-Chemical": "chemical", "I-Disease": "disease", "I-Chemical": "chemical"}
    for lines in open(file_path):
        lines = lines.strip()
        if lines == "":
            if "".join(cur_sent) in title_list:
                title_cnt += 1
                print("Found %d title " % (title_cnt))
                sentences.append("")
                sentences_replaced.append("")
            sentences.append(" ".join(cur_sent))
            sentences_replaced.append(" ".join(cur_sent_replaced))
            cur_sent = []
            cur_sent_replaced = []
            continue
        lines = lines.split("\t")
        cur_sent.append(lines[0])
        if lines[1] == "O":
            if cur_token:
                cur_sent_replaced.append(cur_token)
                cur_token = ""
            cur_sent_replaced.append(lines[0])
        else:
            if lines[1].startswith("B-") and cur_token:
                cur_sent_replaced.append(cur_token)
            cur_token = map_token_concepts[lines[1]]
    # for i in range(len(sentences)):
    out_file = os.path.join(output_folder, "cdr_data_%s_%s_replaced.csv" % (data_type, replace_type))
    print("Now writing for %s type %s replace type %s" % (os.path.basename(file_path), data_type, replace_type))
    with open(out_file, "w") as f:
        for sent in sentences_replaced:
            f.write("%s\n" % sent)
    return


def get_title_keys(INPUT_PATH_PARA):
    tree = ET.parse(INPUT_PATH_PARA)
    root = tree.getroot()
    print(root.tag, root.attrib)
    result_dict = {}
    i = 0
    title_list = []
    for child in root:
        if child.tag == "document":
            # print("*"*50, "start of document", "*"*50)
            # for doc in child:
            #     print(doc.tag, doc.attrib)
            full_text = ""
            sep = ""
            annotation_list = []
            for psg in child.findall("passage"):
                # for txt in psg.findall("text"):
                # print("Text", psg.find("text").text)
                text = psg.find("text").text
                for inf in psg.findall("infon"):
                    if(inf.get("key") == "type"):
                        if inf.text == "title":
                            # if text.startswith("Comparison of the"):
                            #     print(text, sent_tokenize(text))
                            # text = sent_tokenize(text)[0]
                            title_list.append(text.replace(" ", ""))
                            i += 1

            # break
    return title_list


if __name__ == "__main__":
    # INP_PATH = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/MTL-Bioinformatics-2016/data/"
    INP_PATH = sys.argv[1]
    # OUT_PATH = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/data/bert-ready/MTL-Bioinformatics/Para/BC5CDR"
    OUT_PATH = sys.argv[2]
    if not os.path.isdir(OUT_PATH):
        os.makedirs(OUT_PATH)
    # INPUT_PATH_PARA = "/Users/rahulpandey/OneDrive - Philips/philips/rahul-ai-work/clinical_trial_disambiguation/data/CDR_Data/CDR.Corpus.v010516/"
    INPUT_PATH_PARA = sys.argv[3]
    title_list = []
    title_list.extend(get_title_keys(os.path.join(INPUT_PATH_PARA, "CDR_DevelopmentSet.BioC.xml")))
    title_list.extend(get_title_keys(os.path.join(INPUT_PATH_PARA, "CDR_TrainingSet.BioC.xml")))
    title_list_new = []
    for tit in title_list:
        if "." in tit[:-2] and ".," not in tit[:-2]:
            # tit = ".".join(tit.split(".")[:-2])+"."
            tit = tit.split(".")[0]+"."
        if tit.startswith("Comparisonofthesubjectiveeffectsandplasmaconcentrationsfollowingoralandi"):
            tit = "Comparisonofthesubjectiveeffectsandplasmaconcentrationsfollowingoralandi.m.administrationofflunitrazepaminvolunteers."
        if tit == 'Comparisonofi.':
            tit = "Comparisonofi.v.glycopyrrolateandatropineinthepreventionofbradycardiaandarrhythmiasfollowingrepeateddosesofsuxamethoniuminchildren."
        if tit == 'Comparisonoftherespiratoryeffectsofi.':
            tit = "Comparisonoftherespiratoryeffectsofi.v.infusionsofmorphineandregionalanalgesiabyextraduralblock."
        if "?" in tit[:-2]:
            tit = tit.split("?")[0]+"?"
        title_list_new.append(tit)
    # print([x for x in title_list if "." in x[:-2]])
    title_list = [x for x in title_list_new]
    # print(title_list)
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-IOB", "train.tsv"), OUT_PATH, title_list, "train", "all")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-disease-IOB", "train.tsv"), OUT_PATH, title_list, "train", "disease")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-chem-IOB", "train.tsv"), OUT_PATH, title_list, "train", "chem")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-IOB", "devel.tsv"), OUT_PATH, title_list, "dev", "all")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-disease-IOB", "devel.tsv"), OUT_PATH, title_list, "dev", "disease")
    get_cdr_masked_lm(os.path.join(INP_PATH, "BC5CDR-chem-IOB", "devel.tsv"), OUT_PATH, title_list, "dev", "chem")
    # get_cdr_lines(os.path.join(INP_PATH, "BC5CDR-IOB", "train.tsv"), title_list_new)
