"""
@author rahulpandey

"""

from collections import Counter
import xml.etree.ElementTree as ET

import os
INPUT_PATH = "/Users/rahulpandey/OneDrive - Philips/philips/clinical-trial-disambiguation/data/CDR_Data/CDR.Corpus.v010516/CDR_TrainingSet.BioC.xml"

tree = ET.parse(INPUT_PATH)
root = tree.getroot()
print(root.tag, root.attrib)
result_dict = {}
i = 0
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
            full_text += sep + psg.find("text").text
            sep = " "
            for ann in psg.findall("annotation"):
                # print("\t\ttoken", ann.find("text").text)
                ann_sub_text = ann.find("text").text
                for inf in ann.findall("infon"):
                    if(inf.get("key") == "type"):
                        # print("\t\t\t-> annotation", inf.text)
                        annotation_list.append((ann_sub_text, inf.text))
        # print("*"*50, "end of document", "*"*50)
        result_dict[i] = {"text": full_text, "ground_truth": annotation_list}
        i += 1
        # break

token_ann = []
tree = ET.parse(INPUT_PATH)
root = tree.getroot()
doc_cnt = 0
for child in root:
    if child.tag == "document":
        # for doc in child:
        doc_cnt += 1
        for psg in child.findall("passage"):
            for ann in psg.findall("annotation"):
                text = ann.find("text").text
                label = ""
                for inf in ann.findall("infon"):
                    if(inf.get("key") == "type"):
                        label = inf.text
                token_ann.append((text, label))

print(len(token_ann))
print(len(list(set(token_ann))))

print("Total document", doc_cnt)

uniq_token_ann = list(set(token_ann))

uniq_text = [x[0] for x in uniq_token_ann]
uniq_ann = [x[1] for x in uniq_token_ann]

print("Unique concepts", len(list(set(uniq_text))))
print("Unique annotation", len(list(set(uniq_ann))))
print(uniq_token_ann)
