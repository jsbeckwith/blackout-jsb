import os
import random
from statistics import mean
import string
import uuid
import sys
import itertools
import spacy
import pyocr
import pyocr.builders
from PIL import Image, ImageDraw, ImageFilter

BOUND_PADDING = 50
BOX_PADDING = 7 # 10
WOBBLE_MAX = 2

nlp = spacy.load('en')

def draw_vertical_lines(draw, boxes, doc_bounding_box, line_width):
    line_weight_factor = random.triangular(0.005, 1.2)
    current_x = doc_bounding_box[0] - line_width / 2
    color = get_color()

    while current_x < doc_bounding_box[2]:
        start_x = current_x
        start_y = doc_bounding_box[1] - line_width / 2
        end_x = start_x
        end_y = doc_bounding_box[3] - line_width / 2

        bx0 = start_x
        bx1 = start_x + line_width

        select_boxes = []
        for box in boxes:
            wx0 = box.position[0][0] - BOUND_PADDING
            wx1 = box.position[1][0] + BOUND_PADDING
            if bx0 < wx0 and wx1 < bx1 or \
               wx0 < bx1 and bx1 < wx1 or \
               wx0 < bx0 and bx0 < wx1:
                select_boxes.append(box)

        if select_boxes:
            y0 = start_y
            y1 = end_y
            for box in select_boxes:
                y1 = box.position[0][1] - BOX_PADDING
                draw_line(draw, [start_x, y0, end_x, y1], line_width=line_width, color=color,
                          line_weight_factor=line_weight_factor, dir='v')
                y0 = box.position[1][1] + BOX_PADDING
            draw_line(draw, [start_x, y0, end_x, end_y], line_width=line_width,  color=color,
                      line_weight_factor=line_weight_factor, dir='v')
        else:
            draw_line(draw, [start_x, start_y, end_x, end_y], line_width=line_width,  color=color,
                      line_weight_factor=line_weight_factor, dir='v')

        current_x = start_x + line_width

def get_color():
    color = (int(random.triangular(0, 10, 1)),
            int(random.triangular(0, 10, 1)),
            int(random.triangular(0, 10, 1)))
    return color

def draw_horizontal_lines(draw, boxes, doc_bounding_box, line_width):
    """Draw black horizontal lines across the page _except_ for that word"""
    line_weight_factor = random.triangular(0.005, 1.2)
    color = get_color()
    start_x = doc_bounding_box[0]
    current_y = doc_bounding_box[1]
    end_x = doc_bounding_box[2]
    end_y = doc_bounding_box[3] - line_width / 2

    while current_y < doc_bounding_box[3]:
        by0 = current_y
        by1 = current_y + line_width

        select_boxes = []
        for box in boxes:
            wy0 = box.position[0][1]
            wy1 = box.position[1][1]
            if by0 <= wy0 and wy1 <= by1 or \
               wy0 <= by1 and by1 <= wy1 or \
               wy0 <= by0 and by0 <= wy1:
                select_boxes.append(box)

        if select_boxes:
            x0 = start_x
            x1 = end_x
            for box in select_boxes:
                x1 = box.position[0][0] - BOX_PADDING
                draw_line(draw, [x0, current_y, x1, current_y],
                          line_width=line_width,
                          line_weight_factor=line_weight_factor, color=color,
                          dir="h")
                x0 = box.position[1][0] + BOX_PADDING
            draw_line(draw, [x0 + BOX_PADDING, current_y, end_x, current_y],
                      line_width=line_width, line_weight_factor=line_weight_factor, dir="h", color=color)
        else:
            draw_line(draw, [start_x, current_y, end_x, current_y],
                      line_width=line_width, color=color,
                      line_weight_factor=line_weight_factor,
                      dir="h")
        current_y = by1



def draw_line(draw, pos, line_width, dir="h", color=(0, 0, 0), line_weight_factor=1):
    # Draw a fuzzy line of randomish width repeat times
    repeat = random.randint(10, 20)
    width = int(line_width) * line_weight_factor
    default_padding = line_width / 3

    margin_extent = 20 # random.randint(1, 20)
    # Slide the center of the line down width/2 based on dir
    if dir == 'h':
        pos[1] += width / 2
        pos[3] += width / 2
        # Introduce some randomness into the margins
        # pos[0] -= random.triangular(width / margin_extent, width * margin_extent)
        # pos[2] += random.triangular(width / margin_extent, width * margin_extent)
    else:
        pos[0] -= width / 2
        pos[2] -= width / 2
        # Introduce some randomness into the margins
        # pos[1] -= random.triangular(width / margin_extent, width * margin_extent)
        # pos[3] += random.triangular(width / margin_extent, width * margin_extent)

    for i in range(0, repeat):

        width = int(random.uniform(line_width - default_padding, line_width))
        padding = default_padding * 4

        pos[0] = random.triangular(pos[0] - padding, pos[0] + padding)
        pos[1] = random.triangular(pos[1] - padding, pos[1] + padding)
        pos[2] = random.triangular(pos[2] - padding, pos[2] + padding)
        pos[3] = random.triangular(pos[3] - padding, pos[3] + padding)

        opacity = 240 + i
        width_factor = random.triangular(1, 10, 1)
        draw.line(pos, width=int(width / width_factor), fill=(*color, opacity))

def get_boxes(imagefile, tool):
    boxes = tool.image_to_string(
        Image.open(imagefile), lang="eng",
        builder=pyocr.builders.WordBoxBuilder()
    )
    return boxes

def image_filter(img):
    for i in range(5):
        img = img.filter(ImageFilter.SMOOTH_MORE)
    return img

def setup(imagefile):
    tool = pyocr.get_available_tools()[0]
    boxes = get_boxes(imagefile, tool)
    return boxes

def get_boxes_for_grammar(words, wci):
    list_of_boxes = []
    for i in range(len(words)):
        if i in wci:
            list_of_boxes.append(words[i]['box'])
    return list_of_boxes

def draw(imagefile, words, boxes, wli):

    select_boxes = get_boxes_for_grammar(words, wli)

    # Get the line height by taking the average of all the box heights
    box_heights = []
    margin_lefts = []
    margin_rights = []
    margin_top = boxes[0].position[0][1]
    margin_bottom = boxes[-1].position[1][1]

    for box in boxes:
        margin_lefts.append(box.position[0][0])
        margin_rights.append(box.position[1][0])
        box_heights.append(box.position[1][1] - box.position[0][1])

    margin_left = min(margin_lefts)
    margin_right = max(margin_rights)

    line_width = mean(box_heights)
    line_spaces = [0]
    last_y_pos = boxes[0].position[1][1]

    src = Image.open(imagefile)
    src = src.convert('RGBA')
    img = Image.new('RGBA', (src.size[0], src.size[1]))
    draw = ImageDraw.Draw(img)

    
    doc_bounding_box = (margin_left, margin_top, margin_right, margin_bottom)
    line_style = random.choice(['v', 'h', 'b'])
    if line_style == 'v':
        draw_vertical_lines(draw, select_boxes, doc_bounding_box=doc_bounding_box, line_width=line_width)
    elif line_style == 'h':
        draw_horizontal_lines(draw, select_boxes, doc_bounding_box=doc_bounding_box, line_width=line_width)
    else:
        draw_vertical_lines(draw, select_boxes, doc_bounding_box=doc_bounding_box, line_width=line_width)
        draw_horizontal_lines(draw, select_boxes, doc_bounding_box=doc_bounding_box, line_width=line_width)

    img = image_filter(img)
    out = Image.alpha_composite(src, img)

    repeat = 10

    for box in select_boxes:
        pad = BOX_PADDING
        d = ImageDraw.Draw(out)
        p0 = [box.position[0][0] - pad, box.position[0][1] - pad]
        p1 = [box.position[1][0] + pad, box.position[0][1] - pad]
        p2 = [box.position[1][0] + pad, box.position[1][1] + pad]
        p3 = [box.position[0][0] - pad, box.position[1][1] + pad]
        b = (*p0, *p2)
        crop = src.crop(box=b)
        out.paste(crop, box=b)
        w = 3 + int(random.uniform(-2, 3))
        for i in range(0, repeat):
            d.line(p0 + p1, width=w, fill="black")
            d.line(p1 + p2, width=w, fill="black")
            d.line(p2 + p3, width=w, fill="black")
            d.line(p3 + p0, width=w, fill="black")

    final = Image.new('RGBA', (src.size[0], src.size[1]))
    canvas = ImageDraw.Draw(final)
    canvas.rectangle([0, 0, final.size[0], final.size[1]], fill='white')
    final = Image.alpha_composite(final, out)
    outfile = str(uuid.uuid4())[0:5] + '.png' # os.path.basename(imagefile)

    final.save("build/" + outfile)

def parse_words(boxes):
    words = []
    for box in boxes:
        # print(box.position)
        word = box.content.strip()
        word = word.translate(str.maketrans({a:None for a in string.punctuation}))
        words.append({'text': word, 'box': box})
    sent = ' '.join([w['box'].content for w in words])
    doc = nlp(sent)
    for token in doc:
        for word in words:
            if word['text'] == '':
                words.remove(word)
            text = word['text']
            if token.text == text:
                word['token'] = token
                word['pos'] = token.pos_
                word['tag'] = tag_word(token, text.lower())
    return words

# make tags more specific
def tag_word(token, text):
    if text in ['and', 'but', 'not', 'yet', 'i', 'am']:
        return text.upper()
    elif text in ['is', 'was']:
        return 'SCP'
    elif text in ['are', 'were']:
        return 'PCP'
    elif text in ['he', 'she', 'it']:
        return 'SPS'
    elif text in ['they', 'you', 'we']:
        return 'PPS'
    else:
        return token.tag_

def all_subject_tags():
    return [
        # SINGULAR
        # the subject...
        ['DT', 'NN'],
        # the adjective subject...
        ['DT', 'JJ', 'NN'],
        ['DT', 'JJR', 'NN'],
        ['DT', 'JJS', 'NN'],
        # he, she, it...
        ['SPS'],
        # PLURAL
        # subjects...
        ['NNS'],
        # adjective subjects...
        ['JJ', 'NNS'],
        ['JJR', 'NNS'],
        ['JJS', 'NNS'],
        # subjects and subjects...
        ['NNS', 'AND', 'NNS'],
        # they, we, you... 
        ['PPS'],
        # PERSONAL
        # I...
        ['I']
    ]

def singular_verb_tags():
    return [
        # SINGULAR
        # is...
        ['SCP'],
        # can verb...
        ['MD', 'VB'],
        # verbs adverbially
        ['VBZ', 'RB'],
        # verbs...
        ['VBZ'],
        # verbed...
        ['VBD'],
        # is verbing...
        ['SCP', 'VBG']
    ]

def plural_verb_tags():
    return [
        # PLURAL
        # are...
        ['PCP'],
        # verb ...
        ['VB'],
        # can verb...
        ['MD', 'VB'],
        # verb adverbally
        ['VB', 'RB'],
        # verbed...
        ['VBD'],
        # are verbing...
        ['PCP', 'VBG']
    ]

def personal_verb_tags():
    return [
        # PERSONAL
        # am
        ['AM'],
        # can verb...
        ['MD', 'VB'],
        # verbs...
        ['VBZ'],
        # verb adverbally
        ['VB', 'RB'],
        # verbed...
        ['VBD']
    ]

def copula_object_tags():
    return [
        # adjective
        ['JJ'],
        # the adjectivest
        ['DET', 'JJS'],
        # adj and adj
        ['JJ', 'AND', 'JJ'],
        # not adj
        ['NOT', 'JJ'],
        # not the adj
        ['NOT,' 'DET', 'JJS'],
        # adj but not adj
        ['JJ', 'BUT', 'NOT', 'JJ'],
        # gerund
        ['VBG'],
        # the noun
        ['DET', 'NN']
    ]

def modal_object_tags():
    return [
        ['DET', 'NN']
    ]

def verb_object_tags():
    return [
        # the object
        ['DET', 'NN'],
        # the adjective object
        ['DET', 'JJ', 'NN'],
        # the objects
        ['DET', 'NNS'],
        # the adjective objects
        ['DET', 'JJ', 'NNS'],
        # objects and objects
        ['NNS', 'AND', 'NNS'],
        ['NNS'],
        ['NN']
    ]

def get_all_grammar_dicts(words, grammars):
    grammar_dict = {}
    grammar_count = 0

    for g in grammars:
        grammar_dict[grammar_count] = get_grammar_dict(words, g)
        grammar_count += 1

    return grammar_dict

def get_grammar_dict(words, g):
    picks = []
    num_words = len(words)
    starter_list = []
    combin_dict = {}
    index = 0

    for i in range(len(g)):
        pos = g[i]
        combin_dict[i] = get_next_words(index, pos, words, num_words)
        if combin_dict[i] == []:
            index = num_words
        else:
            index = combin_dict[i][0][1]
    
    return combin_dict

def get_next_words(index, pos, words, num_words):
    next_words = []
    for i in range(index, num_words):
        if 'tag' in words[i]:
            if words[i]['tag'] == pos:
                next_words.append((words[i]['text'], i))
    return next_words

def get_all_options(words, grammars, svo, index):
    grammar_dicts = get_all_grammar_dicts(words, grammars)
    gd_count = 0
    all_word_lists = {}
    for gd in grammar_dicts.values():
        print("-------------")
        print(svo, gd_count)
        list_of_wl = []
        for j in gd:
            text_list = []
            word_list = []
            for wl in gd[j]:
                if wl[1] > index:
                    text = wl[0].lower()
                    if text not in text_list:
                        text_list.append(text)
                        word_list.append(wl)
            if text_list == []:
                print("No viable options :(")
                break
            print(text_list)
            list_of_wl.append(word_list)
        all_word_lists[gd_count] = list_of_wl
        gd_count += 1
    return all_word_lists

def blackout(imagefile, words, wci):
    color = (0, 0, 0)
    src = Image.open(imagefile)
    src = src.convert('RGBA')
    img = Image.new('RGBA', (src.size[0], src.size[1]))
    draw = ImageDraw.Draw(img)

    for i in range(len(words)):
        if i in wci:
            draw.rectangle(words[i]['box'].position, outline=color)
        else:
            draw.rectangle(words[i]['box'].position, fill=color)

    out = Image.alpha_composite(src, img)
    outfile = str(uuid.uuid4())[0:5] + '.png' # os.path.basename(imagefile)

    out.save("build/" + outfile)

def get_user_input(imagefile, boxes):
    words = parse_words(boxes)
    wct = []
    wci = []
    subj_grammars = all_subject_tags()
    wct, wci = get_user_choice(words, wct, wci, subj_grammars, "SUBJECT", 0)
    last_subj = words[wci[-1]]
    last_ind = wci[-1]
    #### KEEP GOING ?? ####
    if last_subj['tag'] in ['NNS', 'PPS']:
        plur_v_grammars = plural_verb_tags()
        wct, wci = get_user_choice(words, wct, wci, plur_v_grammars, "VERB", last_ind)
    elif last_subj['tag'] == 'I':
        pers_v_grammars = personal_verb_tags()
        wct, wci = get_user_choice(words, wct, wci, pers_v_grammars, "VERB", last_ind)
    else:
        sing_v_grammars = singular_verb_tags()
        wct, wci = get_user_choice(words, wct, wci, sing_v_grammars, "VERB", last_ind)
    last_ind = wci[-1]
    last_v = words[wci[-1]]
    two_last_v = words[wci[-2]]
    #### KEEP GOING ?? ####
    if last_v in ['SCP', 'PCP']:
        copula_grammars = copula_object_tags()
        wct, wci = get_user_choice(words, wct, wci, copula_grammars, "OBJECT", last_ind)
    elif two_last_v == 'MD':
        modal_grammars = modal_object_tags()
        wct, wci = get_user_choice(words, wct, wci, modal_grammars, "OBJECT", last_ind)
    else:
        object_grammars = verb_object_tags()
        wct, wci = get_user_choice(words, wct, wci, object_grammars, "OBJECT", last_ind)
    draw(imagefile, words, boxes, wci)
    

def get_user_choice(words, wct, wci, g, svo, index):
    word_choices_text = wct
    word_choices_indices = wci

    subj_grammars = all_subject_tags()
    all_word_lists = get_all_options(words, g, svo, index)
    print("********************************")
    print("Choose a", svo, "grammar (0-", len(g), ")")
    g_choice = int(input())
    
    print("Your choice:")
    for l in all_word_lists[g_choice]:
        print(l)
    
    for l in all_word_lists[g_choice]:
        print("-------------")
        print("Choose 1 of the following:")
        for i in range(len(l)):
            print (i, ":", l[i][0])
        print("-------------")
        choice = int(input())
        word_choices_indices.append(l[choice][1])
        word_choices_text.append(l[choice][0])
    
    print("********************************")
    print("Your current poem:", word_choices_text)

    return word_choices_text, word_choices_indices


if __name__ == '__main__':
    path = sys.argv[1]
    pages = []
    for f in os.listdir(path):
        pages.append(f)
    num_generations_per_page = 1
    for f in pages:
        imagefile = os.path.join(path, f)
        print("Procesing " + imagefile)
        boxes = setup(imagefile)
        # words = parse_words(boxes)
        # g = all_subject_tags()
        # get_all_options(words, g, "SUBJECT", 0)
        get_user_input(imagefile, boxes)